import logging
from typing import (
    Literal,
    Optional,
)


def get_logger(name: str, level: Literal[20] = logging.INFO, filename: Optional[str] = None) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(level)
    formatter = logging.Formatter(
        "[%(asctime)s] %(name)s [%(levelname)s] [%(filename)s:%(lineno)d] %(message)s", datefmt="%Y-%m-%dT%H:%M:%S"
    )
    if filename:
        file_handler = logging.FileHandler(filename=filename, encoding="utf-8", mode="w")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    else:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger
