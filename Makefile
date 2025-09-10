.PHONY: help install setup dev run build up down logs rebuild test quality clean docker-clean

# Default target - shows available commands
help:
	@echo "🔥 Load Tester and Dashboard - Development Commands"
	@echo ""
	@echo "📋 Available Commands:"
	@echo "  make install  - Install dependencies with Poetry"
	@echo "  make setup    - Complete setup (install + pre-commit)"
	@echo "  make dev      - Start development servers locally"
	@echo "  make run      - Start load tester API locally"
	@echo "  make up       - Start all services with Docker"
	@echo "  make down     - Stop all Docker services"
	@echo "  make logs     - View Docker service logs"
	@echo "  make rebuild  - Rebuild and restart all Docker services"
	@echo "  make build    - Build Docker containers only"
	@echo "  make test     - Run test suite with coverage"
	@echo "  make quality  - Run code quality checks (format, lint, type-check)"
	@echo "  make clean    - Clean build artifacts and caches"
	@echo "  make docker-clean - Clean all Docker resources"
	@echo ""
	@echo "🚀 Quick Start:"
	@echo "  make setup    - Set up everything for development"
	@echo "  make up       - Start load testing services (requires external currency API)"
	@echo ""
	@echo "💡 Prerequisites: External currency API on localhost:8000"

# Default target when just running 'make'
.DEFAULT_GOAL := help

# Install dependencies
install:
	@echo "📦 Installing dependencies with Poetry..."
	poetry install
	@echo "✅ Dependencies installed!"

# Complete development setup
setup: install
	@echo "🛠️  Setting up development environment..."
	poetry run pre-commit install
	@echo "✅ Development environment ready!"
	@echo ""
	@echo "🚀 Next steps:"
	@echo "  make dev      - Start development servers"
	@echo "  make up       - Start with Docker"
	@echo "  make test     - Run test suite"

# Start development servers locally
dev:
	@echo "🚀 Starting development servers..."
	@echo "📊 Dashboard: http://localhost:8501"
	@echo "🔥 Load Tester: http://localhost:8001"
	@echo ""
	@echo "💡 Make sure your external currency API is running on localhost:8000"
	@echo ""
	@echo "Starting load tester API..."
	LOAD_TESTER_TARGET_API_BASE_URL=http://localhost:8000 poetry run python -m load_tester.main &
	@echo "Starting Streamlit dashboard..."
	poetry run streamlit run dashboard/app.py --server.address 0.0.0.0 --server.port 8501

# Start load tester API locally
run:
	@echo "🚀 Starting load tester API..."
	@echo "🔥 Load Tester API: http://localhost:8001"
	@echo ""
	LOAD_TESTER_TARGET_API_BASE_URL=http://localhost:8000 poetry run python -m load_tester.main

# Build Docker containers
build:
	@echo "🐳 Building Docker containers..."
	docker-compose build
	@echo "✅ Containers built successfully!"

# Start all services with Docker
up:
	@echo "🐳 Starting Load Tester and Dashboard..."
	docker-compose up -d
	@echo "✅ All services started!"
	@echo ""
	@echo "🚀 Available at:"
	@echo "   📊 Dashboard: http://localhost:8501"
	@echo "   🔥 Load Tester: http://localhost:8001"
	@echo ""
	@echo "💡 Make sure your external currency API is running on localhost:8000"
	@echo "Type 'make down' to stop all services"

# Stop all Docker services
down:
	@echo "🐳 Stopping all services..."
	docker-compose down
	@echo "✅ All services stopped!"

# View Docker service logs
logs:
	@echo "📊 Viewing service logs (Ctrl+C to exit)..."
	docker-compose logs -f

# Rebuild and restart all Docker services
rebuild:
	@echo "🔄 Rebuilding and restarting all services..."
	docker-compose down
	docker-compose build
	docker-compose up -d
	@echo "✅ Services rebuilt and restarted!"
	@echo ""
	@echo "🚀 Available at:"
	@echo "   📊 Dashboard: http://localhost:8501"
	@echo "   🔥 Load Tester: http://localhost:8001"

# Run test suite with coverage
test:
	@echo "🧪 Running test suite with coverage..."
	poetry run pytest tests/ -v --cov=load_tester --cov-report=term-missing
	@echo "✅ Tests completed!"

# Run quick tests without coverage
test-fast:
	@echo "🏃 Running tests (fast mode)..."
	poetry run pytest tests/ -v
	@echo "✅ Tests completed!"

# Run code quality checks
quality:
	@echo "🔍 Running code quality checks..."
	@echo "📝 Formatting code..."
	poetry run ruff format load_tester/ dashboard/ tests/
	@echo "🔧 Linting code..."
	poetry run ruff check --fix load_tester/ dashboard/ tests/
	@echo "📋 Type checking..."
	poetry run pyright load_tester/ dashboard/ tests/
	@echo "✅ Quality checks completed!"

# Format code only
format:
	@echo "📝 Formatting code..."
	poetry run ruff format load_tester/ dashboard/ tests/
	@echo "✅ Code formatted!"

# Lint code only
lint:
	@echo "🔧 Linting code..."
	poetry run ruff check --fix load_tester/ dashboard/ tests/
	@echo "✅ Code linted!"

# Type check only
typecheck:
	@echo "📋 Type checking..."
	poetry run pyright load_tester/ dashboard/ tests/
	@echo "✅ Type checking completed!"

# Clean build artifacts and caches
clean:
	@echo "🧹 Cleaning build artifacts and caches..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	rm -rf dist/ build/ .ruff_cache/
	@echo "✅ Cleanup completed!"

# Clean all Docker resources
docker-clean:
	@echo "🧹 Cleaning all Docker resources..."
	docker-compose down -v --rmi local --remove-orphans
	docker system prune -f
	@echo "✅ Docker cleanup completed!"

# Check service health
health:
	@echo "🔍 Checking service health..."
	@echo "Load Tester API:"
	@if command -v curl > /dev/null; then \
		curl -s http://localhost:8001/ || echo "❌ Load Tester not responding at http://localhost:8001"; \
	else \
		echo "❌ curl not found. Please install curl or check http://localhost:8001 manually"; \
	fi
	@echo "Dashboard:"
	@if command -v curl > /dev/null; then \
		curl -s http://localhost:8501/_stcore/health || echo "❌ Dashboard not responding at http://localhost:8501"; \
	else \
		echo "❌ curl not found. Please install curl or check http://localhost:8501 manually"; \
	fi

# Show service status and URLs
status:
	@echo "🔥 Load Tester Status"
	@echo ""
	@echo "🌐 Service URLs:"
	@echo "  Dashboard:     http://localhost:8501"
	@echo "  Load Tester:   http://localhost:8001"
	@echo "  API Docs:      http://localhost:8001/docs"
	@echo ""
	@echo "🔍 Quick Health Check:"
	@make health
