from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence.aio import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import DocumentAnalysisFeature
from azure.ai.documentintelligence.models import DocumentContentFormat
from openai import AsyncAzureOpenAI

from models.swedish_poc_model import LCAnalyticalDocumentSwedish
from models.english_enity_model import LCAnalyticalDocumentEnglish
from utils.utils import  merge_batch_responses, deduplicate_list_of_dicts
from utils.logger import get_logger
from dotenv import load_dotenv
from config.config import Config
from config.config import RETRY_CONFIG
from typing import List, Dict, Any
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
    
    @RETRY_CONFIG
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

    @RETRY_CONFIG
    async def response_generation(self, content:str, batch_context: Dict[str, Any], language:str = "english")-> str:
        
        if language.lower() == "english":
            validator_model = LCAnalyticalDocumentEnglish
        else:
            validator_model = LCAnalyticalDocumentSwedish

        try:
            system_prompt = f"""
Language: {language}
{Config.system_prompt_for_entity_extraction}

BATCH CONTEXT:
- Batch number: {batch_context.get('batch_number')}
- Page range: {batch_context.get('page_range')}
- Total batches: {batch_context.get('total_batches')}

INSTRUCTIONS:
- Extract ALL information present in this batch
- If a section is incomplete (starts or ends mid-section), extract what's available
- Mark sections as 'partial' if they appear incomplete
- Do not infer missing information
- Always provide response in Following language: {language}
"""
            
            logger.info("Generating the response of the extracted content")
            response = await self.openai_client.beta.chat.completions.parse(
                model = os.getenv("AZURE_OPENAI_DEPLOYMENT"),
                messages = [
                    {"role":"system", "content":system_prompt},
                    {"role":"user","content": content},
                    ],
                response_format= validator_model,
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
    async def batch_data_extraction(self, pdf: bytes, language:str="English") -> Dict[str, Any]:
        """
        Main method: Extract data in batches and return consolidated JSON
        
        Returns:
            Dict: Single consolidated LCAnalyticalDocument JSON
        """
        try:
            logger.info("Starting batch data extraction")

            # Step 1: Extract document content using Azure Document Intelligence
            doc_result = await self.extract_data(pdf)

            if not doc_result or not doc_result.content:
                raise ValueError("No content extracted from document")

            # Step 2: Split content by page
            pages = [
                page.strip()
                for page in doc_result.content.split("<!-- PageBreak -->")
                if page.strip()
            ]

            logger.info(f"Total pages extracted: {len(pages)}")

            batch_size = int(Config.batch_size)
            total_batches = (len(pages) + batch_size - 1) // batch_size
            
            batch_responses = []

            # Step 3: Process each batch
            for i in range(0, len(pages), batch_size):
                batch_pages = pages[i:i + batch_size]
                combined_content = "\n\n".join(batch_pages)
                
                batch_number = (i // batch_size) + 1
                page_range = f"{i + 1}-{i + len(batch_pages)}"
                
                logger.info(f"Processing batch {batch_number}/{total_batches} (pages {page_range})")

                # Create batch context
                batch_context = {
                    "batch_number": batch_number,
                    "page_range": page_range,
                    "total_batches": total_batches,
                    "total_pages": len(pages)
                }

                # Step 4: Generate structured response for this batch
                response = await self.response_generation(
                    content=combined_content,
                    batch_context=batch_context,
                    language= language
                )

                # Store batch response with metadata
                batch_responses.append({
                    "batch_number": batch_number,
                    "page_range": page_range,
                    "response": response,
                    "pages_in_batch": len(batch_pages)
                })

            # Step 5: Merge all batch responses into final consolidated JSON
            logger.info("Merging all batch responses into final document")
            final_document = merge_batch_responses(batch_responses)
            
            # Add processing metadata
            final_document["_metadata"] = {
                "total_pages_processed": len(pages),
                "total_batches": total_batches,
                "batch_size": batch_size,
                "processing_complete": True
            }
            
            logger.info("Batch data extraction completed successfully")
            return final_document

        except Exception as e:
            logger.exception("Error in batch_data_extraction")
            raise

    
    async def close(self):
        await self.document_intelligence_client.close()
        await self.openai_client.close()
