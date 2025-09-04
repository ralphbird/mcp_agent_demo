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

    def get_all_currency_pairs_with_amounts(self) -> dict[str, list[float]]:
        """Get all currency pairs with appropriate amounts based on from currency.

        Returns:
            Dictionary mapping currency pair strings to lists of amounts.
            Each pair uses amounts appropriate for its from currency.

        Example:
            {
                "USD_EUR": [100.0, 250.0, 500.0, 1000.0, 2500.0, 5000.0, 10000.0],
                "JPY_USD": [10000.0, 25000.0, 50000.0, 100000.0, 250000.0, 500000.0, 1000000.0],
                "EUR_GBP": [100.0, 250.0, 500.0, 750.0, 1000.0, 2000.0, 5000.0]
            }
        """
        pairs_with_amounts = {}

        for from_curr, to_curr in self.CURRENCY_PAIR_WEIGHTS:
            pair_str = f"{from_curr}_{to_curr}"

            # Use amounts from the from_currency, fallback to USD if not found
            if from_curr in self.CURRENCY_AMOUNTS:
                amounts = [float(amount) for amount in self.CURRENCY_AMOUNTS[from_curr]]
            else:
                amounts = [float(amount) for amount in self.CURRENCY_AMOUNTS["USD"]]

            pairs_with_amounts[pair_str] = amounts

        return pairs_with_amounts

    def get_all_currency_pairs_list(self) -> list[str]:
        """Get list of all currency pairs as strings.

        Returns:
            List of currency pair strings like ["USD_EUR", "EUR_USD", ...]
        """
        return sorted(self.get_all_currency_pairs_with_amounts().keys())

    def get_all_amounts_for_pairs(self, currency_pairs: list[str]) -> list[float]:
        """Get all unique amounts needed for the given currency pairs.

        Args:
            currency_pairs: List of currency pair strings

        Returns:
            Sorted list of all unique amounts across the pairs
        """
        pairs_with_amounts = self.get_all_currency_pairs_with_amounts()
        all_amounts = set()

        for pair in currency_pairs:
            if pair in pairs_with_amounts:
                all_amounts.update(pairs_with_amounts[pair])

        return sorted(all_amounts)

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

    def generate_invalid_request(self) -> dict[str, str | float]:
        """Generate an intentionally invalid currency conversion request for error injection.

        Returns:
            Dictionary with invalid conversion request data that should cause API errors
        """
        # Define different types of errors to inject
        error_types = [
            "unsupported_currency",
            "invalid_amount_negative",
            "invalid_amount_zero",
            "invalid_amount_too_large",
            "invalid_currency_format",
            "invalid_currency_length",
        ]

        error_type = random.choice(error_types)

        if error_type == "unsupported_currency":
            # Use invalid currency codes
            invalid_currencies = ["XXX", "ZZZ", "ABC", "DEF", "QQQ", "WWW"]

            # Randomly decide if from_currency or to_currency (or both) should be invalid
            if random.random() < 0.5:
                # Invalid from_currency
                from_currency = random.choice(invalid_currencies)
                to_currency = random.choice(list(self.CURRENCY_AMOUNTS.keys()))
            else:
                # Invalid to_currency
                from_currency = random.choice(list(self.CURRENCY_AMOUNTS.keys()))
                to_currency = random.choice(invalid_currencies)

            # Use valid amount
            amounts = (
                self.CURRENCY_AMOUNTS[from_currency]
                if from_currency in self.CURRENCY_AMOUNTS
                else self.CURRENCY_AMOUNTS["USD"]
            )
            amount = float(random.choice(amounts))

        elif error_type == "invalid_amount_negative":
            # Use valid currencies but negative amount
            from_currency, to_currency = random.choice(self._weighted_pairs)
            amount = -random.uniform(10, 1000)

        elif error_type == "invalid_amount_zero":
            # Use valid currencies but zero amount
            from_currency, to_currency = random.choice(self._weighted_pairs)
            amount = 0.0

        elif error_type == "invalid_amount_too_large":
            # Use valid currencies but unrealistically large amount
            from_currency, to_currency = random.choice(self._weighted_pairs)
            amount = random.uniform(1e15, 1e18)  # Extremely large numbers

        elif error_type == "invalid_currency_format":
            # Use invalid currency code formats
            invalid_formats = ["usd", "EUR€", "US$", "gbp", "JPY¥", "cad"]
            from_currency = random.choice(invalid_formats)
            to_currency = random.choice(list(self.CURRENCY_AMOUNTS.keys()))

            amounts = self.CURRENCY_AMOUNTS["USD"]  # Default to USD amounts
            amount = float(random.choice(amounts))

        elif error_type == "invalid_currency_length":
            # Use wrong length currency codes
            invalid_lengths = ["US", "USDD", "E", "EURO", "GB", "JPYY"]
            from_currency = random.choice(invalid_lengths)
            to_currency = random.choice(list(self.CURRENCY_AMOUNTS.keys()))

            amounts = self.CURRENCY_AMOUNTS["USD"]  # Default to USD amounts
            amount = float(random.choice(amounts))

        else:
            # Fallback to unsupported currency
            from_currency = "XXX"
            to_currency = "USD"
            amount = 100.0

        return {
            "amount": amount,
            "from_currency": from_currency,
            "to_currency": to_currency,
            "request_id": str(uuid.uuid7()),
            "_error_type": error_type,  # Internal field to track error type for debugging
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
