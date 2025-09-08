"""Logging configuration for load tester API."""

import os
import tempfile
from pathlib import Path

from common.logging_config import configure_structlog, get_logger

# Configure structlog for load tester with file logging
# Use temp directory for local testing, /app/logs for Docker
if os.getenv("LOAD_TESTER_LOG_FILE"):
    log_file_path = os.getenv("LOAD_TESTER_LOG_FILE")
elif Path("/app").exists() and os.access("/app", os.W_OK):
    log_file_path = "/app/logs/load_tester.log"
else:
    # For local testing, use temp directory
    temp_dir = Path(tempfile.gettempdir()) / "load_tester_logs"
    temp_dir.mkdir(exist_ok=True)
    log_file_path = str(temp_dir / "load_tester.log")

# Ensure the log directory exists
try:
    if log_file_path:
        os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
        configure_structlog("load-tester", log_file_path=log_file_path)
    else:
        configure_structlog("load-tester")
except (OSError, PermissionError):
    # Fallback to console logging if file logging fails
    configure_structlog("load-tester")

# Re-export get_logger
__all__ = ["get_logger"]
