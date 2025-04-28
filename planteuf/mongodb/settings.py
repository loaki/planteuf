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
MONGO_USERNAME = os.getenv("MONGO_USERNAME", "")
MONGO_PASSWORD = os.getenv("MONGO_PASSWORD", "")
MONGO_HOST = os.getenv("MONGO_HOST", "")
MONGO_PORT = os.getenv("MONGO_PORT", 0)
MONGO_DB = os.getenv("MONGO_DB", "")
