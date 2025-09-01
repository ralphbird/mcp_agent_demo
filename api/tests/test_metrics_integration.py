"""Integration tests for Prometheus metrics with FastAPI application."""

import re

import pytest
from fastapi.testclient import TestClient

from currency_app.main import app
from currency_app.middleware.metrics import (
    CURRENCY_CONVERSIONS_TOTAL,
    DATABASE_OPERATIONS_TOTAL,
    IN_PROGRESS_REQUESTS,
    RATES_REQUESTS_TOTAL,
    REQUEST_COUNT,
    REQUEST_DURATION,
)


class TestMetricsIntegration:
    """Integration test cases for metrics with full application."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture(autouse=True)
    def clear_metrics(self):
        """Clear Prometheus metrics before each test."""
        REQUEST_COUNT.clear()
        REQUEST_DURATION.clear()
        IN_PROGRESS_REQUESTS.set(0)
        CURRENCY_CONVERSIONS_TOTAL.clear()
        RATES_REQUESTS_TOTAL.clear()
        DATABASE_OPERATIONS_TOTAL.clear()

    def test_root_endpoint_generates_metrics(self, client):
        """Test that root endpoint generates HTTP metrics."""
        response = client.get("/")
        assert response.status_code == 200

        # Check metrics
        metrics_response = client.get("/metrics")
        content = metrics_response.text

        # Should show request to root endpoint
        assert 'http_requests_total{endpoint="/",method="GET",status_code="200"} 1.0' in content
        assert 'http_request_duration_seconds_count{endpoint="/",method="GET"} 1.0' in content

    def test_health_endpoint_generates_metrics(self, client):
        """Test that health endpoint generates HTTP metrics."""
        response = client.get("/health")
        assert response.status_code == 200

        # Check metrics
        metrics_response = client.get("/metrics")
        content = metrics_response.text

        # Should show request to health endpoint
        assert (
            'http_requests_total{endpoint="/health",method="GET",status_code="200"} 1.0' in content
        )

    def test_currency_conversion_generates_multiple_metrics(self, client):
        """Test that currency conversion generates both HTTP and application metrics."""
        # Make conversion request
        response = client.post(
            "/api/v1/convert", json={"amount": 100.0, "from_currency": "USD", "to_currency": "EUR"}
        )
        assert response.status_code == 200

        # Check metrics
        metrics_response = client.get("/metrics")
        content = metrics_response.text

        # Should show HTTP metrics
        assert (
            'http_requests_total{endpoint="/api/v1/convert",method="POST",status_code="200"} 1.0'
            in content
        )

        # Should show currency conversion metrics
        assert (
            'currency_conversions_total{from_currency="USD",status="success",to_currency="EUR"} 1.0'
            in content
        )

    def test_rates_endpoint_generates_application_metrics(self, client):
        """Test that rates endpoint generates application-specific metrics."""
        response = client.get("/api/v1/rates")
        assert response.status_code == 200

        # Check metrics
        metrics_response = client.get("/metrics")
        content = metrics_response.text

        # Should show HTTP metrics
        assert (
            'http_requests_total{endpoint="/api/v1/rates",method="GET",status_code="200"} 1.0'
            in content
        )

        # Should show rates request metrics
        assert 'rates_requests_total{endpoint="current_rates",status="success"} 1.0' in content

    def test_historical_rates_endpoint_generates_metrics(self, client):
        """Test that historical rates endpoint generates metrics."""
        response = client.get("/api/v1/rates/history")
        assert response.status_code == 200

        # Check metrics
        metrics_response = client.get("/metrics")
        content = metrics_response.text

        # Should show HTTP metrics
        assert (
            'http_requests_total{endpoint="/api/v1/rates/history",method="GET",status_code="200"} 1.0'
            in content
        )

        # Should show rates request metrics
        assert 'rates_requests_total{endpoint="rates_history",status="success"} 1.0' in content

    def test_error_requests_generate_error_metrics(self, client):
        """Test that error requests generate appropriate error metrics."""
        # Invalid conversion request
        response = client.post(
            "/api/v1/convert",
            json={
                "amount": -100.0,  # Negative amount should fail validation
                "from_currency": "USD",
                "to_currency": "EUR",
            },
        )
        assert response.status_code == 422

        # Check metrics
        metrics_response = client.get("/metrics")
        content = metrics_response.text

        # Should show HTTP error metrics
        assert (
            'http_requests_total{endpoint="/api/v1/convert",method="POST",status_code="422"} 1.0'
            in content
        )

    def test_invalid_currency_generates_error_metrics(self, client):
        """Test that invalid currency requests generate error metrics."""
        # Request with invalid currency (passes Pydantic but fails service)
        response = client.post(
            "/api/v1/convert", json={"amount": 100.0, "from_currency": "XYZ", "to_currency": "EUR"}
        )
        assert response.status_code == 400

        # Check metrics
        metrics_response = client.get("/metrics")
        content = metrics_response.text

        # Should show HTTP error metrics
        assert (
            'http_requests_total{endpoint="/api/v1/convert",method="POST",status_code="400"} 1.0'
            in content
        )

        # Should show currency conversion error metrics
        assert (
            'currency_conversions_total{from_currency="XYZ",status="error",to_currency="EUR"} 1.0'
            in content
        )

    def test_multiple_requests_accumulate_metrics(self, client):
        """Test that multiple requests accumulate metrics correctly."""
        # Make multiple requests
        client.get("/")
        client.get("/")
        client.get("/health")
        client.post(
            "/api/v1/convert", json={"amount": 100.0, "from_currency": "USD", "to_currency": "EUR"}
        )
        client.post(
            "/api/v1/convert", json={"amount": 50.0, "from_currency": "EUR", "to_currency": "GBP"}
        )

        # Check metrics
        metrics_response = client.get("/metrics")
        content = metrics_response.text

        # Should show accumulated HTTP metrics
        assert 'http_requests_total{endpoint="/",method="GET",status_code="200"} 2.0' in content
        assert (
            'http_requests_total{endpoint="/health",method="GET",status_code="200"} 1.0' in content
        )
        assert (
            'http_requests_total{endpoint="/api/v1/convert",method="POST",status_code="200"} 2.0'
            in content
        )

        # Should show accumulated conversion metrics
        assert (
            'currency_conversions_total{from_currency="USD",status="success",to_currency="EUR"} 1.0'
            in content
        )
        assert (
            'currency_conversions_total{from_currency="EUR",status="success",to_currency="GBP"} 1.0'
            in content
        )

    def test_in_progress_requests_gauge_resets(self, client):
        """Test that in-progress requests gauge is properly managed."""
        # Make a request
        client.get("/")

        # Check metrics - in-progress should be 0 after request completes
        metrics_response = client.get("/metrics")
        content = metrics_response.text

        # Should show 0 in-progress requests
        assert "http_requests_in_progress 0.0" in content

    def test_duration_histogram_buckets_present(self, client):
        """Test that duration histogram includes proper buckets."""
        # Make a request
        client.get("/")

        # Check metrics
        metrics_response = client.get("/metrics")
        content = metrics_response.text

        # Should contain histogram buckets
        bucket_pattern = (
            r'http_request_duration_seconds_bucket\{endpoint="/",le="[^"]+",method="GET"\} \d+\.0'
        )
        assert re.search(bucket_pattern, content)

        # Should contain count and sum
        assert 'http_request_duration_seconds_count{endpoint="/",method="GET"} 1.0' in content
        assert re.search(
            r'http_request_duration_seconds_sum\{endpoint="/",method="GET"\} \d+\.\d+', content
        )

    def test_endpoint_normalization_in_metrics(self, client):
        """Test that endpoint paths are normalized in metrics."""
        # Make request to non-existent endpoint (will be normalized)
        client.get("/api/v1/nonexistent/12345")

        # Check metrics
        metrics_response = client.get("/metrics")
        content = metrics_response.text

        # Should normalize numeric ID
        assert 'endpoint="/api/v1/nonexistent/{id}"' in content

    def test_different_http_methods_tracked_separately(self, client):
        """Test that different HTTP methods are tracked separately."""
        # Make GET request
        client.get("/api/v1/rates")

        # Make POST request to same path (will fail but that's OK)
        client.post("/api/v1/rates", json={})

        # Check metrics
        metrics_response = client.get("/metrics")
        content = metrics_response.text

        # Should show separate entries for GET and POST
        assert 'http_requests_total{endpoint="/api/v1/rates",method="GET"' in content
        assert 'http_requests_total{endpoint="/api/v1/rates",method="POST"' in content

    def test_metrics_endpoint_excluded_from_tracking(self, client):
        """Test that the /metrics endpoint itself is not tracked."""
        # Make multiple requests to metrics endpoint
        client.get("/metrics")
        client.get("/metrics")
        client.get("/metrics")

        # Get final metrics
        metrics_response = client.get("/metrics")
        content = metrics_response.text

        # Should NOT contain any metrics for the /metrics endpoint itself
        assert 'endpoint="/metrics"' not in content

    def test_full_application_workflow_metrics(self, client):
        """Test metrics for a complete application workflow."""
        # Full workflow: check health, get rates, perform conversion
        health_response = client.get("/health")
        assert health_response.status_code == 200

        rates_response = client.get("/api/v1/rates")
        assert rates_response.status_code == 200

        conversion_response = client.post(
            "/api/v1/convert", json={"amount": 100.0, "from_currency": "USD", "to_currency": "EUR"}
        )
        assert conversion_response.status_code == 200

        history_response = client.get("/api/v1/rates/history?currency=EUR&limit=5")
        assert history_response.status_code == 200

        # Check final metrics
        metrics_response = client.get("/metrics")
        content = metrics_response.text

        # Should show all HTTP requests
        assert (
            'http_requests_total{endpoint="/health",method="GET",status_code="200"} 1.0' in content
        )
        assert (
            'http_requests_total{endpoint="/api/v1/rates",method="GET",status_code="200"} 1.0'
            in content
        )
        assert (
            'http_requests_total{endpoint="/api/v1/convert",method="POST",status_code="200"} 1.0'
            in content
        )
        assert (
            'http_requests_total{endpoint="/api/v1/rates/history",method="GET",status_code="200"} 1.0'
            in content
        )

        # Should show application-specific metrics
        assert 'rates_requests_total{endpoint="current_rates",status="success"} 1.0' in content
        assert 'rates_requests_total{endpoint="rates_history",status="success"} 1.0' in content
        assert (
            'currency_conversions_total{from_currency="USD",status="success",to_currency="EUR"} 1.0'
            in content
        )
