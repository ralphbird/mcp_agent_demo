.PHONY: help setup install test lint format type-check quality dev run dashboard clean test-quick markdownlint install-markdownlint install-precommit demo-data clean-demo-data

# Default target
help:
	@echo "Available commands:"
	@echo ""
	@echo "🚀 Quick Setup:"
	@echo "  setup             - Complete environment setup: install deps + clean + generate demo data"
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
	@echo "Data & Database:"
	@echo "  demo-data         - Generate demo historical exchange rate data"
	@echo "  clean-demo-data   - Clean database and regenerate demo data"
	@echo ""
	@echo "Utilities:"
	@echo "  clean             - Clean up temporary files and databases"

# Complete environment setup
setup:
	@echo "🚀 Setting up complete development environment..."
	@echo ""
	@echo "📦 Step 1: Installing dependencies..."
	poetry install
	@echo "✅ Dependencies installed"
	@echo ""
	@echo "🧹 Step 2: Cleaning up temporary files and databases..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name ".pytest_cache" -delete
	find . -type f -name "*.db" -delete
	find . -type f -name "test_*.db" -delete
	rm -rf .coverage htmlcov/ .coverage.*
	@echo "✅ Cleanup completed"
	@echo ""
	@echo "📊 Step 3: Generating demo historical data (30 days)..."
	poetry run python scripts/clean_and_regenerate.py
	@echo "✅ Demo data generated"
	@echo ""
	@echo "🧪 Step 4: Running quick tests to verify setup..."
	poetry run pytest api/tests/ -x -q
	@echo "✅ Tests passed"
	@echo ""
	@echo "🎉 Complete setup finished!"
	@echo ""
	@echo "🚀 Ready to start development:"
	@echo "   make dev      # Start API server (http://localhost:8000)"
	@echo "   make dashboard # Start dashboard (http://localhost:8501) [in another terminal]"
	@echo "   make test     # Run full test suite"
	@echo "   make quality  # Run code quality checks"

# Installation
install:
	@echo "Installing dependencies..."
	poetry install

# Run commands
run:
	@echo "Starting Currency Conversion API server..."
	poetry run python -m currency_app.main

dev:
	@echo "Starting Currency Conversion API server in development mode..."
	poetry run uvicorn currency_app.main:app --host 0.0.0.0 --port 8000 --reload

dashboard:
	@echo "Starting Streamlit dashboard..."
	@echo "Make sure the API server is running first (make dev in another terminal)"
	poetry run streamlit run api/dashboard/app.py

# Testing
test:
	@echo "Running API tests with coverage..."
	poetry run pytest api/tests/ -v --cov=currency_app --cov-report=term-missing --cov-report=html

test-quick:
	@echo "Running API tests (quick)..."
	poetry run pytest api/tests/

# Code quality
format:
	@echo "Formatting API code..."
	poetry run ruff format api/

lint:
	@echo "Linting API code..."
	poetry run ruff check --fix api/

type-check:
	@echo "Type checking API code..."
	poetry run pyright api/

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
	rm -rf .coverage htmlcov/ .coverage.*
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
	poetry install

api-test:
	@echo "Running API tests..."
	poetry run pytest api/tests/ -v

api-run:
	@echo "Starting API server..."
	poetry run uvicorn currency_app.main:app --host 0.0.0.0 --port 8000

api-dev:
	@echo "Starting API server in development mode..."
	poetry run uvicorn currency_app.main:app --host 0.0.0.0 --port 8000 --reload

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
	poetry run python -c "from currency_app.main import app; from fastapi.testclient import TestClient; client = TestClient(app); r = client.get('/health'); print('Health Status:', r.status_code, r.json() if r.status_code == 200 else 'FAILED')"

# Generate demo data
demo-data:
	@echo "Generating demo historical exchange rate data..."
	poetry run python scripts/generate_demo_data.py

# Clean database and regenerate data
clean-demo-data:
	@echo "Cleaning database and regenerating demo data..."
	poetry run python scripts/clean_and_regenerate.py
