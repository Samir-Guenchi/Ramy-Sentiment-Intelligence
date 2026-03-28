"""
Logging Configuration
=====================
Centralized logging setup using loguru.
"""

import sys
from pathlib import Path


def setup_logger(log_file: str = None, level: str = "INFO"):
    """
    Configure application-wide logging.

    Args:
        log_file: Path to log file. If None, logs to stderr only.
        level: Logging level (DEBUG, INFO, WARNING, ERROR).
    """
    try:
        from loguru import logger

        # Remove default handler
        logger.remove()

        # Console handler with colors
        logger.add(
            sys.stderr,
            level=level,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
                   "<level>{level: <8}</level> | "
                   "<cyan>{name}</cyan>:<cyan>{line}</cyan> — "
                   "<level>{message}</level>",
        )

        # File handler (if specified)
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            logger.add(
                str(log_path),
                rotation="10 MB",
                retention="7 days",
                level=level,
            )

        return logger

    except ImportError:
        import logging

        logging.basicConfig(
            level=getattr(logging, level, logging.INFO),
            format="%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d — %(message)s",
        )
        return logging.getLogger("ramy")
