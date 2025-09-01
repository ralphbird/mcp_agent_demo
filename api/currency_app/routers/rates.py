"""API routes for exchange rates."""

from fastapi import APIRouter, HTTPException

from currency_app.models.conversion import ErrorResponse, RatesResponse
from currency_app.services.currency_service import CurrencyService

router = APIRouter(prefix="/api/v1", tags=["rates"])


@router.get("/rates", response_model=RatesResponse)
async def get_current_rates() -> RatesResponse:
    """Get current exchange rates for all supported currencies.

    Returns:
        Current exchange rates relative to USD

    Raises:
        HTTPException: If rates cannot be retrieved
    """
    try:
        # Initialize currency service
        currency_service = CurrencyService()

        # Get current rates
        return currency_service.get_current_rates()

    except Exception as e:
        error_response = ErrorResponse.create(
            code="RATES_ERROR",
            message="An unexpected error occurred while retrieving rates",
            details={"error": str(e)},
        )
        raise HTTPException(status_code=500, detail=error_response.error)
