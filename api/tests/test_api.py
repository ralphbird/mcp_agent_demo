"""Integration tests for API endpoints."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from currency_app.database import get_db
from currency_app.main import app
from currency_app.models.database import Base

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_currency.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture
def client():
    """Create test client with test database."""
    # Create test tables
    Base.metadata.create_all(bind=engine)

    with TestClient(app) as test_client:
        yield test_client

    # Clean up
    Base.metadata.drop_all(bind=engine)


class TestHealthEndpoints:
    """Test health check endpoints."""

    def test_basic_health_check(self, client):
        """Test basic health endpoint."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert data["service"] == "currency-conversion-api"

    def test_detailed_health_check(self, client):
        """Test detailed health endpoint."""
        response = client.get("/health/detailed")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["healthy", "unhealthy"]  # Either is acceptable for this test
        assert "checks" in data
        assert "database" in data["checks"]  # Database check should be present


class TestRootEndpoint:
    """Test root endpoint."""

    def test_root_endpoint(self, client):
        """Test root endpoint returns API information."""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Currency Conversion API"
        assert data["version"] == "0.1.0"
        assert data["docs"] == "/docs"
        assert data["health"] == "/health"


class TestConversionEndpoint:
    """Test currency conversion endpoints."""

    def test_convert_usd_to_eur_success(self, client):
        """Test successful USD to EUR conversion."""
        request_data = {"amount": 100.00, "from_currency": "USD", "to_currency": "EUR"}

        response = client.post("/api/v1/convert", json=request_data)

        assert response.status_code == 200
        data = response.json()

        # Check response structure
        assert "conversion_id" in data
        assert "request_id" in data
        assert float(data["amount"]) == 100.0
        assert data["from_currency"] == "USD"
        assert data["to_currency"] == "EUR"
        assert float(data["converted_amount"]) == 85.23
        assert float(data["exchange_rate"]) == 0.8523
        assert "rate_timestamp" in data
        assert "conversion_timestamp" in data
        assert "metadata" in data

        # Check metadata
        metadata = data["metadata"]
        assert metadata["rate_source"] == "simulated"
        assert metadata["calculation_method"] == "direct"
        assert metadata["precision"] == "4"

    def test_convert_same_currency(self, client):
        """Test conversion with same currency."""
        request_data = {"amount": 50.00, "from_currency": "USD", "to_currency": "USD"}

        response = client.post("/api/v1/convert", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert float(data["converted_amount"]) == 50.0
        assert float(data["exchange_rate"]) == 1.0

    def test_convert_lowercase_currencies(self, client):
        """Test conversion with lowercase currency codes."""
        request_data = {"amount": 25.50, "from_currency": "gbp", "to_currency": "jpy"}

        response = client.post("/api/v1/convert", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["from_currency"] == "GBP"
        assert data["to_currency"] == "JPY"
        # GBP to JPY should be > 130 (rough check)
        assert float(data["converted_amount"]) > 3000

    def test_convert_invalid_from_currency(self, client):
        """Test conversion with invalid source currency."""
        request_data = {"amount": 100.00, "from_currency": "INVALID", "to_currency": "EUR"}

        response = client.post("/api/v1/convert", json=request_data)

        assert response.status_code == 422  # Pydantic validation error
        data = response.json()
        assert "detail" in data

    def test_convert_invalid_to_currency(self, client):
        """Test conversion with invalid target currency."""
        request_data = {"amount": 100.00, "from_currency": "USD", "to_currency": "INVALID"}

        response = client.post("/api/v1/convert", json=request_data)

        assert response.status_code == 422  # Pydantic validation error
        data = response.json()
        assert "detail" in data

    def test_convert_zero_amount(self, client):
        """Test conversion with zero amount (should fail validation)."""
        request_data = {"amount": 0.00, "from_currency": "USD", "to_currency": "EUR"}

        response = client.post("/api/v1/convert", json=request_data)

        assert response.status_code == 422  # Validation error

    def test_convert_negative_amount(self, client):
        """Test conversion with negative amount (should fail validation)."""
        request_data = {"amount": -50.00, "from_currency": "USD", "to_currency": "EUR"}

        response = client.post("/api/v1/convert", json=request_data)

        assert response.status_code == 422  # Validation error

    def test_convert_missing_fields(self, client):
        """Test conversion with missing required fields."""
        request_data = {
            "amount": 100.00
            # Missing from_currency and to_currency
        }

        response = client.post("/api/v1/convert", json=request_data)

        assert response.status_code == 422  # Validation error

    def test_convert_invalid_currency_length(self, client):
        """Test conversion with invalid currency code length."""
        request_data = {
            "amount": 100.00,
            "from_currency": "US",  # Too short
            "to_currency": "EUR",
        }

        response = client.post("/api/v1/convert", json=request_data)

        assert response.status_code == 422  # Validation error
