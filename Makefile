.PHONY: help setup install test lint format type-check quality dev run dashboard load-tester load-test-quick load-test-status load-test-stop load-test-light load-test-moderate load-test-heavy load-test-scenarios load-test-report load-test-report-md clean test-quick markdownlint install-markdownlint install-precommit demo-data clean-demo-data docker-build docker-up docker-down docker-logs docker-clean docker-monitor docker-setup docker-rebuild docker-restart docker-load-test

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
	@echo "  load-tester       - Run the Load Tester service (requires API server running)"
	@echo "  load-test-quick   - Run a quick load test (all currency pairs and amounts)"
	@echo "  load-test-status  - Check current load test status"
	@echo "  load-test-light   - Run light load test scenario"
	@echo "  load-test-moderate - Run moderate load test scenario"
	@echo "  load-test-heavy   - Run heavy load test scenario"
	@echo "  load-test-report  - Generate detailed load test report"
	@echo "  load-test-scenarios - List all available test scenarios"
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
	@echo "🐳 Docker:"
	@echo "  docker-build      - Build Docker images"
	@echo "  docker-up         - Start all services (API + Dashboard + Load Tester)"
	@echo "  docker-down       - Stop all Docker services"
	@echo "  docker-rebuild    - Stop, rebuild, and restart all services in one command"
	@echo "  docker-logs       - View Docker service logs"
	@echo "  docker-clean      - Clean Docker images and volumes"
	@echo "  docker-monitor    - Start services with monitoring (Prometheus + Grafana)"
	@echo "  docker-load-test  - Run load test against Docker stack"
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
	poetry run pytest tests/ -x -q
	@echo "✅ Tests passed"
	@echo ""
	@echo "🎉 Complete setup finished!"
	@echo ""
	@echo "🚀 Ready to start development:"
	@echo "   make dev           # Start API server (http://localhost:8000)"
	@echo "   make dashboard     # Start dashboard (http://localhost:8501) [in another terminal]"
	@echo "   make load-tester   # Start load tester (http://localhost:8001) [in another terminal]"
	@echo "   make test          # Run full test suite"
	@echo "   make quality       # Run code quality checks"
	@echo "   make docker-up     # Or start everything with Docker"

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
	poetry run streamlit run dashboard/app.py

# Load Tester commands
load-tester:
	@echo "Starting Load Tester service..."
	@echo "Make sure the API server is running first (make dev in another terminal)"
	poetry run python -m load_tester.main

load-test-quick:
	@echo "Running comprehensive load test..."
	@echo "Starting comprehensive load test (1 req/s for 30 seconds with all currency pairs and amounts)..."
	curl -X POST "http://localhost:8001/api/load-test/start" \
		-H "Content-Type: application/json" \
		-d '{"config": {"requests_per_second": 1.0}}' && \
	sleep 30 && \
	curl -X POST "http://localhost:8001/api/load-test/stop" && \
	curl -s "http://localhost:8001/api/load-test/status" | python -m json.tool

load-test-status:
	@echo "Checking load test status..."
	curl -s "http://localhost:8001/api/load-test/status" | python -m json.tool

load-test-stop:
	@echo "Stopping current load test..."
	curl -X POST "http://localhost:8001/api/load-test/stop" | python -m json.tool

# Scenario-based load tests
load-test-light:
	@echo "Running light load test scenario (0.5 req/s for 60s)..."
	curl -X POST "http://localhost:8001/api/load-test/scenarios/light/start" | python -m json.tool

load-test-moderate:
	@echo "Running moderate load test scenario (5 req/s for 120s)..."
	curl -X POST "http://localhost:8001/api/load-test/scenarios/moderate/start" | python -m json.tool

load-test-heavy:
	@echo "Running heavy load test scenario (15 req/s for 300s)..."
	curl -X POST "http://localhost:8001/api/load-test/scenarios/heavy/start" | python -m json.tool

load-test-scenarios:
	@echo "Available load test scenarios:"
	curl -s "http://localhost:8001/api/load-test/scenarios" | python -m json.tool

load-test-report:
	@echo "Generating load test report..."
	curl -s "http://localhost:8001/api/load-test/report" | python -m json.tool

