"""Pydantic models for currency conversion."""

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


class ConversionRequest(BaseModel):
    """Request model for currency conversion."""

    amount: Decimal = Field(..., gt=0, description="Amount to convert")
    from_currency: str = Field(..., min_length=3, max_length=3, description="Source currency code")
    to_currency: str = Field(..., min_length=3, max_length=3, description="Target currency code")
    request_id: UUID = Field(
        default_factory=uuid4, description="Request ID (auto-generated if not provided)"
    )

    @field_validator("from_currency", "to_currency")
    @classmethod
    def validate_currency_code(cls, v):
        """Validate currency codes are uppercase."""
        return v.upper()


class ConversionResponse(BaseModel):
    """Response model for currency conversion."""

    conversion_id: UUID = Field(default_factory=uuid4, description="Unique conversion ID")
    request_id: UUID = Field(..., description="Request ID from input")
    amount: Decimal = Field(..., description="Original amount")
    from_currency: str = Field(..., description="Source currency code")
    to_currency: str = Field(..., description="Target currency code")
    converted_amount: Decimal = Field(..., description="Converted amount")
    exchange_rate: Decimal = Field(..., description="Exchange rate used")
    rate_timestamp: datetime = Field(..., description="When the rate was last updated")
    conversion_timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="When conversion was performed",
    )
    metadata: dict[str, str] = Field(
        default_factory=lambda: {
            "rate_source": "simulated",
            "calculation_method": "direct",
            "precision": "4",
        },
        description="Additional metadata about the conversion",
    )


class ErrorResponse(BaseModel):
    """Error response model."""

    error: dict[str, str | dict[str, str]] = Field(..., description="Error details")

    @classmethod
    def create(
        cls,
        code: str,
        message: str,
        details: dict[str, str] | None = None,
        request_id: UUID | None = None,
    ) -> "ErrorResponse":
        """Create an error response."""
        error_data: dict[str, str | dict[str, str]] = {
            "code": code,
            "message": message,
            "timestamp": datetime.now(UTC).isoformat(),
        }
        if details:
            error_data["details"] = details
        if request_id:
            error_data["request_id"] = str(request_id)

        return cls(error=error_data)


class RateInfo(BaseModel):
    """Individual exchange rate information."""

    currency: str = Field(..., description="Currency code")
    rate: Decimal = Field(..., description="Exchange rate relative to USD")
    last_updated: datetime = Field(..., description="When this rate was last updated")


class RatesResponse(BaseModel):
    """Response model for current exchange rates."""

    base_currency: str = Field(default="USD", description="Base currency for all rates")
    rates: list[RateInfo] = Field(..., description="List of exchange rates")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="When rates were retrieved",
    )
    metadata: dict[str, str] = Field(
        default_factory=lambda: {
            "rate_source": "simulated",
            "total_currencies": "10",
        },
        description="Additional metadata about the rates",
    )
