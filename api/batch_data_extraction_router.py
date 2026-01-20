from models.schema import InputParameter
from typing import Literal
from fastapi import APIRouter, File, UploadFile, HTTPException, Form
from data_extraction.batch_extraction import BatchDocumentExtraction
import time




batch_data_extraction = APIRouter(
    tags=["batch_data_extraction"],
    prefix="/api/v1"
)


@batch_data_extraction.post("/batch-extract-data", response_model=dict)
async def extract_data(
    pdf: UploadFile = File(...),
    language: Literal["english", "swedish"] = Form(...)
):
    # Validate file type
    if not pdf.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    extractor = BatchDocumentExtraction()

    try:
        start_time = time.time()

        # Read PDF bytes
        pdf_bytes = await pdf.read()

        # Call batch extraction with language
        batch_results = await extractor.batch_data_extraction(
            pdf=pdf_bytes,
            language=language
        )

        end_time = time.time()

        return {
            "status": "success",
            "language": language,
            "processing_time_seconds": round(end_time - start_time, 2),
            "data": batch_results
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        await extractor.close()