load-test-report-md:
	@echo "Downloading Markdown load test report..."
	curl -s "http://localhost:8001/api/load-test/report/markdown" -o load_test_report.md
	@echo "Report saved as load_test_report.md"

# Testing
test:
	@echo "Running API tests with coverage..."
	poetry run pytest tests/ -v --cov=currency_app --cov=load_tester --cov-report=term-missing --cov-report=html

test-quick:
	@echo "Running API tests (quick)..."
	poetry run pytest tests/

# Code quality
format:
	@echo "Formatting API code..."
	poetry run ruff format currency_app/ load_tester/ dashboard/ tests/

lint:
	@echo "Linting API code..."
	poetry run ruff check --fix currency_app/ load_tester/ dashboard/ tests/

type-check:
	@echo "Type checking API code..."
	poetry run pyright currency_app/ load_tester/ dashboard/ tests/

markdownlint:
	@echo "Linting markdown files..."
	markdownlint README.md CLAUDE.md

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
	poetry run pytest tests/ -v

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

# Docker commands
docker-build:
	@echo "🐳 Building Docker images..."
	docker-compose build
	@echo "✅ Docker images built successfully!"

docker-up:
	@echo "🐳 Starting all services with Docker Compose..."
	docker-compose up -d
	@echo "✅ Services started!"
	@echo ""
	@echo "🚀 Services available at:"
	@echo "   API: http://localhost:8000"
	@echo "   API Docs: http://localhost:8000/docs"
	@echo "   Dashboard: http://localhost:8501"
	@echo "   Load Tester: http://localhost:8001"
	@echo "   Load Tester Docs: http://localhost:8001/docs"
	@echo "   Metrics: http://localhost:8000/metrics"
	@echo "   Load Tester Metrics: http://localhost:8001/metrics"
	@echo ""
	@echo "📊 View logs: make docker-logs"
	@echo "🔥 Run load test: make docker-load-test"
	@echo "🛑 Stop services: make docker-down"

docker-down:
	@echo "🐳 Stopping Docker services..."
	docker-compose down
	@echo "✅ Services stopped!"

docker-logs:
	@echo "📊 Viewing Docker service logs (press Ctrl+C to exit)..."
	docker-compose logs -f

docker-clean:
	@echo "🧹 Cleaning Docker images and volumes..."
	docker-compose down -v --rmi all --remove-orphans
	docker system prune -f
	@echo "✅ Docker cleanup completed!"

docker-monitor:
	@echo "🐳 Starting services with monitoring stack..."
	docker-compose --profile monitoring up -d
	@echo "✅ Services with monitoring started!"
	@echo ""
	@echo "🚀 Services available at:"
	@echo "   API: http://localhost:8000"
	@echo "   Dashboard: http://localhost:8501"
	@echo "   Load Tester: http://localhost:8001"
	@echo "   Prometheus: http://localhost:9090"
	@echo "   Grafana: http://localhost:3000 (admin/admin)"
	@echo ""
	@echo "📊 View logs: make docker-logs"
	@echo "🔥 Run load test: make docker-load-test"
	@echo "🛑 Stop services: make docker-down"

docker-load-test:
	@echo "🔥 Running comprehensive load test against Docker stack..."
	@echo "Starting comprehensive load test (5 req/s for 60 seconds with all currency pairs and amounts)..."
	curl -X POST "http://localhost:8001/api/load-test/start" \
		-H "Content-Type: application/json" \
		-d '{"config": {"requests_per_second": 5.0}}' && \
	@echo "Load test started! Monitoring for 60 seconds..." && \
	sleep 60 && \
	@echo "Stopping load test and showing results..." && \
	curl -X POST "http://localhost:8001/api/load-test/stop" && \
	echo "" && \
	curl -s "http://localhost:8001/api/load-test/status" | python -m json.tool

# Docker development workflow
docker-setup: docker-build
	@echo "🐳 Setting up Docker environment..."
	make docker-up
	@echo "⏳ Waiting for services to be ready..."
	sleep 10
	@echo "🗄️ Generating demo data in container..."
	docker-compose exec api poetry run python scripts/generate_demo_data.py
	@echo "✅ Docker setup completed!"

docker-rebuild:
	@echo "🐳 Rebuilding and restarting services..."
	docker-compose down
	docker-compose build
	make docker-up
