from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence.aio import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import DocumentAnalysisFeature
from azure.ai.documentintelligence.models import DocumentContentFormat
from openai import AsyncAzureOpenAI

from models.english_enity_model import EnityExtractionResponse
from utils.logger import get_logger
from dotenv import load_dotenv
from config.config import Config
from typing import List
import json
import uuid
import aiofiles
import base64
import os
load_dotenv()

logger = get_logger(__name__)


class BatchDocumentExtraction:
    
    def __init__(self):
        logger.info("Initializing BatchDocumentExtraction")
        self.document_intelligence_client  = DocumentIntelligenceClient(
            endpoint=os.getenv("DOCUMENT_INTELLIGENCE_ENDPOINT"), 
            credential=AzureKeyCredential(os.getenv("DOCUMENT_INTELLIGENCE_KEY"))
            )
        self.openai_client = AsyncAzureOpenAI(
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_KEY"),
            api_version=os.getenv("API_VERSION")
            )
    
    async def extract_data(self, pdf:bytes):
        try:
            logger.info("Starting data extraction from document")
            base64_encoded_pdf = base64.b64encode(pdf).decode("utf-8")

            analyze_request = {
                "base64Source": base64_encoded_pdf
            }   
            poller = await self.document_intelligence_client.begin_analyze_document(
                model_id="prebuilt-layout", 
                body=analyze_request,
                features=[DocumentAnalysisFeature.LANGUAGES],
                output_content_format=DocumentContentFormat.MARKDOWN,
                
            )
            result = await poller.result()
            logger.info(f"document extracted sucessfully")

            return  result
        except Exception as e:
            logger.error(e)
            raise
    
    async def response_generation(self, content:str)-> str:
        try:
            logger.info("Generating the response of the extracted content")
            response = await self.openai_client.beta.chat.completions.parse(
                model = os.getenv("AZURE_OPENAI_DEPLOYMENT"),
                messages = [
                    {"role":"system", "content":Config.system_prompt_for_entity_extraction},
                    {"role":"user","content": content},
                    ],
                response_format= EnityExtractionResponse,
            )

            ## total token used to generate the response:
            logger.info(f"Total token use to generate the response: {response.usage.total_tokens}")
            logger.info(f"Total chat completeion token: {response.usage.completion_tokens}")
            logger.info(f"Total input tokens: {response.usage.prompt_tokens}")

            raw_response = response.choices[0].message.parsed
            raw_response_json = raw_response.model_dump()
            
            logger.info(f"response generated successfully")
            return raw_response_json
        except Exception as e:
            logger.error(e)
            raise
    
    ## Handling the batch extraction after extractiing the data
    async def batch_data_extraction(self, pdf: bytes):
        try:
            logger.info("Handling Batch Data Extraction For Multiple Pages")

            # Extract document data using Azure Document Intelligence
            doc_result = await self.extract_data(pdf)

            if not doc_result or not doc_result.content:
                raise ValueError("No content extracted from document")

            # Split content by page
            pages = [
                page.strip()
                for page in doc_result.content.split("<!-- PageBreak -->")
                if page.strip()
            ]

            logger.info(f"Total pages extracted: {len(pages)}")

            batch_size = int(Config.batch_size)
            
            final_response = []

            # Batch pages (3 pages per batch)
            for i in range(0, len(pages), batch_size):
                batch_pages = pages[i:i + batch_size]

                combined_content = "\n\n".join(batch_pages)

                logger.info(
                    f"Processing batch {i // batch_size + 1} "
                    f"with pages {i + 1} to {i + len(batch_pages)}"
                )

                # Step 4: Entity extraction / LLM processing
                response = await self.response_generation(
                    content=combined_content
                )

                # Store structured response
                final_response.append({
                    "batch_number": (i // batch_size) + 1,
                    "page_range": f"{i + 1}-{i + len(batch_pages)}",
                    "response": response
                })

            return final_response

        except Exception as e:
            logger.exception("Error in batch_data_extraction")
            raise

    
    async def close(self):
        await self.document_intelligence_client.close()
        await self.openai_client.close()
