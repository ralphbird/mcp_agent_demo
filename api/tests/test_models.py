"""Tests for Pydantic models."""

from datetime import UTC, datetime
from uuid import uuid4

from currency_app.models.conversion import ErrorResponse


class TestErrorResponse:
    """Test ErrorResponse model and its create method."""

    def test_error_response_create_minimal(self):
        """Test ErrorResponse.create() with minimal parameters."""
        error_response = ErrorResponse.create(code="TEST_ERROR", message="Test error message")

        assert error_response.error["code"] == "TEST_ERROR"
        assert error_response.error["message"] == "Test error message"
        assert "timestamp" in error_response.error
        assert isinstance(error_response.error["timestamp"], str)  # Now ISO string
        assert "details" not in error_response.error
        assert "request_id" not in error_response.error

    def test_error_response_create_with_details(self):
        """Test ErrorResponse.create() with details parameter."""
        details = {"field": "amount", "issue": "must be positive"}

        error_response = ErrorResponse.create(
            code="VALIDATION_ERROR", message="Validation failed", details=details
        )

        assert error_response.error["code"] == "VALIDATION_ERROR"
        assert error_response.error["message"] == "Validation failed"
        assert error_response.error["details"] == details
        assert "request_id" not in error_response.error

    def test_error_response_create_with_request_id(self):
        """Test ErrorResponse.create() with request_id parameter."""
        request_id = uuid4()

        error_response = ErrorResponse.create(
            code="SERVER_ERROR", message="Internal server error", request_id=request_id
        )

        assert error_response.error["code"] == "SERVER_ERROR"
        assert error_response.error["message"] == "Internal server error"
        assert error_response.error["request_id"] == str(request_id)
        assert "details" not in error_response.error

    def test_error_response_create_with_all_parameters(self):
        """Test ErrorResponse.create() with all optional parameters."""
        details = {"currency": "INVALID", "supported": "USD,EUR,GBP"}
        request_id = uuid4()

        error_response = ErrorResponse.create(
            code="INVALID_CURRENCY",
            message="Currency not supported",
            details=details,
            request_id=request_id,
        )

        assert error_response.error["code"] == "INVALID_CURRENCY"
        assert error_response.error["message"] == "Currency not supported"
        assert error_response.error["details"] == details
        assert error_response.error["request_id"] == str(request_id)
        assert "timestamp" in error_response.error
        assert isinstance(error_response.error["timestamp"], str)  # Now ISO string

    def test_error_response_create_with_none_details(self):
        """Test ErrorResponse.create() with explicit None details (should be omitted)."""
        error_response = ErrorResponse.create(
            code="TEST_ERROR", message="Test message", details=None
        )

        assert "details" not in error_response.error
        assert error_response.error["code"] == "TEST_ERROR"
        assert error_response.error["message"] == "Test message"

    def test_error_response_create_with_none_request_id(self):
        """Test ErrorResponse.create() with explicit None request_id (should be omitted)."""
        error_response = ErrorResponse.create(
            code="TEST_ERROR", message="Test message", request_id=None
        )

        assert "request_id" not in error_response.error
        assert error_response.error["code"] == "TEST_ERROR"
        assert error_response.error["message"] == "Test message"

    def test_error_response_create_timestamp_accuracy(self):
        """Test that timestamp is recent and properly formatted."""
        before = datetime.now(UTC)
        error_response = ErrorResponse.create(code="TEST", message="Test")
        after = datetime.now(UTC)

        timestamp_value = error_response.error["timestamp"]
        # Parse the ISO timestamp back to datetime for comparison
        if isinstance(timestamp_value, str):
            timestamp = datetime.fromisoformat(timestamp_value.replace("Z", "+00:00"))
            assert before <= timestamp <= after
