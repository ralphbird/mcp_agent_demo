.PHONY: help up down logs clean rebuild test quality

# Default target - launches everything with monitoring
up:
	@echo "🐳 Starting Currency Conversion API with full monitoring stack..."
	docker-compose up -d
	@echo "✅ All services started!"
	@echo ""
	@echo "🚀 Available at:"
	@echo "   💰 API: http://localhost:8000"
	@echo "   📊 Dashboard: http://localhost:8501"
	@echo "   🔥 Load Tester: http://localhost:8001"
	@echo "   📈 Prometheus: http://localhost:9090"
	@echo "   📉 Grafana: http://localhost:3000 (admin/admin)"
	@echo "   🔍 Jaeger: http://localhost:16686"
	@echo ""
	@echo "Type 'make down' to stop all services"

help:
	@echo "🐳 Currency Conversion API - Docker Commands"
	@echo ""
	@echo "📋 Available Commands:"
	@echo "  make         - Print this help"
	@echo "  make up      - Start all services with full monitoring stack"
	@echo "  make down    - Stop all services"
	@echo "  make logs    - View service logs (Ctrl+C to exit)"
	@echo "  make rebuild - Rebuild containers and restart all services"
	@echo "  make test    - Run tests with coverage"
	@echo "  make quality - Run code quality checks (format, lint, type-check)"
	@echo "  make clean   - Clean all Docker resources (images, volumes, containers)"
	@echo ""
	@echo "🚀 Services Included:"
	@echo "  💰 Currency API (FastAPI)     - http://localhost:8000"
	@echo "  📊 Dashboard (Streamlit)      - http://localhost:8501"
	@echo "  🔥 Load Tester (FastAPI)      - http://localhost:8001"
	@echo "  📈 Prometheus (Metrics)       - http://localhost:9090"
	@echo "  📉 Grafana (Dashboards)       - http://localhost:3000 (admin/admin)"
	@echo "  🔍 Jaeger (Tracing)           - http://localhost:16686"
	@echo ""
	@echo "💡 Quick Start: Just run 'make' to start everything!"

# Default target when just running 'make'
.DEFAULT_GOAL := help

down:
	@echo "🐳 Stopping all services..."
	docker-compose down
	@echo "✅ All services stopped!"

logs:
	@echo "📊 Viewing service logs (Ctrl+C to exit)..."
	docker-compose logs -f

rebuild:
	@echo "🔄 Rebuilding and restarting all services..."
	docker-compose down
	docker-compose build
	docker-compose up -d
	@echo "✅ Services rebuilt and restarted!"
	@echo ""
	@echo "🚀 Available at:"
	@echo "   💰 API: http://localhost:8000"
	@echo "   📊 Dashboard: http://localhost:8501"
	@echo "   🔥 Load Tester: http://localhost:8001"
	@echo "   📈 Prometheus: http://localhost:9090"
	@echo "   📉 Grafana: http://localhost:3000 (admin/admin)"
	@echo "   🔍 Jaeger: http://localhost:16686"

test:
	@echo "🧪 Running tests with coverage..."
	poetry run pytest tests/ -v --cov=currency_app --cov=load_tester --cov-report=term-missing

quality:
	@echo "🔍 Running code quality checks..."
	@echo "📝 Formatting code..."
	poetry run ruff format currency_app/ load_tester/ dashboard/ tests/
	@echo "🔧 Linting code..."
	poetry run ruff check --fix currency_app/ load_tester/ dashboard/ tests/
	@echo "📋 Type checking..."
	poetry run pyright currency_app/ load_tester/ dashboard/ tests/
	@echo "✅ Quality checks completed!"

clean:
	@echo "🧹 Cleaning all Docker resources..."
	docker-compose down -v --rmi local --remove-orphans
	docker system prune -f
	@echo "✅ Cleanup completed!"
