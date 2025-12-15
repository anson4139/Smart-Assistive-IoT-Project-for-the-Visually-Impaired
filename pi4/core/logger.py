from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from .config import LOG_DIR, LOG_FILE_NAME, LOG_LEVEL

LOG_DIR.mkdir(parents=True, exist_ok=True)

def get_logger(name: str) -> logging.Logger:
    """Return a configured logger with file and console handlers."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    formatter = logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s")
    handler = logging.FileHandler(LOG_DIR / LOG_FILE_NAME, encoding="utf-8")
    handler.setFormatter(formatter)
    handler.setLevel(getattr(logging, LOG_LEVEL.upper(), logging.INFO))

    console = logging.StreamHandler()
    console.setFormatter(formatter)
    console.setLevel(getattr(logging, LOG_LEVEL.upper(), logging.INFO))

    logger.setLevel(getattr(logging, LOG_LEVEL.upper(), logging.INFO))
    logger.addHandler(handler)
    logger.addHandler(console)
    return logger
