"""
Loguru-based logging configuration.
- Colored console output in development
- JSON structured output in production
- Automatic daily log rotation with 30-day retention
"""
from __future__ import annotations

import sys
from pathlib import Path

from loguru import logger

from app.config import settings


def _configure_logger() -> None:
    """Set up loguru sinks based on environment."""
    # Remove the default loguru sink
    logger.remove()

    is_prod = settings.ENVIRONMENT == "production"

    # ── Console sink ──────────────────────────────────────────────────────
    console_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
        "{exception}"
    )
    json_format = (
        '{{"time":"{time:YYYY-MM-DDTHH:mm:ss.SSSZ}",'
        '"level":"{level}",'
        '"logger":"{name}",'
        '"function":"{function}",'
        '"line":{line},'
        '"message":"{message}"}}'
    )

    logger.add(
        sys.stderr,
        level=settings.LOG_LEVEL,
        format=json_format if is_prod else console_format,
        colorize=not is_prod,
        backtrace=not is_prod,
        diagnose=not is_prod,
        enqueue=True,
    )

    # ── File sink ─────────────────────────────────────────────────────────
    log_file = Path(settings.LOG_FILE)
    log_file.parent.mkdir(parents=True, exist_ok=True)

    logger.add(
        str(log_file),
        level="DEBUG",
        format=json_format,
        rotation="00:00",          # New file every midnight
        retention="30 days",
        compression="gz",
        backtrace=True,
        diagnose=False,            # Never expose locals in file logs
        enqueue=True,
        serialize=False,
    )


_configure_logger()

# Export alias for startup hook
setup_logging = _configure_logger

__all__ = ["logger", "setup_logging"]
