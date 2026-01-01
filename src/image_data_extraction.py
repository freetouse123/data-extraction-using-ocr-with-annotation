"""
PDF to Image Data Extraction Module
Handles PDF conversion and OCR text extraction using Azure Vision API
"""

import os
import base64
import fitz  # PyMuPDF
from io import BytesIO
from typing import List, Tuple, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed

from azure.ai.vision.imageanalysis import ImageAnalysisClient
from azure.ai.vision.imageanalysis.models import VisualFeatures
from azure.core.credentials import AzureKeyCredential
from dotenv import load_dotenv

from utils.helper import normalize_ocr

load_dotenv()


class Pdf2ImageDataExtractor:
    """
    Extract text data from PDF documents using Azure Vision OCR
    """
    
    def __init__(self):
        self.endpoint = os.getenv("VISION_ENDPOINT")
        self.key = os.getenv("VISION_KEY")
        
        if not self.endpoint or not self.key:
            raise ValueError("Missing VISION_ENDPOINT or VISION_KEY environment variables")
        
        self.client = ImageAnalysisClient(
            endpoint=self.endpoint,
            credential=AzureKeyCredential(self.key)
        )
    
    def pdf_to_images_for_ocr(self, pdf_bytes: bytes, dpi: int = 300) -> List[Tuple[int, bytes, int, int]]:
        """
        Convert PDF to high-resolution images for OCR processing
        
        Args:
            pdf_bytes: PDF file as bytes
            dpi: Resolution for image conversion (default 300)
        
        Returns:
            List of tuples (page_num, image_bytes, width, height)
        """
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        images_data = []
        
        zoom = dpi / 72
        matrix = fitz.Matrix(zoom, zoom)
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            pix = page.get_pixmap(matrix=matrix)
            img_bytes = pix.tobytes("png")
            images_data.append((page_num, img_bytes, pix.width, pix.height))
        
        doc.close()
        return images_data
    
    def pdf_to_images_for_display(self, pdf_bytes: bytes, dpi: int = 150) -> List[Tuple[int, str, int, int]]:
        """
        Convert PDF to display-resolution images with base64 encoding
        
        Args:
            pdf_bytes: PDF file as bytes
            dpi: Resolution for display (default 150)
        
        Returns:
            List of tuples (page_num, base64_string, width, height)
        """
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
        return images_data
    
    def extract_text_from_image(self, image_bytes: bytes):
        """
        Extract text from image using Azure Vision API
        
        Args:
            image_bytes: Image as bytes
        
        Returns:
            Azure Vision analysis result
        """
        result = self.client.analyze(
            image_data=image_bytes,
            visual_features=[VisualFeatures.CAPTION, VisualFeatures.READ],
            gender_neutral_caption=True,
            model_version="latest"
        )
        return result
    
    def process_single_page(self, page_data: Tuple[int, bytes, int, int]) -> Dict:
        """
        Process a single page: OCR and normalize results
        
        Args:
            page_data: Tuple of (page_num, image_bytes, width, height)
        
        Returns:
            Dictionary with page_num and annotations
        """
        page_num, img_bytes, width, height = page_data
        
        ocr_result = self.extract_text_from_image(img_bytes)
        annotations = normalize_ocr(ocr_result, width, height)
        
        return {
            'page_num': page_num,
            'annotations': annotations,
            'width': width,
            'height': height
        }


class BatchProcessor:
    """
    Process multiple PDF pages in parallel batches
    """
    
    def __init__(self, extractor: Pdf2ImageDataExtractor, batch_size: int = 5, max_workers: int = 3):
        self.extractor = extractor
        self.batch_size = batch_size
        self.max_workers = max_workers
    
    def process_batch(self, images_data: List[Tuple], batch_id: int) -> Dict:
        """
        Process a batch of images
        
        Args:
            images_data: List of image data tuples
            batch_id: Identifier for this batch
        
        Returns:
            Dictionary with batch_id and results
        """
        batch_results = []
        
        for page_data in images_data:
            result = self.extractor.process_single_page(page_data)
            batch_results.append(result)
        
        return {
            'batch_id': batch_id,
            'results': batch_results
        }
    
    def process_all_batches(self, images_data: List[Tuple], progress_callback=None) -> List[Dict]:
        """
        Process all images in parallel batches
        
        Args:
            images_data: List of all image data tuples
            progress_callback: Optional callback function for progress updates
        
        Returns:
            Flattened list of all results sorted by page number
        """
        # Split into batches
        batches = [
            images_data[i:i + self.batch_size]
            for i in range(0, len(images_data), self.batch_size)
        ]
        
        all_results = []
        completed = 0
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(self.process_batch, batch, idx): idx
                for idx, batch in enumerate(batches)
            }
            
            for future in as_completed(futures):
                batch_result = future.result()
                all_results.append(batch_result)
                completed += 1
                
                if progress_callback:
                    progress_callback(completed / len(batches))
        
        # Sort by batch_id and flatten
        all_results.sort(key=lambda x: x['batch_id'])
        
        flattened = []
        for batch in all_results:
            flattened.extend(batch['results'])
        
        return flattened