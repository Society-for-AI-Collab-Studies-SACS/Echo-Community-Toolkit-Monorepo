"""Shared utilities for VesselOS agents."""

import logging
from datetime import datetime


def setup_logging(name: str, level: int = logging.INFO) -> logging.Logger:
    """Create or retrieve a logger with consistent formatting."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    logger.setLevel(level)
    return logger


def timestamp_utc() -> str:
    """Return an ISO8601 UTC timestamp with trailing Z."""
    return datetime.utcnow().isoformat() + "Z"
