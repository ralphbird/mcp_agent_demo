# Currency Conversion Demo

A comprehensive FastAPI-based currency conversion application designed to demonstrate advanced
debugging techniques, monitoring, and observability practices in a realistic microservice environment.

## 🎯 Project Status

**Phase 1: ✅ COMPLETE** - Core API Foundation
**Phase 2: ✅ COMPLETE** - Extended API & Dashboard
**Phase 3: ✅ COMPLETE** - Full Observability & Advanced Features
**Phase 4: ✅ COMPLETE** - Docker Deployment & Production Ready

## 🚀 Features

### Phase 1: Core API Foundation

- **Currency Conversion**: Convert between 10 major currencies with real-time simulated rates
- **Health Monitoring**: Basic and detailed health check endpoints
- **Database Integration**: SQLite storage for complete conversion history
- **Input Validation**: Comprehensive request validation with structured error responses
- **Precision Handling**: Proper decimal precision with banker's rounding for financial accuracy

### Phase 2: Extended API & Dashboard

- **Exchange Rates API**: Current rates endpoint with comprehensive rate data
- **Interactive Dashboard**: Streamlit-based web interface with:
  - Real-time currency converter
  - Exchange rates table and comparison charts
  - Currency strength visualizations
  - Summary statistics and analytics

### Phase 3: Full Observability & Advanced Features

- **Historical Rate Data**: Time-series storage and API for 30+ days of exchange rate history
- **Prometheus Metrics**: HTTP requests, conversions, and database operations monitoring
- **Advanced Dashboard**: Historical trend charts with time-series visualizations
- **Production Monitoring**: `/metrics` endpoint ready for Prometheus/Grafana integration
- **Demo Data Generation**: Realistic historical data with proper base currency handling (USD = 1.0)

### Phase 4: Docker Deployment & Production Ready

- **Docker Containerization**: Multi-stage Dockerfile for API and Dashboard services
- **Docker Compose**: Complete orchestration with persistent volumes and networking
- **Configuration Management**: Pydantic Settings with environment variable support
- **Monitoring Stack**: Optional Prometheus + Grafana deployment with profiles
- **Production Features**: Health checks, proper logging, graceful shutdowns
- **One-Command Deployment**: `make docker-up` for instant stack deployment

### Supported Currencies

- USD (US Dollar), EUR (Euro), GBP (British Pound)
- JPY (Japanese Yen), AUD (Australian Dollar), CAD (Canadian Dollar)
- CHF (Swiss Franc), CNY (Chinese Yuan), SEK (Swedish Krona), NZD (New Zealand Dollar)

### Development Tools

- **Testing**: Comprehensive test suite with 30 tests (unit + integration)
- **Code Quality**: Ruff for formatting/linting + Pyright for type checking + Markdownlint
- **Workflow**: Make commands for streamlined development
- **Dashboard**: Streamlit for interactive data visualization

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
# or: cd api && poetry run streamlit run dashboard/app.py
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
cd api

# Run application
poetry run python -m currency_app.main
poetry run uvicorn currency_app.main:app --reload

# Testing
poetry run pytest -v
poetry run pytest tests/test_currency_service.py

# Code quality
poetry run ruff format .
poetry run ruff check .
poetry run pyright
```

## 📁 Project Structure

```text
mcp_agent_demo/
├── api/                          # Core API service
│   ├── currency_app/            # Main application code
│   │   ├── models/              # Pydantic & SQLAlchemy models
│   │   ├── routers/             # FastAPI route handlers
│   │   ├── services/            # Business logic
│   │   ├── database.py          # Database configuration
│   │   └── main.py              # FastAPI application
│   ├── dashboard/               # Phase 2: Streamlit dashboard
│   │   ├── app.py              # Main dashboard application
│   │   └── __init__.py         # Package initialization
│   ├── tests/                   # Test suite
│   ├── pyproject.toml          # Poetry configuration
│   └── README.md               # API-specific documentation
├── .claude/                    # Development specifications
├── Makefile                   # Development workflow commands
├── CLAUDE.md                  # Claude Code usage instructions
└── README.md                  # This file
```

## 🔮 Roadmap

### Phase 3: Full Observability & Advanced Features (Planned)

- **GET /api/v1/rates/history** - Historical rate data and analytics
- **Monitoring Stack** - Prometheus metrics + Grafana dashboards
- **Load Testing** - Performance testing capabilities
- **Containerization** - Docker + Docker Compose for local deployment

## 🧪 Testing

The project includes a comprehensive test suite with 30 tests:

- **Unit Tests**: Currency service logic, validation, calculations (15 tests)
- **Integration Tests**: API endpoints, database operations, error handling (15 tests)
- **Phase 2 Coverage**: Exchange rates endpoint testing (3 new tests)
- **Edge Cases**: Invalid inputs, boundary conditions, error scenarios

```bash
# Run specific test categories
poetry run pytest tests/test_currency_service.py  # Unit tests
poetry run pytest tests/test_api.py              # Integration tests (includes rates endpoint)
```

## 🏗️ Architecture

**Current Architecture (Phases 1 & 2):**

- **FastAPI**: Modern async web framework with comprehensive API endpoints
- **SQLAlchemy**: Database ORM with SQLite backend
- **Pydantic**: Data validation and serialization
- **Streamlit**: Interactive dashboard for data visualization
- **Plotly**: Advanced charting and visualization components
- **Pandas**: Data manipulation for dashboard analytics
- **Poetry**: Dependency management and packaging
- **Ruff + Pyright + Markdownlint**: Code quality and documentation standards

**Key Design Decisions:**

- **Simulated Rates**: Static exchange rates for consistent testing
- **Decimal Precision**: Financial-grade decimal handling
- **Banker's Rounding**: Industry-standard rounding for currency
- **Request Tracking**: Complete audit trail with UUIDs
- **Structured Errors**: Consistent error response format

## 🤝 Contributing

This is a demo project showcasing incremental development practices. The codebase follows:

- **Code Quality**: Ruff formatting + linting, Pyright type checking, Markdownlint documentation standards
- **Testing**: >80% coverage target with comprehensive test scenarios (30 tests across phases)
- **Documentation**: Inline docstrings + architectural documentation + interactive dashboards
- **Git Workflow**: Descriptive commits with proper attribution and pre-commit hooks

## 📄 License

MIT License - see LICENSE file for details.
