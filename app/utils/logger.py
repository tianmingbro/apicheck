"""Application logging configuration."""
import logging
import sys
from app.core.config import settings


def setup_logging() -> None:
    """Configure structured logging for the application.

    - DEBUG level to stdout in debug mode, INFO otherwise
    - Includes exc_info for ERROR-level tracebacks
    - Format: timestamp | level | logger: message
    """
    level = logging.DEBUG if settings.DEBUG else getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    handler.setFormatter(logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    ))

    # Configure root logger
    root = logging.getLogger()
    root.setLevel(level)
    # Remove any existing handlers to avoid duplicates
    root.handlers.clear()
    root.addHandler(handler)

    # Silence noisy third-party loggers in production
    if not settings.DEBUG:
        for noisy in ("httpx", "httpcore", "urllib3", "apscheduler", "sqlalchemy.engine"):
            logging.getLogger(noisy).setLevel(logging.WARNING)

    # Log startup info
    logger = logging.getLogger(__name__)
    logger.info("Logging configured (level=%s)", logging.getLevelName(level))
