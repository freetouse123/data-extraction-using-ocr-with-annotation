import os
from dotenv import load_dotenv
load_dotenv()
from .prompt import SYSTEM_PROMPT_FOR_ENTITY_EXTRACTION

class Config:
    system_prompt_for_entity_extraction = SYSTEM_PROMPT_FOR_ENTITY_EXTRACTION
    batch_size = os.getenv("BATCH_SIZE", 3)