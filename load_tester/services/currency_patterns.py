"""Realistic currency patterns for load testing."""

import random
from decimal import Decimal
from typing import ClassVar

import uuid_utils.compat as uuid


class CurrencyPatterns:
    """Provides realistic currency conversion patterns for load testing."""

    # Major currency pairs with weights (higher = more common)
    CURRENCY_PAIR_WEIGHTS: ClassVar[dict[tuple[str, str], int]] = {
        # Major pairs (highest volume)
        ("USD", "EUR"): 25,
        ("USD", "GBP"): 20,
        ("EUR", "GBP"): 15,
        ("USD", "JPY"): 18,
        ("EUR", "USD"): 25,
        ("GBP", "USD"): 20,
        ("GBP", "EUR"): 15,
        ("JPY", "USD"): 18,
        # Cross pairs (medium volume)
        ("EUR", "JPY"): 8,
        ("GBP", "JPY"): 8,
        ("JPY", "EUR"): 8,
        ("JPY", "GBP"): 8,
        # Minor pairs (lower volume)
        ("USD", "CAD"): 6,
        ("USD", "AUD"): 5,
        ("USD", "CHF"): 4,
        ("CAD", "USD"): 6,
        ("AUD", "USD"): 5,
        ("CHF", "USD"): 4,
        ("EUR", "CAD"): 3,
        ("EUR", "AUD"): 3,
        ("EUR", "CHF"): 3,
        ("GBP", "CAD"): 2,
        ("GBP", "AUD"): 2,
        ("GBP", "CHF"): 2,
    }

    # Typical amounts by currency (realistic transaction sizes)
    CURRENCY_AMOUNTS: ClassVar[dict[str, list[Decimal]]] = {
        "USD": [
            Decimal("100.00"),
            Decimal("250.00"),
            Decimal("500.00"),
            Decimal("1000.00"),
            Decimal("2500.00"),
            Decimal("5000.00"),
            Decimal("10000.00"),
        ],
        "EUR": [
            Decimal("100.00"),
            Decimal("250.00"),
            Decimal("500.00"),
            Decimal("750.00"),
            Decimal("1000.00"),
            Decimal("2000.00"),
            Decimal("5000.00"),
        ],
        "GBP": [
            Decimal("75.00"),
            Decimal("150.00"),
            Decimal("300.00"),
            Decimal("500.00"),
            Decimal("1000.00"),
            Decimal("2500.00"),
            Decimal("5000.00"),
        ],
        "JPY": [
            Decimal("10000"),
            Decimal("25000"),
            Decimal("50000"),
            Decimal("100000"),
            Decimal("250000"),
            Decimal("500000"),
            Decimal("1000000"),
        ],
        "CAD": [
            Decimal("100.00"),
            Decimal("200.00"),
            Decimal("500.00"),
            Decimal("1000.00"),
            Decimal("2000.00"),
            Decimal("5000.00"),
        ],
        "AUD": [
            Decimal("100.00"),
            Decimal("200.00"),
            Decimal("500.00"),
            Decimal("1000.00"),
            Decimal("2000.00"),
            Decimal("5000.00"),
        ],
        "CHF": [
            Decimal("100.00"),
            Decimal("200.00"),
            Decimal("500.00"),
            Decimal("1000.00"),
            Decimal("2500.00"),
            Decimal("5000.00"),
        ],
    }

    def __init__(self) -> None:
        """Initialize currency patterns generator."""
        # Precompute weighted currency pairs list for efficient selection
        self._weighted_pairs: list[tuple[str, str]] = []
        for (from_curr, to_curr), weight in self.CURRENCY_PAIR_WEIGHTS.items():
            self._weighted_pairs.extend([(from_curr, to_curr)] * weight)

    def generate_random_request(self) -> dict[str, str | float]:
        """Generate a realistic currency conversion request.

        Returns:
            Dictionary with conversion request data
        """
        # Select random currency pair based on weights
        from_currency, to_currency = random.choice(self._weighted_pairs)

        # Select realistic amount for the source currency
        amounts = self.CURRENCY_AMOUNTS.get(from_currency, self.CURRENCY_AMOUNTS["USD"])
        amount = random.choice(amounts)

        return {
            "amount": float(amount),
            "from_currency": from_currency,
            "to_currency": to_currency,
            "request_id": str(uuid.uuid7()),
        }

    def get_currency_pair_distribution(self) -> dict[str, float]:
        """Get the distribution of currency pairs as percentages.

        Returns:
            Dictionary mapping currency pairs to their percentage frequency
        """
        total_weight = sum(self.CURRENCY_PAIR_WEIGHTS.values())
        return {
            f"{from_curr}_{to_curr}": (weight / total_weight) * 100
            for (from_curr, to_curr), weight in self.CURRENCY_PAIR_WEIGHTS.items()
        }

    def get_supported_currencies(self) -> list[str]:
        """Get list of all supported currencies.

        Returns:
            List of currency codes
        """
        currencies = set()
        for from_curr, to_curr in self.CURRENCY_PAIR_WEIGHTS:
            currencies.add(from_curr)
            currencies.add(to_curr)
        return sorted(currencies)

    def get_amount_ranges_by_currency(self) -> dict[str, dict[str, Decimal]]:
        """Get min/max amount ranges for each currency.

        Returns:
            Dictionary mapping currencies to their min/max amounts
        """
        return {
            currency: {
                "min": min(amounts),
                "max": max(amounts),
                "typical": amounts[len(amounts) // 2],  # Median value
            }
            for currency, amounts in self.CURRENCY_AMOUNTS.items()
        }
