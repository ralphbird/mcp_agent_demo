"""Currency conversion service with simulated exchange rates."""

from datetime import UTC, datetime
from decimal import ROUND_HALF_EVEN, Decimal

from currency_app.models.conversion import ConversionRequest, ConversionResponse


class InvalidCurrencyError(Exception):
    """Raised when an invalid currency code is provided."""

    pass


class CurrencyService:
    """Service for currency conversion with simulated exchange rates."""

    # Static exchange rates relative to USD (as of a simulated snapshot)
    EXCHANGE_RATES: dict[str, Decimal] = {
        "USD": Decimal("1.0000"),
        "EUR": Decimal("0.8523"),
        "GBP": Decimal("0.7891"),
        "JPY": Decimal("110.4500"),
        "AUD": Decimal("1.3456"),
        "CAD": Decimal("1.2567"),
        "CHF": Decimal("0.9234"),
        "CNY": Decimal("6.4521"),
        "SEK": Decimal("8.7654"),
        "NZD": Decimal("1.4321"),
    }

    SUPPORTED_CURRENCIES: set[str] = set(EXCHANGE_RATES.keys())

    def __init__(self):
        """Initialize the currency service."""
        self.rate_timestamp = datetime.now(UTC)

    def validate_currency(self, currency_code: str) -> str:
        """Validate and normalize currency code.

        Args:
            currency_code: Currency code to validate

        Returns:
            Normalized currency code

        Raises:
            InvalidCurrencyError: If currency is not supported
        """
        normalized_code = currency_code.upper()
        if normalized_code not in self.SUPPORTED_CURRENCIES:
            raise InvalidCurrencyError(
                f"Currency code '{currency_code}' is not supported. "
                f"Supported currencies: {sorted(self.SUPPORTED_CURRENCIES)}"
            )
        return normalized_code

    def get_exchange_rate(self, from_currency: str, to_currency: str) -> Decimal:
        """Get exchange rate between two currencies.

        Args:
            from_currency: Source currency code
            to_currency: Target currency code

        Returns:
            Exchange rate from source to target currency

        Raises:
            InvalidCurrencyError: If either currency is not supported
        """
        from_currency = self.validate_currency(from_currency)
        to_currency = self.validate_currency(to_currency)

        if from_currency == to_currency:
            return Decimal("1.0000")

        # Convert via USD (all rates are relative to USD)
        from_usd_rate = self.EXCHANGE_RATES[from_currency]
        to_usd_rate = self.EXCHANGE_RATES[to_currency]

        # Calculate cross rate: (1 / from_usd_rate) * to_usd_rate
        exchange_rate = to_usd_rate / from_usd_rate

        # Round to 6 decimal places for rate precision
        return exchange_rate.quantize(Decimal("0.000001"), rounding=ROUND_HALF_EVEN)

    def convert_currency(self, request: ConversionRequest) -> ConversionResponse:
        """Convert currency based on request.

        Args:
            request: Conversion request with amount and currencies

        Returns:
            Conversion response with results

        Raises:
            InvalidCurrencyError: If currencies are not supported
        """
        # Validate currencies
        from_currency = self.validate_currency(request.from_currency)
        to_currency = self.validate_currency(request.to_currency)

        # Get exchange rate
        exchange_rate = self.get_exchange_rate(from_currency, to_currency)

        # Calculate converted amount
        converted_amount = request.amount * exchange_rate

        # Round to 2 decimal places for currency amounts (banker's rounding)
        converted_amount = converted_amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)

        # Create response
        return ConversionResponse(
            request_id=request.request_id,
            amount=request.amount,
            from_currency=from_currency,
            to_currency=to_currency,
            converted_amount=converted_amount,
            exchange_rate=exchange_rate,
            rate_timestamp=self.rate_timestamp,
        )

    def get_supported_currencies(self) -> list[str]:
        """Get list of supported currency codes.

        Returns:
            Sorted list of supported currency codes
        """
        return sorted(self.SUPPORTED_CURRENCIES)
