# Currency Conversion Demo

A comprehensive FastAPI-based currency conversion application designed to demonstrate advanced debugging techniques, monitoring, and observability practices in a realistic microservice environment.

## 🎯 Project Status

**Phase 1: ✅ COMPLETE** - Core API Foundation  
**Phase 2: 🚧 Planned** - Extended API & Dashboard  
**Phase 3: 📋 Planned** - Full Observability & Advanced Features

## 🚀 Features (Phase 1)

### Core API

- **Currency Conversion**: Convert between 10 major currencies with real-time simulated rates
- **Health Monitoring**: Basic and detailed health check endpoints
- **Database Integration**: SQLite storage for complete conversion history
- **Input Validation**: Comprehensive request validation with structured error responses
- **Precision Handling**: Proper decimal precision with banker's rounding for financial accuracy

### Supported Currencies

- USD (US Dollar), EUR (Euro), GBP (British Pound)
- JPY (Japanese Yen), AUD (Australian Dollar), CAD (Canadian Dollar)  
- CHF (Swiss Franc), CNY (Chinese Yuan), SEK (Swedish Krona), NZD (New Zealand Dollar)

### Development Tools

- **Testing**: Comprehensive test suite with 27 tests (unit + integration)
- **Code Quality**: Ruff for formatting/linting + Pyright for type checking
- **Workflow**: Make commands for streamlined development

## 🛠️ Quick Start

### Prerequisites

- Python 3.12+
- Poetry

### Installation & Setup

```bash
# Clone and navigate to project
cd mcp_agent_demo

# Install API dependencies
make install
# or: cd api && poetry install

# Run the application
make dev
# or: cd api && poetry run uvicorn currency_app.main:app --reload
```

The API will be available at:

- **Server**: <http://localhost:8000>
- **Documentation**: <http://localhost:8000/docs>  
- **Health Check**: <http://localhost:8000/health>

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
- `GET /health` - Basic health check
- `GET /health/detailed` - Detailed system health with database connectivity
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

## 🛠️ Development

### Make Commands

```bash
make help          # Show all available commands
make install       # Install dependencies  
make dev           # Run development server with auto-reload
make test          # Run all tests with verbose output
make test-quick    # Run tests with minimal output
make quality       # Run formatting, linting, and type checking
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
├── api/                          # Phase 1: Core API service
│   ├── currency_app/            # Main application code
│   │   ├── models/              # Pydantic & SQLAlchemy models
│   │   ├── routers/             # FastAPI route handlers  
│   │   ├── services/            # Business logic
│   │   ├── database.py          # Database configuration
│   │   └── main.py              # FastAPI application
│   ├── tests/                   # Test suite
│   ├── pyproject.toml          # Poetry configuration
│   └── README.md               # API-specific documentation
├── .claude/                    # Development specifications
├── Makefile                   # Development workflow commands
├── CLAUDE.md                  # Claude Code usage instructions
└── README.md                  # This file
```

## 🔮 Roadmap

### Phase 2: Extended API & Dashboard (Planned)

- **GET /api/v1/rates** - Current exchange rates endpoint
- **Rate Management** - Dynamic rate updates and caching
- **Streamlit Dashboard** - Interactive web interface for conversions
- **Enhanced Testing** - Expanded coverage and integration tests

### Phase 3: Full Observability & Advanced Features (Planned)

- **GET /api/v1/rates/history** - Historical rate data and analytics
- **Monitoring Stack** - Prometheus metrics + Grafana dashboards
- **Load Testing** - Performance testing capabilities
- **Containerization** - Docker + Docker Compose deployment
- **CI/CD Pipeline** - Automated testing and deployment

## 🧪 Testing

The project includes a comprehensive test suite:

- **Unit Tests**: Currency service logic, validation, calculations
- **Integration Tests**: API endpoints, database operations, error handling
- **Edge Cases**: Invalid inputs, boundary conditions, error scenarios

```bash
# Run specific test categories
poetry run pytest tests/test_currency_service.py  # Unit tests
poetry run pytest tests/test_api.py              # Integration tests
```

## 🏗️ Architecture

**Phase 1 Architecture:**

- **FastAPI**: Modern async web framework
- **SQLAlchemy**: Database ORM with SQLite backend  
- **Pydantic**: Data validation and serialization
- **Poetry**: Dependency management and packaging
- **Ruff + Pyright**: Code quality and type safety

**Key Design Decisions:**

- **Simulated Rates**: Static exchange rates for consistent testing
- **Decimal Precision**: Financial-grade decimal handling  
- **Banker's Rounding**: Industry-standard rounding for currency
- **Request Tracking**: Complete audit trail with UUIDs
- **Structured Errors**: Consistent error response format

## 🤝 Contributing

This is a demo project showcasing incremental development practices. The codebase follows:

- **Code Quality**: Ruff formatting + linting, Pyright type checking
- **Testing**: >80% coverage target with comprehensive test scenarios  
- **Documentation**: Inline docstrings + architectural documentation
- **Git Workflow**: Descriptive commits with proper attribution

## 📄 License

MIT License - see LICENSE file for details.
