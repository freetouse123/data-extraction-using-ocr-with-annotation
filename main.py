from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.data_extraction_router import data_extraction
from api.batch_data_extraction_router import batch_data_extraction
from api.image_data_extraction_router import annotate_pdf, annotate_pdf_interactive,extract_ocr_data, pdf_annotation_router
from utils.logger import setup_logging
# Initialize logging
setup_logging()

# Create FastAPI app
app = FastAPI(title="Document Processing API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(data_extraction)
app.include_router(batch_data_extraction)
app.include_router(pdf_annotation_router)



if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)