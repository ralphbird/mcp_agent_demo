.PHONY: help install test lint format type-check quality dev run dashboard clean test-quick markdownlint install-markdownlint install-precommit

# Default target
help:
	@echo "Available commands:"
	@echo ""
	@echo "Development:"
	@echo "  install           - Install dependencies for API service"
	@echo "  install-markdownlint - Install markdownlint globally (run once)"
	@echo "  install-precommit - Install and setup pre-commit hooks (run once)"
	@echo "  run               - Run the API server"
	@echo "  dev               - Run API server in development mode with auto-reload"
	@echo "  dashboard         - Run the Streamlit dashboard (requires API server running)"
	@echo ""
	@echo "Testing & Quality:"
	@echo "  test              - Run all tests with coverage report"
	@echo "  test-quick        - Run tests with minimal output"
	@echo "  lint              - Run linting (ruff check)"
	@echo "  format            - Format code (ruff format)"
	@echo "  type-check        - Run type checking (pyright)"
	@echo "  markdownlint      - Lint markdown files"
	@echo "  quality           - Run all quality checks (format, lint, type-check, markdownlint)"
	@echo "  check             - Run quality checks + tests (full validation)"
	@echo ""
	@echo "Utilities:"
	@echo "  clean             - Clean up temporary files and databases"

# Installation
install:
	@echo "Installing API dependencies..."
	cd api && poetry install

# Run commands
run:
	@echo "Starting Currency Conversion API server..."
	cd api && poetry run python -m currency_app.main

dev:
	@echo "Starting Currency Conversion API server in development mode..."
	cd api && poetry run uvicorn currency_app.main:app --host 0.0.0.0 --port 8000 --reload

dashboard:
	@echo "Starting Streamlit dashboard..."
	@echo "Make sure the API server is running first (make dev in another terminal)"
	cd api && poetry run streamlit run dashboard/app.py

# Testing
test:
	@echo "Running API tests with coverage..."
	cd api && poetry run pytest -v --cov=currency_app --cov-report=term-missing --cov-report=html

test-quick:
	@echo "Running API tests (quick)..."
	cd api && poetry run pytest

# Code quality
format:
	@echo "Formatting API code..."
	cd api && poetry run ruff format .

lint:
	@echo "Linting API code..."
	cd api && poetry run ruff check .

type-check:
	@echo "Type checking API code..."
	cd api && poetry run pyright

markdownlint:
	@echo "Linting markdown files..."
	markdownlint README.md api/README.md CLAUDE.md || true

quality: format lint type-check markdownlint
	@echo "All quality checks completed!"

# Utility commands
clean:
	@echo "Cleaning up temporary files..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name ".pytest_cache" -delete
	find . -type f -name "*.db" -delete
	find . -type f -name "test_*.db" -delete
	cd api && rm -rf .coverage htmlcov/ .coverage.*
	@echo "Cleanup completed!"

# Development workflow
check: quality test
	@echo "Development checks completed - code is ready!"

# Setup markdownlint (run once)
install-markdownlint:
	@echo "Installing markdownlint globally..."
	npm install -g markdownlint-cli
	@echo "markdownlint installed! You can now run 'make markdownlint'"

# Setup pre-commit hooks (run once)
install-precommit:
	@echo "Installing pre-commit..."
	pip install pre-commit
	@echo "Installing pre-commit hooks..."
	pre-commit install
	@echo "Pre-commit hooks installed! They will run automatically before each commit."
	@echo "To run manually: pre-commit run --all-files"

# API-specific commands (for when we have multiple services)
api-install:
	@echo "Installing API dependencies..."
	cd api && poetry install

api-test:
	@echo "Running API tests..."
	cd api && poetry run pytest -v

api-run:
	@echo "Starting API server..."
	cd api && poetry run uvicorn currency_app.main:app --host 0.0.0.0 --port 8000

api-dev:
	@echo "Starting API server in development mode..."
	cd api && poetry run uvicorn currency_app.main:app --host 0.0.0.0 --port 8000 --reload

# Show API endpoints
api-info:
	@echo "Currency Conversion API Information:"
	@echo "  Server: http://localhost:8000"
	@echo "  Docs: http://localhost:8000/docs"
	@echo "  Health: http://localhost:8000/health"
	@echo "  Convert: POST http://localhost:8000/api/v1/convert"

# Quick health check
health-check:
	@echo "Checking API health..."
	cd api && poetry run python -c "from currency_app.main import app; from fastapi.testclient import TestClient; client = TestClient(app); r = client.get('/health'); print('Health Status:', r.status_code, r.json() if r.status_code == 200 else 'FAILED')"
