# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a comprehensive FastAPI-based currency conversion application designed to demonstrate
advanced debugging techniques, monitoring, and observability practices. The project is
**COMPLETE** with all 4 phases implemented:

- **Phase 1**: Core API Foundation (currency conversion, health checks, database)
- **Phase 2**: Extended API & Dashboard (rates endpoint, Streamlit dashboard)
- **Phase 3**: Full Observability (Prometheus metrics, historical data, time-series)
- **Phase 4**: Docker Deployment (containerization, monitoring stack, production-ready)

## Development Commands

### Quick Start

```bash
make setup        # Complete setup: install deps + clean + generate demo data + test
make dev          # Start API server (http://localhost:8000)
make dashboard    # Start Streamlit dashboard (http://localhost:8501) [separate terminal]
```

### Development Workflow

```bash
make install      # Install dependencies
make test         # Run all 117 tests with coverage
make quality      # Run format + lint + type-check + markdownlint
make check        # Run quality + tests (full validation)
```

### Testing Commands

```bash
make test              # Full test suite with coverage report
make test-quick        # Quick test run without coverage
poetry run pytest api/tests/test_api.py -v        # Run specific test file
poetry run pytest api/tests/test_api.py::test_convert_currencies -v  # Run single test
poetry run pytest -k "test_convert" -v           # Run tests matching pattern
```

### Code Quality

```bash
make format       # Format code with ruff
make lint         # Lint code with ruff (auto-fix)
make type-check   # Type checking with pyright
make markdownlint # Lint markdown files
```

### Docker Deployment (Recommended)

```bash
make docker-up       # Start API + Dashboard services
make docker-monitor  # Start with Prometheus + Grafana monitoring
make docker-setup    # Complete setup with demo data generation
make docker-logs     # View service logs
make docker-down     # Stop all services
make docker-clean    # Clean images and volumes
```

### Data Management

```bash
make demo-data        # Generate 30 days of historical exchange rate data
make clean-demo-data  # Clean database and regenerate demo data
```

## Architecture Overview

### Application Structure

```text
api/currency_app/
├── main.py              # FastAPI app with lifespan management, middleware setup
├── config.py            # Pydantic Settings for environment-based configuration
├── database.py          # SQLAlchemy engine, session management
├── routers/             # FastAPI route handlers
│   ├── conversion.py    # Currency conversion endpoints
│   ├── rates.py         # Current + historical rates endpoints
│   └── health.py        # Health check endpoints
├── services/            # Business logic layer
│   ├── currency_service.py        # Core conversion logic with simulated rates
│   └── rates_history_service.py   # Historical data management
├── models/              # Data models
│   ├── conversion.py    # Pydantic models for API requests/responses
│   └── database.py      # SQLAlchemy ORM models
└── middleware/
    └── metrics.py       # Prometheus metrics collection
```

### Key Architectural Patterns

**Configuration Management**: Uses Pydantic Settings (`config.py`) for environment-based
configuration with validation. Settings automatically adapt to Docker vs local environments.

**Database Layer**: SQLAlchemy with dependency injection pattern. Database sessions are
managed via FastAPI dependencies (`get_db()`). Test isolation uses separate test databases.

**Service Layer**: Business logic separated into services (`currency_service.py`,
`rates_history_service.py`) with clear interfaces and comprehensive error handling.

**Metrics & Observability**: Prometheus middleware (`PrometheusMiddleware`) automatically
tracks HTTP requests, response times, and database operations. Metrics available at `/metrics`.

**Testing Strategy**: 117 tests with database isolation. Each test suite uses separate
test databases in `api/tests/databases/`. Integration tests override database dependencies.

### Database Models

**Key Tables**:

- `conversions`: Currency conversion transactions with full audit trail
- `exchange_rates`: Current exchange rates (10 supported currencies)
- `historical_rates`: Time-series data for 30+ days of rate history

**Important**: USD is the base currency (always 1.0). All rates are relative to USD.

### Docker Architecture

**Multi-stage Build**: Single Dockerfile with separate stages for API and Dashboard services.
**Service Orchestration**: docker-compose.yml with persistent volumes, health checks, and
optional monitoring stack (Prometheus + Grafana) via profiles.

## Test Structure and Patterns

### Test Organization

```text
api/tests/
├── test_api.py                 # Integration tests for all endpoints
├── test_currency_service.py    # Unit tests for core business logic
├── test_rates_history_service.py  # Historical data service tests
├── test_models.py              # Pydantic model validation tests
├── test_database.py            # Database connection and migration tests
├── test_metrics_*.py           # Prometheus metrics tests (4 files)
└── databases/                  # Isolated test databases
```

### Test Database Isolation

Each test file uses its own test database to prevent interference:

```python
# Pattern used in integration tests
test_db_path = test_db_dir / "test_specific_name.db"
test_engine = create_engine(f"sqlite:///{test_db_path}")
```

**Important**: Always clean up database dependency overrides in test teardown to prevent
test pollution between different test suites.

### Prometheus Metrics Testing

When testing Prometheus Counter metrics, they create both `_total` and `_created` samples:

```python
# Correct pattern for testing Counter metrics
samples = list(counter.collect())[0].samples
total_samples = [s for s in samples if s.name.endswith('_total')]
assert len(total_samples) > 0
```

## Configuration and Environment

**Local Development**: Uses SQLite database, default ports (8000 for API, 8501 for dashboard)
**Docker Deployment**: Environment variables override defaults, services communicate via
internal networking (`api:8000` for dashboard to API communication)

**Key Environment Variables**:

- `DATABASE_URL`: Database connection string
- `API_BASE_URL`: Dashboard API endpoint (defaults to localhost for local, api:8000 for Docker)

## Development Best Practices in Codebase

**Type Safety**: Comprehensive type annotations, pyright type checking enabled
**Error Handling**: Custom exceptions (`InvalidCurrencyError`), structured error responses
**Financial Precision**: Uses `Decimal` type with banker's rounding (`ROUND_HALF_EVEN`)
**Request Validation**: Pydantic models validate all inputs with detailed error messages
**Observability**: Request tracing with UUIDs, comprehensive metrics collection

## Pre-commit Hooks

Configured hooks run automatically before each commit:

- **Ruff**: Code formatting and linting (Python files in `api/`)
- **Pyright**: Type checking (Python files in `api/`)
- **Markdownlint**: Markdown formatting (all `.md` files)
- **General**: Trailing whitespace, end-of-file-fixer, YAML/TOML validation

Setup: `make install-precommit` (one-time)

## Code Style Requirements

- Use lowercase built-in types: `list`, `dict`, `set`, `tuple` (not `List`, `Dict`, etc.)
- Keep line length to 100 characters
- Use Google-style docstrings
- No trailing whitespace, files end with newline
- Follow ruff rules configured in pyproject.toml
