import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


def configure_logging(path: Path, foreground: bool = False) -> logging.Logger:
    logger = logging.getLogger("hi_puter")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    handler = RotatingFileHandler(path, maxBytes=1_000_000, backupCount=3)
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(handler)
    if foreground:
        logger.addHandler(logging.StreamHandler())
    return logger
