# Analytics Service and Dashboard System

A comprehensive load testing and dashboard system for external currency conversion APIs.
This system provides powerful load testing capabilities with advanced attack simulation
for currency services running on external endpoints.

## ✨ What This System Provides

📊 **Interactive Web Dashboard**: Streamlit-based interface for load testing and attack simulation
🔥 **Load Testing Platform**: Built-in analytics service with configurable scenarios
⚡ **Advanced Burst Testing**: Ramping burst tests with single IP simulation for realistic DDoS patterns
🎯 **External API Testing**: Test any currency conversion API running on localhost:8000
🛡️ **IP Spoofing**: Sophisticated IP address rotation and single-source attack simulation

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
   🔥 Analytics Service: http://localhost:8001
```

### 🎯 What You Get Out of the Box

- **Attack Simulation Dashboard** at <http://localhost:8501> for load testing and DDoS simulation
- **Analytics Service API** at <http://localhost:8001> with interactive docs at `/docs`
- **File-based Logging** for analytics service operations
- **Advanced Test Scenarios** with ramping burst tests and IP spoofing

### 🐳 Docker Commands

```bash
make up                        # Start load testing services
make down                      # Stop all services
make logs                      # View service logs
make rebuild                   # Rebuild and restart everything
make clean                     # Clean all Docker resources
```

## 🚀 Core Features

### Analytics Service

- **Performance Testing**: Configurable load tests for external API endpoints
- **Ramping Burst Tests**: Gradual load increase in 10 steps for realistic attack simulation
- **IP Spoofing**: Sophisticated IP address generation from real ISP ranges (US, EU, APAC)
- **Burst Mode**: Single IP attack simulation for authentic DDoS pattern testing
- **Real-Time Monitoring**: Live statistics during test execution
- **Custom Scenarios**: Adjustable request rates, currency pairs, and test duration
- **Error Injection**: Configurable error rates for resilience testing
- **JWT Authentication**: Support for authenticated API testing
- **File Logging**: All operations logged to files for analysis

### Interactive Dashboard

- **Attack Simulation Control**: Start baseline and burst tests with simplified interface
- **Automatic Restart**: Change configurations and restart tests seamlessly
- **Test Status Monitoring**: Clear status indicators for baseline and burst tests
- **Focused Controls**: Essential buttons only - start, stop baseline, stop burst, get reports
- **Auto-stop Timers**: Countdown timers for timed test execution

### External API Testing

- **Currency Conversion Testing**: Automated testing of currency conversion endpoints
- **Rate Lookup Testing**: Performance testing of exchange rate retrieval
- **Multi-scenario Testing**: Support for different testing patterns and load profiles
- **Baseline + Burst Testing**: Concurrent baseline traffic with attack simulation

## 🛠️ Local Development

If you prefer to run without Docker:

### Local Prerequisites

- Python 3.12+
- Poetry

### Setup

```bash
# Install dependencies
poetry install

# Run the analytics service API
poetry run python -m analytics_service.main

# In another terminal, run the dashboard
poetry run streamlit run dashboard/app.py
```

The services will be available at:

- **Analytics Service API**: <http://localhost:8001>
- **Dashboard**: <http://localhost:8501>

## 🧪 Quick Test & Verification

Once your services are running, you can test the analytics service:

```bash
# Check analytics service health
curl http://localhost:8001/

# Start a ramping burst test (gradually increases from 10% to 100% of target RPS)
curl -X POST "http://localhost:8001/api/load-test/burst-ramp?target_rps=100&duration_seconds=180"

# Start a simple load test
curl -X POST "http://localhost:8001/api/load-test/start" \
  -H "Content-Type: application/json" \
  -d '{
    "config": {
      "requests_per_second": 10,
      "burst_mode": false
    }
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
- `POST /api/load-test/burst-ramp` - Start a ramping burst test with gradual RPS increase
- `POST /api/load-test/stop` - Stop the current load test
- `GET /api/load-test/status` - Get current load test status
- `GET /api/load-test/report` - Get load test results
- `GET /api/load-test/scenarios` - List available test scenarios
- `POST /api/load-test/concurrent/{test_id}/start` - Start concurrent baseline tests
- `POST /api/load-test/concurrent/{test_id}/stop` - Stop specific concurrent tests
- `GET /` - API information and available endpoints

### Example API Usage

**Start Load Test:**

```json
POST /api/load-test/start
{
  "config": {
    "requests_per_second": 50,
    "error_injection_enabled": true,
    "error_injection_rate": 0.05,
    "burst_mode": false
  }
}

Response:
{
  "status": "running",
  "config": {
    "requests_per_second": 50,
    "burst_mode": false,
    "error_injection_enabled": true
  },
  "stats": {
    "total_requests": 0,
    "successful_requests": 0,
    "failed_requests": 0
  }
}
```

**Start Ramping Burst Test:**

```bash
POST /api/load-test/burst-ramp?target_rps=200&duration_seconds=300&error_injection_enabled=true

Response:
{
  "status": "running",
  "config": {
    "requests_per_second": 20.0,  // Starts at 10% of target
    "burst_mode": true,
    "error_injection_enabled": true
  }
}
```

## 📁 Project Structure

```text
mcp_agent_demo/
├── analytics_service/         # Analytics and load testing service
├── dashboard/                 # Streamlit web dashboard with attack simulation
├── tests/                     # Comprehensive test suite
├── docker-compose.yml         # Docker orchestration
├── Dockerfile                 # Multi-stage Docker build
├── Makefile                   # Development commands
├── CLAUDE.md                  # Developer guidance
└── README.md                  # This documentation
```

## 🧪 Testing

The project includes comprehensive tests:

```bash
# Run all tests
make test

# Run specific test modules
poetry run pytest tests/analytics_service/ -v   # Analytics service tests
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
