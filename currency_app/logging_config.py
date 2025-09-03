"""Logging configuration for currency conversion API."""

from common.logging_config import configure_structlog, get_logger

# Configure structlog for currency API
configure_structlog("currency-api")

# Re-export get_logger for backward compatibility
__all__ = ["configure_logging", "get_logger"]


def configure_logging() -> None:
    """Configure structured logging for the application.

    Note: This is maintained for backward compatibility.
    Structlog is configured automatically when this module is imported.
    """
    # Structlog is already configured during module import
