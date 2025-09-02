# Multi-stage Docker build for Currency Conversion API
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

# API Service Stage
FROM base AS api

# Copy application code
COPY currency_app/ ./currency_app/
COPY load_tester/ ./load_tester/
COPY dashboard/ ./dashboard/
COPY tests/ ./tests/
COPY scripts/ ./scripts/
COPY README.md ./

# Install the application (including the current project)
RUN poetry install --only=main

# Create directories for data persistence
RUN mkdir -p /app/data /app/tests/currency_app/databases

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the API
CMD ["poetry", "run", "uvicorn", "currency_app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# Dashboard Service Stage
FROM base AS dashboard

# Copy application code
COPY currency_app/ ./currency_app/
COPY load_tester/ ./load_tester/
COPY dashboard/ ./dashboard/
COPY tests/ ./tests/
COPY scripts/ ./scripts/
COPY README.md ./

# Install the application (including the current project)
RUN poetry install --only=main

# Create directories for data persistence
RUN mkdir -p /app/data

# Expose port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Run the dashboard
CMD ["poetry", "run", "streamlit", "run", "dashboard/app.py", "--server.address", "0.0.0.0", "--server.port", "8501"]

# Load Tester Service Stage
FROM base AS load-tester

# Copy application code
COPY currency_app/ ./currency_app/
COPY load_tester/ ./load_tester/
COPY dashboard/ ./dashboard/
COPY tests/ ./tests/
COPY scripts/ ./scripts/
COPY README.md ./

# Install the application (including the current project)
RUN poetry install --only=main

# Expose port
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8001/ || exit 1

# Run the load tester
CMD ["poetry", "run", "python", "-m", "load_tester.main"]
