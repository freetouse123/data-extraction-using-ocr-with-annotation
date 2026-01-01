import logging, os
from logging.handlers import RotatingFileHandler


def setup_logging():
    """
    Configure centralized logging for the application.

    Args:
        app (Flask, optional): Flask application instance
    """
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "application.log")

    file_handler = RotatingFileHandler(
        log_file, maxBytes=1024 * 1024 * 1, backupCount=5  # 1 MB
    )

    # Create console handler
    console_handler = logging.StreamHandler()

    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(lineno)d - %(name)s - %(levelname)s - %(message)s"
    )

    # Set formatter for handlers
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Configure root logger
    logging.basicConfig(level=logging.INFO, handlers=[file_handler, console_handler])

    # Disable the verbose logging for the Azure SDK
    logging.getLogger("azure.core.pipeline.policies.http_logging_policy").setLevel(
        logging.WARNING
    )
    logging.getLogger("azure").setLevel(
        logging.WARNING
    )  # You can suppress other Azure-related logs if needed


def get_logger(name):
    """
    Get a logger for a specific module.

    Args:
        name (str): Name of the logger

    Returns:
        logging.Logger: Configured logger
    """
    return logging.getLogger(name)