import logging
import sys
from rich.logging import RichHandler
from src.config import config

def setup_logger(name: str = "avscraper"):
    log_level_str = config.get("base.log_level", "INFO").upper()
    log_level = getattr(logging, log_level_str, logging.INFO)

    logging.basicConfig(
        level=log_level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True)]
    )
    
    logger = logging.getLogger(name)
    return logger

logger = setup_logger()
