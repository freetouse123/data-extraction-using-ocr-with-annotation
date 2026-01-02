"""
PDF to Image Data Extraction Module
Handles PDF conversion and OCR text extraction using Azure Vision API
"""

import os
import base64
import time
import fitz  # PyMuPDF
from typing import List, Tuple, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
import threading

from azure.ai.vision.imageanalysis import ImageAnalysisClient
from azure.ai.vision.imageanalysis.models import VisualFeatures
from azure.core.credentials import AzureKeyCredential
from dotenv import load_dotenv

from utils.helper import normalize_ocr
from utils.logger import get_logger
load_dotenv()
logger = get_logger(__name__)


class ProgressTracker:
    """Thread-safe progress tracker"""
    
    def __init__(self):
        self._lock = threading.Lock()
        self._ocr_progress = 0.0
        self._api_progress = 0.0
        self._ocr_status = "Initializing..."
        self._api_status = "Waiting..."
        self._ocr_complete = False
        self._api_complete = False
    
    def update_ocr(self, progress: float, status: str = None):
        with self._lock:
            self._ocr_progress = min(progress, 1.0)
            if status:
                self._ocr_status = status
            if progress >= 1.0:
                self._ocr_complete = True
    
    def update_api(self, progress: float, status: str = None):
        with self._lock:
            self._api_progress = min(progress, 1.0)
            if status:
                self._api_status = status
            if progress >= 1.0:
                self._api_complete = True
    
    def get_progress(self) -> Dict:
        with self._lock:
            return {
                "ocr_progress": self._ocr_progress,
                "api_progress": self._api_progress,
                "ocr_status": self._ocr_status,
                "api_status": self._api_status,
                "ocr_complete": self._ocr_complete,
                "api_complete": self._api_complete
            }
    
    def is_complete(self) -> bool:
        with self._lock:
            return self._ocr_complete and self._api_complete


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
    
    def pdf_to_images_for_ocr(self, pdf_bytes: bytes, dpi: int = 300) -> List[Tuple[int, bytes, int, int]]:
        """
        Convert PDF to high-resolution images for OCR processing
        """
        logger.info("Converting PDF to images for OCR")
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
        logger.info(f"Converted {len(images_data)} pages to images for OCR")
        return images_data
    
    def pdf_to_images_for_display(self, pdf_bytes: bytes, dpi: int = 150) -> List[Tuple[int, str, int, int]]:
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
        """
        logger.info(f"Processing batch {batch_id} with {len(images_data)} pages")
        batch_results = []
        
        for page_data in images_data:
            result = self.extractor.process_single_page(page_data)
            batch_results.append(result)

        logger.info(f"Completed processing batch {batch_id}")
        return {
            'batch_id': batch_id,
            'results': batch_results
        }
    
    def process_all_batches(
        self, 
        images_data: List[Tuple], 
        progress_tracker: Optional[ProgressTracker] = None
    ) -> List[Dict]:
        """
        Process all images in parallel batches
        """
        logger.info("Starting processing all batches")

        batches = [
            images_data[i:i + self.batch_size]
            for i in range(0, len(images_data), self.batch_size)
        ]
        
        all_results = []
        completed = 0
        
        logger.info(f"Total batches to process: {len(batches)}")
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(self.process_batch, batch, idx): idx
                for idx, batch in enumerate(batches)
            }
            
            for future in as_completed(futures):
                batch_result = future.result()
                all_results.append(batch_result)
                completed += 1
                
                if progress_tracker:
                    progress = 0.2 + (completed / len(batches)) * 0.6  # 20% to 80%
                    progress_tracker.update_ocr(
                        progress, 
                        f"Processing batch {completed}/{len(batches)}..."
                    )
        
        all_results.sort(key=lambda x: x['batch_id'])
        
        logger.info("Completed processing all batches")
        flattened = []
        for batch in all_results:
            flattened.extend(batch['results'])
        
        return flattened


class APIDataExtractor:
    """
    Extract structured data from PDF using external API
    """
    
    def __init__(self, api_url: str = "http://localhost:8000/api/v1/batch-extract-data"):
        self.api_url = api_url
    
    def extract_data(
        self, 
        pdf_bytes: bytes, 
        filename: str = "document.pdf",
        progress_tracker: Optional[ProgressTracker] = None
    ) -> Dict:
        """
        Send PDF to API and get extracted structured data
        """
        logger.info("Starting API data extraction")
        try:
            if progress_tracker:
                progress_tracker.update_api(0.1, "Sending PDF to API...")
            
            files = {
                "pdf": (filename, pdf_bytes, "application/pdf")
            }
            
            response = requests.post(
                self.api_url,
                files=files,
                headers={"accept": "application/json"},
                timeout=300
            )
            
            if progress_tracker:
                progress_tracker.update_api(0.8, "Processing response...")
            
            if response.status_code == 200:
                result = response.json()
                if result.get("status") == "success":
                    if progress_tracker:
                        progress_tracker.update_api(1.0, "Complete!")
                    return {
                        "success": True,
                        "data": result.get("data", []),
                        "error": None
                    }
                else:
                    if progress_tracker:
                        progress_tracker.update_api(1.0, "Failed")
                    return {
                        "success": False,
                        "data": [],
                        "error": result.get("message", "Extraction failed")
                    }
            else:
                if progress_tracker:
                    progress_tracker.update_api(1.0, "API Error")
                return {
                    "success": False,
                    "data": [],
                    "error": f"API Error: {response.status_code}"
                }
        
        except requests.exceptions.ConnectionError:
            if progress_tracker:
                progress_tracker.update_api(1.0, "Connection failed")
            return {
                "success": False,
                "data": [],
                "error": "Could not connect to API server"
            }
        except requests.exceptions.Timeout:
            if progress_tracker:
                progress_tracker.update_api(1.0, "Timeout")
            return {
                "success": False,
                "data": [],
                "error": "Request timed out"
            }
        except Exception as e:
            if progress_tracker:
                progress_tracker.update_api(1.0, "Error")
            return {
                "success": False,
                "data": [],
                "error": str(e)
            }


class ParallelProcessor:
    """
    Run OCR annotation and API extraction in parallel
    """
    
    def __init__(
        self,
        extractor: Pdf2ImageDataExtractor,
        api_extractor: APIDataExtractor,
        batch_size: int = 5
    ):
        self.extractor = extractor
        self.api_extractor = api_extractor
        self.batch_processor = BatchProcessor(extractor, batch_size=batch_size)
    
    def process_pdf_parallel(
        self, 
        pdf_bytes: bytes, 
        filename: str = "document.pdf",
        progress_tracker: Optional[ProgressTracker] = None
    ) -> Dict:
        """
        Process PDF with both OCR and API extraction in parallel
        
        Returns:
            Dictionary with OCR results, API results, display images, and timing info
        """
        
        logger.info("Starting parallel PDF processing")

        results = {
            "ocr_results": [],
            "api_results": {"success": False, "data": [], "error": None},
            "display_images": [],
            "timing": {}
        }
        
        start_time = time.time()
        
        def run_ocr_pipeline():
            """OCR processing pipeline"""
            logger.info("Starting OCR pipeline")
            ocr_start = time.time()
            
            try:
                # Convert to images for OCR
                if progress_tracker:
                    progress_tracker.update_ocr(0.1, "Converting PDF to images...")
                
                images_for_ocr = self.extractor.pdf_to_images_for_ocr(pdf_bytes)
                
                if progress_tracker:
                    progress_tracker.update_ocr(0.2, "Starting OCR processing...")
                
                # Run OCR batch processing
                ocr_results = self.batch_processor.process_all_batches(
                    images_for_ocr, 
                    progress_tracker=progress_tracker
                )
                
                if progress_tracker:
                    progress_tracker.update_ocr(0.85, "Preparing display images...")
                
                # Convert to display images
                display_images = self.extractor.pdf_to_images_for_display(pdf_bytes)
                
                if progress_tracker:
                    progress_tracker.update_ocr(1.0, "Complete!")
                
                ocr_end = time.time()
                
                return {
                    "ocr_results": ocr_results,
                    "display_images": display_images,
                    "ocr_time": ocr_end - ocr_start,
                    "error": None
                }
            except Exception as e:
                if progress_tracker:
                    progress_tracker.update_ocr(1.0, f"Error: {str(e)}")
                return {
                    "ocr_results": [],
                    "display_images": [],
                    "ocr_time": 0,
                    "error": str(e)
                }
        
        def run_api_extraction():
            """API extraction pipeline"""
            api_start = time.time()
            
            api_result = self.api_extractor.extract_data(
                pdf_bytes, 
                filename,
                progress_tracker=progress_tracker
            )
            
            api_end = time.time()
            api_result["api_time"] = api_end - api_start
            
            return api_result
        
        # Run both pipelines in parallel using threads (not ThreadPoolExecutor for the outer level)
        ocr_result_holder = [None]
        api_result_holder = [None]
        
        def ocr_thread_func():
            ocr_result_holder[0] = run_ocr_pipeline()
        
        def api_thread_func():
            api_result_holder[0] = run_api_extraction()
        
        ocr_thread = threading.Thread(target=ocr_thread_func)
        api_thread = threading.Thread(target=api_thread_func)
        
        ocr_thread.start()
        api_thread.start()
        
        ocr_thread.join()
        api_thread.join()
        
        # Get results
        ocr_data = ocr_result_holder[0]
        api_data = api_result_holder[0]
        
        if ocr_data:
            results["ocr_results"] = ocr_data.get("ocr_results", [])
            results["display_images"] = ocr_data.get("display_images", [])
            results["timing"]["ocr"] = ocr_data.get("ocr_time", 0)
            if ocr_data.get("error"):
                results["ocr_error"] = ocr_data["error"]
        
        if api_data:
            results["api_results"] = {
                "success": api_data.get("success", False),
                "data": api_data.get("data", []),
                "error": api_data.get("error")
            }
            results["timing"]["api"] = api_data.get("api_time", 0)
        
        end_time = time.time()
        results["timing"]["total"] = end_time - start_time
        
        return results
    
    def process_pdf_sequential(
        self, 
        pdf_bytes: bytes, 
        filename: str = "document.pdf"
    ) -> Dict:
        """
        Process PDF sequentially (fallback if parallel has issues)
        """
        logger.info("Starting sequential PDF processing")
        results = {
            "ocr_results": [],
            "api_results": {"success": False, "data": [], "error": None},
            "display_images": [],
            "timing": {}
        }
        
        start_time = time.time()
        
        # OCR Pipeline
        ocr_start = time.time()
        try:
            images_for_ocr = self.extractor.pdf_to_images_for_ocr(pdf_bytes)
            ocr_results = self.batch_processor.process_all_batches(images_for_ocr)
            display_images = self.extractor.pdf_to_images_for_display(pdf_bytes)
            
            results["ocr_results"] = ocr_results
            results["display_images"] = display_images
        except Exception as e:
            results["ocr_error"] = str(e)
        
        results["timing"]["ocr"] = time.time() - ocr_start

        logger.info("Completed OCR processing")
        
        # API Pipeline
        logger.info("Starting API extraction")
        api_start = time.time()
        api_result = self.api_extractor.extract_data(pdf_bytes, filename)
        results["api_results"] = {
            "success": api_result.get("success", False),
            "data": api_result.get("data", []),
            "error": api_result.get("error")
        }
        results["timing"]["api"] = time.time() - api_start
        
        results["timing"]["total"] = time.time() - start_time
        logger.info("Completed API extraction")
        return results