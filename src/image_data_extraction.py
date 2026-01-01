"""
This module handles the extraction of the data from the pdf where it convert the PDF into images and then
extracts text from the images using custom vision models.
"""

from azure.ai.vision.imageanalysis import ImageAnalysisClient  
from azure.ai.vision.imageanalysis.models import VisualFeatures   
from azure.core.credentials import AzureKeyCredential  

from msrest.authentication import ApiKeyCredentials
import os, time, uuid

import fitz
from io import BytesIO
from utils.logger import get_logger
from dotenv import load_dotenv
load_dotenv()

logger = get_logger(__name__)

class Pdf2ImageDataExtractor:
    def __init__(self):
        pass

    async def pdf_to_images(self, pdf_bytes: bytes):
        """
        Convert PDF bytes to images using PyMuPDF.
        """
        logger.info("Converting PDF to images")
        print("Converting PDF to images")
        
        # Open PDF from bytes
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        
        image_bytes_list = []
        for page_num, page in enumerate(doc):
            # Convert page to image with 300 DPI
            # zoom = 300 / 72 (default DPI)
            zoom = 300 / 72
            matrix = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=matrix)
            
            # Convert to PNG bytes
            img_bytes = pix.tobytes("png")
            image_bytes_list.append(img_bytes)
            
        doc.close()
        logger.info(f"Converted PDF to {len(image_bytes_list)} images")
        print(f"Converted PDF to {len(image_bytes_list)} images")
        return image_bytes_list
    
    async def extract_text_from_image(self, image_bytes: bytes):
        """
        Extract text from image bytes using Custom Vision model.
        This is a placeholder function. Actual implementation will depend on the Custom Vision setup.
        """ 
        logger.info("Extracting text from image using Custom Vision model") 
        try:  
            endpoint = os.getenv("VISION_ENDPOINT")  
            key = os.getenv("VISION_KEY")  
            # print(endpoint,"\n KEY: ",key)
        except KeyError:  
            logger.error("Missing environment variable 'VISION_ENDPOINT' or 'VISION_KEY'. Set them before running this sample.")  
            return None  
    
        print("Extracting text from image using Custom Vision model")
        print(endpoint)
        print(key)
        client = ImageAnalysisClient(  
            endpoint=endpoint,  
            credential=AzureKeyCredential(key)  
        )  
        result = client.analyze(  
            image_data=image_bytes,  
            visual_features=[VisualFeatures.CAPTION, VisualFeatures.READ],  
            gender_neutral_caption=True,
            model_version="latest"
        )

        logger.info("Text extraction completed")
        return result
    

    async def main(self, pdf_bytes: bytes):
        images = await self.pdf_to_images(pdf_bytes)
        all_extracted_texts = []
        for idx, image in enumerate(images):
            logger.info(f"Processing page {idx + 1}/{len(images)}")
            extracted_text = await self.extract_text_from_image(image)
            all_extracted_texts.append(extracted_text)
        return all_extracted_texts
    