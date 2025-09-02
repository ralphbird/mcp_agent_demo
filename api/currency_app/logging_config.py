"""Logging configuration for currency conversion API."""

import json
import logging
import sys


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON.

        Args:
            record: The log record to format

        Returns:
            JSON formatted log string
        """
        log_entry = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "service": "currency-api",
        }

        # Add extra fields if present
        if hasattr(record, "request_id"):
            log_entry["request_id"] = getattr(record, "request_id")  # type: ignore  # noqa: B009
        if hasattr(record, "endpoint"):
            log_entry["endpoint"] = getattr(record, "endpoint")  # type: ignore  # noqa: B009
        if hasattr(record, "method"):
            log_entry["method"] = getattr(record, "method")  # type: ignore  # noqa: B009
        if hasattr(record, "status_code"):
            log_entry["status_code"] = getattr(record, "status_code")  # type: ignore  # noqa: B009
        if hasattr(record, "response_time_ms"):
            log_entry["response_time_ms"] = getattr(record, "response_time_ms")  # type: ignore  # noqa: B009
        if hasattr(record, "user_agent"):
            log_entry["user_agent"] = getattr(record, "user_agent")  # type: ignore  # noqa: B009
        if hasattr(record, "client_ip"):
            log_entry["client_ip"] = getattr(record, "client_ip")  # type: ignore  # noqa: B009

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry, default=str)


def configure_logging() -> None:
    """Configure structured logging for the application."""
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Remove existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create console handler with JSON formatter
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)

    # Set JSON formatter
    json_formatter = JSONFormatter(datefmt="%Y-%m-%dT%H:%M:%S")
    console_handler.setFormatter(json_formatter)

    # Add handler to root logger
    root_logger.addHandler(console_handler)

    # Configure specific loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name.

    Args:
        name: Logger name

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)
