# Load Tester and Dashboard System

A comprehensive load testing and dashboard system for external currency conversion APIs.
This system provides powerful load testing capabilities and analytics for currency services
running on external endpoints.

## ✨ What This System Provides

📊 **Interactive Web Dashboard**: Streamlit-based interface for load testing and analytics
🔥 **Load Testing Platform**: Built-in load testing service with configurable scenarios
📈 **Performance Analytics**: Real-time metrics and performance visualization
🎯 **External API Testing**: Test any currency conversion API running on localhost:8000

## 🚀 Quick Start (Docker - Recommended)

### Prerequisites

- Docker & Docker Compose
- A currency conversion API running on localhost:8000

### ⚡ One-Command Setup

```bash
# Start load tester and dashboard
make up
```

This will start the load testing services:

```text
🚀 Available at:
   📊 Dashboard: http://localhost:8501
   🔥 Load Tester: http://localhost:8001
```

### 🎯 What You Get Out of the Box

- **Load Testing Dashboard** at <http://localhost:8501> for testing and analytics
- **Load Tester API** at <http://localhost:8001> with interactive docs at `/docs`
- **File-based Logging** for load tester operations
- **Configurable Test Scenarios** with real-time performance monitoring

### 🐳 Docker Commands

```bash
make up                        # Start load testing services
make down                      # Stop all services
make logs                      # View service logs
make rebuild                   # Rebuild and restart everything
make clean                     # Clean all Docker resources
```

## 🚀 Core Features

### Load Testing Service

- **Performance Testing**: Configurable load tests for external API endpoints
- **Real-Time Monitoring**: Live statistics during test execution
- **Custom Scenarios**: Adjustable request rates, currency pairs, and test duration
- **Results Tracking**: Detailed performance metrics and response time analysis
- **File Logging**: All operations logged to files for analysis
- **JWT Authentication**: Support for authenticated API testing

### Interactive Dashboard

- **Load Test Control**: Start, stop, and monitor load tests
- **Performance Analytics**: Real-time metrics and response time visualization
- **Test Results**: Comprehensive test reports and failure analysis
- **Configuration Management**: Easy setup of test scenarios and parameters

### External API Testing

- **Currency Conversion Testing**: Automated testing of currency conversion endpoints
- **Rate Lookup Testing**: Performance testing of exchange rate retrieval
- **Multi-scenario Testing**: Support for different testing patterns and load profiles
- **Error Injection**: Configurable error rates for resilience testing

## 🛠️ Local Development

If you prefer to run without Docker:

### Local Prerequisites

- Python 3.12+
- Poetry

### Setup

```bash
# Install dependencies
poetry install

# Run the load tester API
poetry run python -m load_tester.main

# In another terminal, run the dashboard
poetry run streamlit run dashboard/app.py
```

The services will be available at:

- **Load Tester API**: <http://localhost:8001>
- **Dashboard**: <http://localhost:8501>

## 🧪 Quick Test & Verification

Once your services are running, you can test the load tester:

```bash
# Check load tester health
curl http://localhost:8001/

# Start a load test
curl -X POST "http://localhost:8001/api/load-test/start" \
  -H "Content-Type: application/json" \
  -d '{
    "requests_per_second": 10,
    "duration_seconds": 60,
    "currency_pairs": [["USD", "EUR"], ["GBP", "USD"]]
  }'

# Check load test status
curl http://localhost:8001/api/load-test/status
```

## 🛠️ Development & Testing

### Docker-based Development

```bash
# Start with development mode
make up

# View logs for debugging
make logs

# Run tests
make test

# Code quality checks
make quality
```

### Local Development Commands

```bash
# Install and setup
poetry install

# Run tests
poetry run pytest tests/ -v

# Code quality
poetry run ruff format .
poetry run ruff check .
poetry run pyright
```

## 📖 API Endpoints

### Load Testing Endpoints

- `POST /api/load-test/start` - Start a new load test
- `POST /api/load-test/stop` - Stop the current load test
- `GET /api/load-test/status` - Get current load test status
- `GET /api/load-test/report` - Get load test results
- `GET /api/load-test/scenarios` - List available test scenarios
- `GET /` - API information and available endpoints

### Example API Usage

**Start Load Test:**

```json
POST /api/load-test/start
{
  "requests_per_second": 50,
  "duration_seconds": 300,
  "currency_pairs": [["USD", "EUR"], ["GBP", "JPY"]],
  "amounts": [100, 500, 1000]
}

Response:
{
  "status": "running",
  "config": {
    "requests_per_second": 50,
    "duration_seconds": 300
  },
  "stats": {
    "total_requests": 0,
    "successful_requests": 0,
    "failed_requests": 0
  }
}
```

## 📁 Project Structure

```text
mcp_agent_demo/
├── load_tester/               # Load testing service
├── dashboard/                 # Streamlit web dashboard
├── docker-compose.yml         # Docker orchestration
├── Dockerfile                 # Multi-stage Docker build
├── Makefile                   # Development commands
└── README.md                  # This documentation
```

## 🧪 Testing

The project includes comprehensive tests:

```bash
# Run all tests
make test

# Run specific test modules
poetry run pytest tests/load_tester/ -v         # Load testing tests
poetry run pytest tests/dashboard/ -v           # Dashboard tests
```

## 🤝 Contributing

This project follows modern development practices:

- **Code Quality**: Ruff formatting + linting, Pyright type checking
- **Testing**: Comprehensive test coverage
- **Documentation**: Clear README and API documentation
- **Container First**: Docker-based workflows

## 📄 License

MIT License - see LICENSE file for details.
