import logging
import os

from dotenv import load_dotenv


load_dotenv()

logging_levels = {
    "CRITICAL": logging.CRITICAL,
    "ERROR": logging.ERROR,
    "WARNING": logging.WARNING,
    "INFO": logging.INFO,
    "DEBUG": logging.DEBUG,
    "NOTSET": logging.NOTSET,
}

LOGGING_LEVEL = logging_levels.get(os.getenv("LOGGING_LEVEL", "INFO"), logging.INFO)
LOGGING_FILENAME = os.getenv("LOGGING_FILENAME", "")
