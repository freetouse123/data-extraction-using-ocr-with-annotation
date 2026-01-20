"""
PDF Annotation API Router
Handles PDF upload and returns annotated PDF with hoverable regions
"""

from fastapi import APIRouter, File, UploadFile, HTTPException, Query
from fastapi.responses import StreamingResponse, JSONResponse
from typing import Optional
import io
import time

from data_extraction.image_data_extraction_v2 import BatchProcessor
from src.pdf_annotator import PdfAnnotator, PdfAnnotatorSimple
from utils.logger import get_logger

logger = get_logger(__name__)

pdf_annotation_router = APIRouter(
    tags=["PDF Annotation"],
    prefix="/api/v1"
)


@pdf_annotation_router.post("/annotate-pdf")
async def annotate_pdf(
    file: UploadFile = File(..., description="PDF file to annotate"),
    annotation_type: str = Query(
        default="popup",
        description="Type of annotation: popup, highlight, invisible_text, all, words, underline"
    ),
    show_confidence: bool = Query(
        default=True,
        description="Show OCR confidence scores in annotations"
    ),
    dpi: int = Query(
        default=300,
        ge=72,
        le=600,
        description="DPI for OCR processing"
    ),
    return_format: str = Query(
        default="pdf",
        description="Return format: pdf or json"
    )
):
    """
    Upload a PDF and receive an annotated PDF with hoverable text regions.
    """
    
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400, 
            detail="Only PDF files are allowed"
        )
    
    try:
        start_time = time.time()
        
        pdf_bytes = await file.read()
        logger.info(f"Processing PDF: {file.filename}, size: {len(pdf_bytes)} bytes")
        
        # Initialize processors
        batch_processor = BatchProcessor()
        pdf_annotator = PdfAnnotator()
        
        # Process PDF with OCR
        ocr_results, used_dpi = batch_processor.process_pdf(
            pdf_bytes=pdf_bytes,
            dpi=dpi
        )
        
        ocr_time = time.time() - start_time
        logger.info(f"OCR completed in {ocr_time:.2f} seconds")
        
        # Create annotated PDF
        annotated_pdf_bytes = pdf_annotator.create_annotated_pdf(
            pdf_bytes=pdf_bytes,
            ocr_results=ocr_results,
            annotation_type=annotation_type,
            show_confidence=show_confidence,
            dpi=used_dpi
        )
        
        total_time = time.time() - start_time
        
        if return_format == "json":
            return JSONResponse({
                "status": "success",
                "filename": file.filename,
                "pages_processed": len(ocr_results),
                "total_annotations": sum(len(r['annotations']) for r in ocr_results),
                "processing_time_seconds": round(total_time, 2),
                "ocr_results": ocr_results
            })
        
        output_filename = file.filename.replace(".pdf", "_annotated.pdf")
        
        return StreamingResponse(
            io.BytesIO(annotated_pdf_bytes),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{output_filename}"',
                "X-Processing-Time": str(round(total_time, 2)),
                "X-Pages-Processed": str(len(ocr_results))
            }
        )
        
    except Exception as e:
        logger.error(f"Error processing PDF: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")


@pdf_annotation_router.post("/annotate-pdf-simple")
async def annotate_pdf_simple(
    file: UploadFile = File(..., description="PDF file to annotate"),
    annotation_style: str = Query(
        default="box",
        description="Annotation style: box, highlight, or underline"
    ),
    dpi: int = Query(default=300, ge=72, le=600)
):
    """
    Create annotated PDF using simplified, more compatible annotations.
    Use this if the main endpoint has compatibility issues.
    """
    
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    try:
        start_time = time.time()
        pdf_bytes = await file.read()
        
        batch_processor = BatchProcessor()
        pdf_annotator = PdfAnnotatorSimple()
        
        ocr_results, used_dpi = batch_processor.process_pdf(pdf_bytes, dpi)
        
        annotated_pdf_bytes = pdf_annotator.create_annotated_pdf(
            pdf_bytes=pdf_bytes,
            ocr_results=ocr_results,
            dpi=used_dpi,
            annotation_style=annotation_style
        )
        
        output_filename = file.filename.replace(".pdf", f"_annotated_{annotation_style}.pdf")
        
        return StreamingResponse(
            io.BytesIO(annotated_pdf_bytes),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{output_filename}"',
                "X-Processing-Time": str(round(time.time() - start_time, 2))
            }
        )
        
    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@pdf_annotation_router.post("/annotate-pdf-interactive")
async def annotate_pdf_interactive(
    file: UploadFile = File(..., description="PDF file to annotate"),
    dpi: int = Query(default=300, ge=72, le=600)
):
    """
    Create a fully interactive PDF with hoverable text regions.
    """
    
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    try:
        start_time = time.time()
        pdf_bytes = await file.read()
        
        batch_processor = BatchProcessor()
        pdf_annotator = PdfAnnotator()
        
        ocr_results, used_dpi = batch_processor.process_pdf(pdf_bytes, dpi)
        
        annotated_pdf_bytes = pdf_annotator.create_interactive_pdf(
            pdf_bytes=pdf_bytes,
            ocr_results=ocr_results,
            dpi=used_dpi
        )
        
        output_filename = file.filename.replace(".pdf", "_interactive.pdf")
        
        return StreamingResponse(
            io.BytesIO(annotated_pdf_bytes),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{output_filename}"',
                "X-Processing-Time": str(round(time.time() - start_time, 2))
            }
        )
        
    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@pdf_annotation_router.post("/annotate-pdf-searchable")
async def annotate_pdf_searchable(
    file: UploadFile = File(...),
    dpi: int = Query(default=300, ge=72, le=600),
    add_highlights: bool = Query(default=False, description="Add subtle highlights over text")
):
    """
    Create a searchable PDF with invisible text layer.
    The text becomes searchable and selectable.
    """
    
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    try:
        start_time = time.time()
        pdf_bytes = await file.read()
        
        batch_processor = BatchProcessor()
        pdf_annotator = PdfAnnotator()
        
        ocr_results, used_dpi = batch_processor.process_pdf(pdf_bytes, dpi)
        
        annotated_pdf_bytes = pdf_annotator.create_searchable_pdf(
            pdf_bytes=pdf_bytes,
            ocr_results=ocr_results,
            dpi=used_dpi,
            add_highlights=add_highlights
        )
        
        output_filename = file.filename.replace(".pdf", "_searchable.pdf")
        
        return StreamingResponse(
            io.BytesIO(annotated_pdf_bytes),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{output_filename}"',
                "X-Processing-Time": str(round(time.time() - start_time, 2))
            }
        )
        
    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@pdf_annotation_router.post("/extract-ocr-data")
async def extract_ocr_data(
    file: UploadFile = File(...),
    dpi: int = Query(default=300, ge=72, le=600)
):
    """
    Extract OCR data from PDF without creating annotated PDF.
    Returns JSON with all extracted text and bounding boxes.
    """
    
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    try:
        start_time = time.time()
        pdf_bytes = await file.read()
        
        batch_processor = BatchProcessor()
        ocr_results, used_dpi = batch_processor.process_pdf(pdf_bytes, dpi)
        
        return {
            "status": "success",
            "filename": file.filename,
            "pages_processed": len(ocr_results),
            "dpi_used": used_dpi,
            "processing_time_seconds": round(time.time() - start_time, 2),
            "ocr_results": ocr_results
        }
        
    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))