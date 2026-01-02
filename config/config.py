import os
from dotenv import load_dotenv
load_dotenv()
from .prompt import SYSTEM_PROMPT_FOR_ENTITY_EXTRACTION

class Config:
    system_prompt_for_entity_extraction = SYSTEM_PROMPT_FOR_ENTITY_EXTRACTION
    batch_size = os.getenv("BATCH_SIZE_FOR_PAGE", 3)
    OCR_DPI: int = int(os.getenv("OCR_DPI", 300))
    DISPLAY_DPI: int = int(os.getenv("DISPLAY_DPI", 150))
    BATCH_SIZE: int = int(os.getenv("BATCH_SIZE", 5))
    MAX_WORKERS: int = int(os.getenv("MAX_WORKERS", 3))