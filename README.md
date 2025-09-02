# Currency Conversion API

A production-ready FastAPI-based currency conversion system with real-time exchange rates,
historical data tracking, interactive dashboard, and comprehensive monitoring capabilities.

## ✨ What This System Provides

**Currency Conversion Service**: Convert between 10 major currencies with simulated real-time rates
and complete transaction history.

**Interactive Web Dashboard**: Streamlit-based interface for currency conversion, rate visualization,
and historical trend analysis.

**Load Testing Platform**: Built-in load testing service to validate API performance under various
traffic conditions.

**Production Monitoring**: Prometheus metrics integration with optional Grafana dashboards for
comprehensive observability.

## 🚀 Core Features

### Currency API Features

- **Multi-Currency Support**: Convert between USD, EUR, GBP, JPY, AUD, CAD, CHF, CNY, SEK, NZD
- **Real-Time Rates**: Simulated exchange rates that update dynamically
- **Financial Precision**: Proper decimal handling with banker's rounding for accuracy
- **Complete Audit Trail**: Every conversion tracked with unique IDs and timestamps
- **Comprehensive Validation**: Structured error responses with detailed validation messages

### Interactive Dashboard

- **Currency Converter**: Real-time conversion with rate visualization
- **Exchange Rate Tables**: Current rates display with comparison tools
- **Historical Charts**: Time-series visualizations of rate trends over 30+ days
- **Currency Analytics**: Strength indicators and statistical summaries
- **Rate Comparison**: Side-by-side currency performance analysis

### Load Testing Service

- **Performance Testing**: Configurable load tests for API endpoints
- **Real-Time Monitoring**: Live statistics during test execution
- **Custom Scenarios**: Adjustable request rates, currency pairs, and test duration
- **Results Tracking**: Detailed performance metrics and response time analysis

### Production-Ready Features

- **Health Monitoring**: Basic and detailed health check endpoints with dependency validation
- **Prometheus Metrics**: HTTP requests, response times, conversion counts, and database operations
- **Historical Data**: 30+ days of exchange rate history with time-series analysis
- **Docker Deployment**: Complete containerization with orchestration and persistent storage
- **Configuration Management**: Environment-based settings with validation

### Monitoring & Observability

- **Metrics Endpoint**: `/metrics` for Prometheus scraping
- **Optional Grafana**: Pre-configured dashboards for performance monitoring
- **Request Tracing**: UUID-based tracking for debugging and analytics
- **Database Monitoring**: Connection health and query performance tracking

## 🛠️ Quick Start

### Prerequisites

#### Option 1: Local Development**

- Python 3.12+
- Poetry
- Node.js (for markdown linting)

#### Option 2: Docker Deployment**

- Docker & Docker Compose
- No other dependencies required!

### ⚡ One-Command Setup

```bash
# Clone and navigate to project
cd mcp_agent_demo

# Complete setup: install deps + clean + generate demo data + verify
make setup
```

This single command will:

- 📦 Install all Python dependencies
- 🧹 Clean up any existing files/databases
- 📊 Generate 30 days of realistic historical exchange rate data
- 🧪 Run tests to verify everything works
- ✅ USD rates correctly fixed at 1.000000 (base currency)

### Manual Installation (Alternative)

```bash
# Install dependencies only
make install

# Run the API server
make dev
```

The API will be available at:

- **Server**: <http://localhost:8000>
- **Documentation**: <http://localhost:8000/docs>
- **Health Check**: <http://localhost:8000/health>

### Dashboard Setup

```bash
# Start the API first (in one terminal)
make dev

# Run the Streamlit dashboard (in another terminal)
make dashboard
# or: poetry run streamlit run dashboard/app.py
```

The dashboard will be available at:

- **Dashboard**: <http://localhost:8501>

### 🐳 Docker Deployment (Recommended)

The easiest way to run the complete application stack:

```bash
# Build and start all services
make docker-up

# Or manually:
docker-compose up -d
```

This will start:

- **API**: <http://localhost:8000> (FastAPI with automatic demo data)
- **Dashboard**: <http://localhost:8501> (Streamlit interface)
- **Metrics**: <http://localhost:8000/metrics> (Prometheus metrics)

#### Docker Commands

```bash
# Complete Docker setup (build + start + demo data)
make docker-setup

# View service logs
make docker-logs

# Stop all services
make docker-down

# Clean everything (images, volumes, containers)
make docker-clean

# Start with monitoring stack (Prometheus + Grafana)
make docker-monitor
```

#### With Monitoring Stack

```bash
# Start with Prometheus & Grafana
make docker-monitor
```

Additional services available:

- **Prometheus**: <http://localhost:9090> (Metrics collection)
- **Grafana**: <http://localhost:3000> (admin/admin - Dashboards)

### Quick Test

```bash
# Run all tests
make test

# Quick health check
make health-check

# Currency conversion example
curl -X POST "http://localhost:8000/api/v1/convert" \
  -H "Content-Type: application/json" \
  -d '{"amount": 100.00, "from_currency": "USD", "to_currency": "EUR"}'
```

## 📖 API Endpoints

### Core Endpoints

- `POST /api/v1/convert` - Convert currency amounts
- `GET /api/v1/rates` - Get current exchange rates for all supported currencies
- `GET /api/v1/rates/history` - Get historical exchange rates with filtering options
- `GET /health` - Basic health check
- `GET /health/detailed` - Detailed system health with database connectivity
- `GET /metrics` - Prometheus metrics for monitoring (Phase 3)
- `GET /` - API information and links

### Example API Usage

**Convert Currency:**

