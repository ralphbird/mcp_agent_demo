# Currency Conversion API

A production-ready FastAPI-based currency conversion system with real-time exchange rates,
interactive dashboard, and comprehensive monitoring capabilities.

## ✨ What This System Provides

🏦 **Currency Conversion Service**: Convert between 10 major currencies with simulated
real-time rates and PostgreSQL persistence
📊 **Interactive Web Dashboard**: Streamlit-based interface for currency conversion and
rate visualization
🔥 **Load Testing Platform**: Built-in load testing service to validate API performance
📈 **Production Monitoring**: Prometheus metrics with Grafana dashboards and distributed tracing
🐘 **PostgreSQL Database**: Production-ready database with connection pooling and data persistence

## 🚀 Quick Start (Docker - Recommended)

### Prerequisites

- Docker & Docker Compose
- That's it! No other dependencies required

### ⚡ One-Command Setup

```bash
# Clone the repository
git clone <repository-url>
cd mcp_agent_demo

# Start everything with one command
make
```

This will start all services and you'll see:

```text
🚀 Available at:
   💰 API: http://localhost:8000
   📊 Dashboard: http://localhost:8501
   🔥 Load Tester: http://localhost:8001
   🐘 PostgreSQL: localhost:5432 (currency_user/currency_pass)
   📈 Prometheus: http://localhost:9090
   📉 Grafana: http://localhost:3000 (admin/admin)
   🔍 Jaeger: http://localhost:16686
```

### 🎯 What You Get Out of the Box

- **Currency API** at <http://localhost:8000> with interactive docs at `/docs`
- **Web Dashboard** at <http://localhost:8501> for conversions and charts
- **Load Tester** at <http://localhost:8001> for performance testing
- **PostgreSQL Database** at localhost:5432 with persistent data storage
- **Monitoring Stack** with Prometheus, Grafana, and Jaeger for observability
- **30+ days of demo data** automatically generated in PostgreSQL

### 🐳 Docker Commands

```bash
make up       # Start all services
make down     # Stop all services
make logs     # View service logs
make rebuild  # Rebuild and restart everything
make clean    # Clean all Docker resources
```

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

### Database Architecture

- **Production Database**: PostgreSQL 15 with connection pooling (10 base + 20 overflow connections)
- **Data Persistence**: Volume-backed storage maintains data between container restarts
- **ACID Compliance**: Full transaction support with proper isolation and consistency
- **Testing Database**: SQLite for fast, isolated test execution (228+ tests)
- **Auto-Initialization**: Database tables and demo data created automatically on startup

### Monitoring & Observability

- **Distributed Tracing**: OpenTelemetry integration with Jaeger for end-to-end request tracing
- **Metrics Endpoint**: `/metrics` for Prometheus scraping
- **Pre-configured Grafana**: Dashboards for performance monitoring
- **Request Correlation**: UUID-based tracking with trace context for debugging and analytics
- **Database Monitoring**: Connection health and query performance tracking
- **Structured Logging**: JSON logs with trace correlation and business context

## 🛠️ Alternative Setup (Local Development)

If you prefer to run without Docker (uses SQLite for development, PostgreSQL available via Docker):

### Local Development Prerequisites

- Python 3.12+
- Poetry
- Node.js (for markdown linting)

### Setup

```bash
# Install dependencies
poetry install

# Generate demo data
poetry run python scripts/generate_demo_data.py

# Run the API server
poetry run uvicorn currency_app.main:app --reload

# In another terminal, run the dashboard
poetry run streamlit run dashboard/app.py
```

The API will be available at:

- **Server**: <http://localhost:8000>
- **Documentation**: <http://localhost:8000/docs>
- **Dashboard**: <http://localhost:8501>

## 🧪 Quick Test & Verification

Once your services are running, you can quickly test the system:

```bash
# Quick health check
curl http://localhost:8000/health

# Currency conversion example
curl -X POST "http://localhost:8000/api/v1/convert" \
  -H "Content-Type: application/json" \
  -d '{"amount": 100.00, "from_currency": "USD", "to_currency": "EUR"}'

# Get current exchange rates
curl http://localhost:8000/api/v1/rates
```

## 🔍 Distributed Tracing

The system includes comprehensive distributed tracing with OpenTelemetry and Jaeger.
When running with Docker, access the Jaeger UI at <http://localhost:16686> to view:

- **End-to-End Request Tracing**: Track requests across all services
- **Business Logic Spans**: Currency conversions, rate lookups, and validations
- **Database Query Tracing**: SQLAlchemy instrumentation for database operations
- **HTTP Request Tracing**: FastAPI auto-instrumentation for all endpoints
- **Error Context**: Rich error information with trace correlation

## �️ Development & Testing

### Docker-based Development

For development with auto-reload and debugging:

```bash
# Start with development mode (mounts source code)
docker-compose up --build

# View logs for debugging
make logs

# Run tests
make test

# Code quality checks
make quality
```

### Local Development Commands

If running locally without Docker:

```bash
# Install and setup
poetry install
poetry run python scripts/generate_demo_data.py

# Development server with auto-reload
poetry run uvicorn currency_app.main:app --reload

# Run tests
poetry run pytest tests/ -v

# Code quality
poetry run ruff format .
poetry run ruff check .
poetry run pyright
```

## �📖 API Endpoints

### Core Endpoints

- `POST /api/v1/convert` - Convert currency amounts
- `GET /api/v1/rates` - Get current exchange rates for all supported currencies
- `GET /api/v1/rates/history` - Get historical exchange rates with filtering options
- `GET /health` - Basic health check
- `GET /health/detailed` - Detailed system health with database connectivity
- `GET /metrics` - Prometheus metrics for monitoring
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

## 📁 Project Structure

```text
mcp_agent_demo/
├── currency_app/              # Currency conversion API service
├── dashboard/                 # Streamlit web dashboard
├── load_tester/               # Load testing service
├── docker-compose.yml         # Docker orchestration
├── Dockerfile                 # Multi-stage Docker build
├── Makefile                   # Development commands
└── README.md                  # This documentation
```

## 🧪 Testing

The project includes comprehensive tests with 228+ test cases using SQLite for fast execution:

```bash
# Run all tests (uses SQLite for speed)
make test

# Run specific test modules
poetry run pytest tests/currency_app/ -v        # Currency conversion tests
poetry run pytest tests/load_tester/ -v         # Load testing tests
```

**Database Testing Strategy**:

- **Local Tests**: Use SQLite with isolated databases per test file for speed
- **Docker Production**: Uses PostgreSQL with full ACID compliance and persistence
- **Test Isolation**: Each test suite uses separate databases to prevent interference

## 🤝 Contributing

This project follows modern development practices:

- **Code Quality**: Ruff formatting + linting, Pyright type checking
- **Testing**: Comprehensive test coverage with 228+ tests
- **Documentation**: Clear README and API documentation
- **Container First**: Docker-based workflows

## 📄 License

MIT License - see LICENSE file for details.
