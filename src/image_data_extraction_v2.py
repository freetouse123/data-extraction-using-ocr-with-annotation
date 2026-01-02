"""
PDF to Image Data Extraction Module
Handles PDF conversion and OCR text extraction using Azure Vision API
"""

import os
import base64
import time
import fitz
import requests
import threading

from typing import List, Tuple, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from azure.ai.vision.imageanalysis import ImageAnalysisClient
from azure.ai.vision.imageanalysis.models import VisualFeatures
from azure.core.credentials import AzureKeyCredential

from utils.logger import get_logger
from utils.helper import normalize_ocr
from config.config import Config
from dotenv import load_dotenv

load_dotenv()

logger = get_logger(__name__)


class Pdf2ImageDataExtractor:
    """
    Extract text data from PDF documents using Azure Vision OCR
    """
    
    def __init__(self):
        logger.info("Initializing Pdf2ImageDataExtractor")
        self.endpoint = os.getenv("VISION_ENDPOINT")
        self.key = os.getenv("VISION_KEY")
        
        if not self.endpoint or not self.key:
            raise ValueError("Missing VISION_ENDPOINT or VISION_KEY environment variables")
        
        self.client = ImageAnalysisClient(
            endpoint=self.endpoint,
            credential=AzureKeyCredential(self.key)
        )
        self.ocr_dpi = 300  # Store DPI for coordinate scaling
    
    def pdf_to_images_for_ocr(
        self, 
        pdf_bytes: bytes, 
        dpi: int = 300
    ) -> Tuple[List[Tuple[int, bytes, int, int]], fitz.Document]:
        """
        Convert PDF to high-resolution images for OCR processing
        
        Returns:
            Tuple of (images_data, original_doc)
        """
        logger.info("Converting PDF to images for OCR")
        self.ocr_dpi = dpi
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        images_data = []
        
        zoom = dpi / 72
        matrix = fitz.Matrix(zoom, zoom)
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            pix = page.get_pixmap(matrix=matrix)
            img_bytes = pix.tobytes("png")
            images_data.append((page_num, img_bytes, pix.width, pix.height))
        
        logger.info(f"Converted {len(images_data)} pages to images for OCR")
        return images_data, doc
    
    def pdf_to_images_for_display(
        self, 
        pdf_bytes: bytes, 
        dpi: int = 150
    ) -> List[Tuple[int, str, int, int]]:
        """
        Convert PDF to display-resolution images with base64 encoding
        """
        logger.info("Converting PDF to images for display")
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        images_data = []
        
        zoom = dpi / 72
        matrix = fitz.Matrix(zoom, zoom)
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            pix = page.get_pixmap(matrix=matrix)
            img_bytes = pix.tobytes("png")
            img_base64 = base64.b64encode(img_bytes).decode('utf-8')
            images_data.append((page_num, img_base64, pix.width, pix.height))
        
        doc.close()
        logger.info(f"Converted {len(images_data)} pages to images for display")
        return images_data
    
    def extract_text_from_image(self, image_bytes: bytes):
        """
        Extract text from image using Azure Vision API
        """
        logger.info("Extracting text from image using Azure Vision API")
        result = self.client.analyze(
            image_data=image_bytes,
            visual_features=[VisualFeatures.CAPTION, VisualFeatures.READ],
            gender_neutral_caption=True,
            model_version="latest"
        )
        logger.info("Text extraction complete")
        return result
    
    def process_single_page(self, page_data: Tuple[int, bytes, int, int]) -> Dict:
        """
        Process a single page: OCR and normalize results
        """
        logger.info(f"Processing page {page_data[0]} for OCR")
        page_num, img_bytes, width, height = page_data
        
        ocr_result = self.extract_text_from_image(img_bytes)
        annotations = normalize_ocr(ocr_result, width, height)
        
        logger.info(f"Completed processing page {page_num}")
        return {
            'page_num': page_num,
            'annotations': annotations,
            'width': width,
            'height': height,
            'dpi': self.ocr_dpi
        }


class BatchProcessor:
    """Process multiple PDF pages in parallel batches"""
    
    def __init__(
        self, 
        batch_size: int = None, 
        max_workers: int = None
    ):
        self.ocr_client = Pdf2ImageDataExtractor()
        self.batch_size = batch_size or getattr(Config, 'BATCH_SIZE', 5)
        self.max_workers = max_workers or getattr(Config, 'MAX_WORKERS', 3)
    
    def process_batch(self, pages_data: List[Tuple]) -> List[Dict]:
        """Process a batch of pages"""
        results = []
        for page_data in pages_data:
            result = self.ocr_client.process_single_page(page_data)
            results.append(result)
        return results
    
    def process_all(
        self, 
        images_data: List[Tuple], 
        progress_callback: callable = None
    ) -> List[Dict]:
        """Process all images in parallel batches"""
        
        # Split into batches
        batches = [
            images_data[i:i + self.batch_size]
            for i in range(0, len(images_data), self.batch_size)
        ]
        
        all_results = []
        completed = 0
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_batch = {
                executor.submit(self.process_batch, batch): idx
                for idx, batch in enumerate(batches)
            }
            
            for future in as_completed(future_to_batch):
                batch_idx = future_to_batch[future]
                try:
                    batch_results = future.result()
                    all_results.extend(batch_results)
                    completed += 1
                    
                    if progress_callback:
                        progress = completed / len(batches)
                        progress_callback(progress, f"Processed batch {completed}/{len(batches)}")
                
                except Exception as e:
                    logger.error(f"Batch {batch_idx} failed: {e}")
                    raise
        
        # Sort by page number
        all_results.sort(key=lambda x: x['page_num'])
        
        return all_results
    
    def process_pdf(
        self, 
        pdf_bytes: bytes, 
        dpi: int = 300,
        progress_callback: callable = None
    ) -> Tuple[List[Dict], int]:
        """
        Complete PDF processing pipeline
        
        Returns:
            Tuple of (ocr_results, dpi)
        """
        images_data, doc = self.ocr_client.pdf_to_images_for_ocr(pdf_bytes, dpi)
        doc.close()
        
        ocr_results = self.process_all(images_data, progress_callback)
        
        return ocr_results, dpi