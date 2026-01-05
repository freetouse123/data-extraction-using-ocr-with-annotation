from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence.aio import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import DocumentAnalysisFeature
from azure.ai.documentintelligence.models import DocumentContentFormat
from openai import AsyncAzureOpenAI

from models.schema import DataExtractionSchema
from models.swedish_poc_model import LCAnalyticalDocumentSwedish
from models.english_enity_model import LCAnalyticalDocumentEnglish

from config.config import RETRY_CONFIG
from utils.logger import get_logger
from dotenv import load_dotenv
from config.config import Config
import aiofiles
import base64
import os
load_dotenv()

logger = get_logger(__name__)


class DocumentDataExtractor:
    def __init__(self):
        logger.info("Initializing DocumentDataExtractor")
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
                "prebuilt-layout", 
                analyze_request,
                features=[DocumentAnalysisFeature.LANGUAGES],
                output_content_format=DocumentContentFormat.MARKDOWN,
                
            )
            result = await poller.result()
            logger.info(f"document extracted sucessfully")

            return result
        except Exception as e:
            logger.error(f"Error in extract_data: {e}")
            raise
    
    @RETRY_CONFIG
    async def response_generation(self, content:str)-> str:
        try:
            logger.info("Generating the response of the extracted content")
            response = await self.openai_client.beta.chat.completions.parse(
                model = os.getenv("AZURE_OPENAI_DEPLOYMENT"),
                messages = [
                    {"role":"system", "content":Config.system_prompt_for_entity_extraction},
                    {"role":"user","content": content},
                    ],
                response_format= LCAnalyticalDocumentSwedish,
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
    
    async def close(self):
        await self.document_intelligence_client.close()
        await self.openai_client.close()