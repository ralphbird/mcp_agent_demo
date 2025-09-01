# Currency Conversion API

A FastAPI-based currency conversion service for debugging and learning purposes.

## Features

### Phase 1 (Complete)

- Currency conversion endpoint (`POST /api/v1/convert`)
- Support for 10 major currencies (USD, EUR, GBP, JPY, AUD, CAD, CHF, CNY, SEK, NZD)
- SQLite database for conversion history
- Health check endpoints
- Simulated exchange rates

### Phase 2 (Complete)

- Current exchange rates endpoint (`GET /api/v1/rates`)
- Interactive Streamlit dashboard with:
  - Real-time currency converter
  - Exchange rates table and charts
  - Currency strength visualizations
  - Summary statistics

## Quick Start

### Installation

```bash
# Install dependencies
poetry install

# Run the application
poetry run python -m currency_app.main
```

### API Usage

The API will be available at `http://localhost:8000`

- **API Documentation**: `http://localhost:8000/docs`
- **Health Check**: `http://localhost:8000/health`

### Dashboard Usage

```bash
# Start the API first (in one terminal)
poetry run python -m currency_app.main

# Run the Streamlit dashboard (in another terminal)
poetry run streamlit run dashboard/app.py
```

The dashboard will be available at `http://localhost:8501`

### Example Conversion Request

```bash
curl -X POST "http://localhost:8000/api/v1/convert" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 100.00,
    "from_currency": "USD",
    "to_currency": "EUR"
  }'
```

## Development

### Code Quality

```bash
# Format code
poetry run ruff format .

# Lint code
poetry run ruff check .

# Type checking
poetry run pyright
```

### Testing

```bash
# Run tests
poetry run pytest

# Run tests with verbose output
poetry run pytest -v
```

## Supported Currencies

- USD (US Dollar)
- EUR (Euro)
- GBP (British Pound)
- JPY (Japanese Yen)
- AUD (Australian Dollar)
- CAD (Canadian Dollar)
- CHF (Swiss Franc)
- CNY (Chinese Yuan)
- SEK (Swedish Krona)
- NZD (New Zealand Dollar)