```json
POST /api/v1/convert
{
  "amount": 100.00,
  "from_currency": "USD",
  "to_currency": "EUR"
}

Response:
{
  "conversion_id": "uuid",
  "amount": 100.00,
  "converted_amount": 85.23,
  "exchange_rate": 0.8523,
  "from_currency": "USD",
  "to_currency": "EUR",
  "rate_timestamp": "2025-08-29T10:30:00Z",
  "conversion_timestamp": "2025-08-29T10:30:15Z"
}
```

**Get Current Rates:**

```json
GET /api/v1/rates

Response:
{
  "base_currency": "USD",
  "rates": [
    {
      "currency": "USD",
      "rate": 1.0000,
      "last_updated": "2025-08-29T10:30:00Z"
    },
    {
      "currency": "EUR",
      "rate": 0.8523,
      "last_updated": "2025-08-29T10:30:00Z"
    }
  ],
  "timestamp": "2025-08-29T10:30:15Z",
  "metadata": {
    "rate_source": "simulated",
    "total_currencies": "10"
  }
}
```

## 🛠️ Development

### Make Commands

```bash
make help          # Show all available commands
make install       # Install dependencies
make dev           # Run development server with auto-reload
make dashboard     # Run Streamlit dashboard (requires API server running)
make test          # Run all tests with verbose output
make test-quick    # Run tests with minimal output
make quality       # Run formatting, linting, type checking, and markdown linting
make markdownlint  # Lint markdown files
make clean         # Clean up temporary files and databases
make check         # Run quality checks + tests (full validation)
```

### Manual Commands

```bash
# Run applications
poetry run python -m currency_app.main              # Currency API
poetry run uvicorn currency_app.main:app --reload   # Currency API with auto-reload
poetry run streamlit run dashboard/app.py           # Dashboard
poetry run python -m load_tester.main               # Load tester

# Testing
poetry run pytest -v                                # All tests
poetry run pytest tests/currency_app/ -v            # Currency app tests
poetry run pytest tests/load_tester/ -v             # Load tester tests

# Code quality
poetry run ruff format .                            # Format code
poetry run ruff check .                             # Lint code
poetry run pyright                                  # Type checking
```

## 📁 Project Structure

```text
mcp_agent_demo/
├── currency_app/               # Currency conversion API service
│   ├── models/                # Pydantic & SQLAlchemy models
│   ├── routers/               # FastAPI route handlers
│   ├── services/              # Business logic
│   ├── middleware/            # Prometheus metrics middleware
│   ├── database.py            # Database configuration
│   └── main.py                # FastAPI application
├── dashboard/                  # Streamlit web dashboard
│   └── app.py                 # Interactive dashboard application
├── load_tester/               # Load testing service
│   ├── models/                # Load test configuration models
│   ├── services/              # Load testing logic
│   ├── routers/               # Load test API endpoints
│   └── main.py                # Load tester FastAPI application
├── tests/                     # Test suite organized by module
│   ├── currency_app/          # Currency API tests
│   ├── load_tester/           # Load tester tests
│   └── dashboard/             # Dashboard tests
├── pyproject.toml             # Poetry configuration
├── Makefile                   # Development workflow commands
├── CLAUDE.md                  # Claude Code usage instructions
└── README.md                  # This documentation
```

## 🧪 Testing

The project includes a comprehensive test suite with 228 tests organized by module:

- **Currency App Tests**: API endpoints, service logic, database operations, and metrics
- **Load Tester Tests**: Load testing manager functionality and configuration
- **Dashboard Tests**: (Future dashboard-specific tests)
- **Coverage Areas**: Unit tests, integration tests, edge cases, and error scenarios

```bash
# Run specific test modules
poetry run pytest tests/currency_app/ -v        # Currency conversion tests
poetry run pytest tests/load_tester/ -v        # Load testing tests
poetry run pytest tests/currency_app/test_api.py -v  # API integration tests
poetry run pytest tests/currency_app/test_currency_service.py -v  # Service unit tests
```

## 🏗️ Architecture

### Technology Stack

- **FastAPI**: Modern async web framework with comprehensive API endpoints
- **SQLAlchemy**: Database ORM with SQLite backend for development
- **Pydantic**: Data validation, serialization, and settings management
- **Streamlit**: Interactive dashboard for data visualization and analytics
- **Plotly**: Advanced charting and visualization components
- **Pandas**: Data manipulation for dashboard analytics
- **Prometheus**: Metrics collection and monitoring integration
- **Poetry**: Dependency management and packaging
- **Docker**: Containerization with multi-stage builds
- **Ruff + Pyright**: Code quality, formatting, linting, and type checking

### Key Design Principles

- **Financial Precision**: Decimal-based calculations with banker's rounding for currency accuracy
- **Request Tracing**: Complete audit trail with UUID tracking for all transactions
- **Structured Validation**: Comprehensive input validation with detailed error responses
- **Separation of Concerns**: Clean architecture with separate service, router, and model layers
- **Observability First**: Built-in metrics, health checks, and monitoring capabilities
- **Container Ready**: Production deployment via Docker with persistent data storage

## 🤝 Contributing

This is a production-ready demo project showcasing modern development practices. The codebase follows:

- **Code Quality**: Ruff formatting + linting, Pyright type checking, Markdownlint documentation standards
- **Testing**: Comprehensive test coverage with 228+ tests across all modules
- **Documentation**: Inline docstrings, architectural documentation, and interactive dashboards
- **Git Workflow**: Descriptive commits with proper attribution and pre-commit hooks
- **Container First**: Docker-based development and deployment workflows

## 📄 License

MIT License - see LICENSE file for details.
