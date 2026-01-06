from fastapi import APIRouter, File, UploadFile, HTTPException, Form
from src.data_extraction import DocumentDataExtractor
import uuid
import time
from typing import Literal

data_extraction = APIRouter(
    tags=["data_extraction"],
    prefix="/api/v1"
)


@data_extraction.post("/extract-data", response_model=dict)
async def extract_data(
    pdf: UploadFile = File(...),
    language: Literal["english", "swedish"] = Form(...)
):
    if not pdf.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    extractor = DocumentDataExtractor()

    try:
        start_time = time.time()

        pdf_bytes = await pdf.read()

        doc_result = await extractor.extract_data(pdf_bytes)

        content = doc_result.content  
        response = await extractor.response_generation(
            content=content,
            language=language,
            )

        end_time = time.time()

        return {
            "status": "success",
            "processing_time_seconds": round(end_time - start_time, 2),
            "data": response
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        await extractor.close()