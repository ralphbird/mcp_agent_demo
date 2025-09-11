# Multi-stage Docker build for Load Testing Services
FROM python:3.12.11-slim AS base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry==2.1.3

# Configure Poetry
ENV POETRY_NO_INTERACTION=1 \
    POETRY_VENV_IN_PROJECT=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

WORKDIR /app

# Copy Poetry configuration files
COPY pyproject.toml poetry.lock ./

# Install dependencies
RUN poetry install --only=main --no-root && rm -rf $POETRY_CACHE_DIR


# Dashboard Service Stage
FROM base AS dashboard

# Copy application code
COPY dashboard/ ./dashboard/
COPY analytics_service/ ./analytics_service/
COPY common/ ./common/
COPY README.md ./

# Install the application (including the current project)
RUN poetry install --only=main

# Expose port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Run the dashboard
CMD ["poetry", "run", "streamlit", "run", "dashboard/app.py", "--server.address", "0.0.0.0", "--server.port", "8501"]

# Analytics Service Stage
FROM base AS analytics-service

# Copy application code
COPY analytics_service/ ./analytics_service/
COPY common/ ./common/
COPY README.md ./

# Install the application (including the current project)
RUN poetry install --only=main

# Expose port
EXPOSE 9001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:9001/ || exit 1

# Run the analytics service
CMD ["poetry", "run", "python", "-m", "analytics_service.main"]
