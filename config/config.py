import os
from dotenv import load_dotenv
load_dotenv()
from .prompt import SYSTEM_PROMPT_FOR_ENTITY_EXTRACTION
from tenacity import retry,stop_after_attempt,wait_random_exponential,retry_if_exception_type,before_sleep_log

from utils.logger import get_logger
logger = get_logger(__name__)

class Config:
    system_prompt_for_entity_extraction = SYSTEM_PROMPT_FOR_ENTITY_EXTRACTION
    batch_size = os.getenv("BATCH_SIZE_FOR_PAGE", 3)
    OCR_DPI: int = int(os.getenv("OCR_DPI", 300))
    DISPLAY_DPI: int = int(os.getenv("DISPLAY_DPI", 150))
    BATCH_SIZE: int = int(os.getenv("BATCH_SIZE", 5))
    MAX_WORKERS: int = int(os.getenv("MAX_WORKERS", 3))
    SUPPORTED_EXTENSIONS = (
        ".pdf", ".tif", ".tiff", ".jpg", ".jpeg", ".png", ".bmp"
    )

    DEFAULT_FONT = "Times-Roman"



## configuration for retrying operations with tenacity
RETRY_CONFIG = retry(
    reraise=True,
    stop=stop_after_attempt(6),
    wait=wait_random_exponential(min=1, max=60),
    retry=retry_if_exception_type(Exception),
    before_sleep=before_sleep_log(logger, logger.warning),
)