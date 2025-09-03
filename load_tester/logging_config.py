"""Logging configuration for load tester API."""

from common.logging_config import configure_structlog, get_logger

# Configure structlog for load tester
configure_structlog("load-tester")

# Re-export get_logger
__all__ = ["get_logger"]
