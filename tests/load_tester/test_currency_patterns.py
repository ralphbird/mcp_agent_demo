"""Unit tests for CurrencyPatterns service."""

from decimal import Decimal

import pytest

from load_tester.services.currency_patterns import CurrencyPatterns


class TestCurrencyPatterns:
    """Test CurrencyPatterns functionality."""

    @pytest.fixture
    def patterns(self):
        """Create currency patterns instance."""
        return CurrencyPatterns()

    def test_initialization(self, patterns):
        """Test patterns initialization."""
        assert patterns is not None
        assert len(patterns._weighted_pairs) > 0

        # Verify weighted pairs are populated correctly
        total_pairs = sum(patterns.CURRENCY_PAIR_WEIGHTS.values())
        assert len(patterns._weighted_pairs) == total_pairs

    def test_generate_random_request(self, patterns):
        """Test generating random currency conversion requests."""
        request = patterns.generate_random_request()

        # Check required fields are present
        assert "amount" in request
        assert "from_currency" in request
        assert "to_currency" in request
        assert "request_id" in request

        # Check field types
        assert isinstance(request["amount"], float)
        assert isinstance(request["from_currency"], str)
        assert isinstance(request["to_currency"], str)
        assert isinstance(request["request_id"], str)

        # Check currency codes are valid (3 characters)
        assert len(request["from_currency"]) == 3
        assert len(request["to_currency"]) == 3

        # Check amount is positive
        assert request["amount"] > 0

        # Check currencies are different (should be since we have different pairs)
        # Note: This might not always be true for all pairs, but let's check it's a known pair
        pair = (request["from_currency"], request["to_currency"])
        assert pair in patterns.CURRENCY_PAIR_WEIGHTS

    def test_generate_multiple_requests_variety(self, patterns):
        """Test that generating multiple requests produces variety."""
        requests = [patterns.generate_random_request() for _ in range(50)]

        # Check we get variety in currency pairs
        pairs = {(r["from_currency"], r["to_currency"]) for r in requests}
        assert len(pairs) > 1  # Should get more than one pair in 50 requests

        # Check we get variety in amounts
        amounts = {r["amount"] for r in requests}
        assert len(amounts) > 1  # Should get more than one amount in 50 requests

        # All pairs should be valid
        for pair in pairs:
            assert pair in patterns.CURRENCY_PAIR_WEIGHTS

    def test_get_currency_pair_distribution(self, patterns):
        """Test getting currency pair distribution."""
        distribution = patterns.get_currency_pair_distribution()

        # Check all pairs are present
        expected_pairs = {f"{fc}_{tc}" for fc, tc in patterns.CURRENCY_PAIR_WEIGHTS}
        actual_pairs = set(distribution.keys())
        assert actual_pairs == expected_pairs

        # Check percentages sum to 100 (approximately)
        total_percentage = sum(distribution.values())
        assert abs(total_percentage - 100.0) < 0.01

        # Check all percentages are positive
        for percentage in distribution.values():
            assert percentage > 0

    def test_get_supported_currencies(self, patterns):
        """Test getting list of supported currencies."""
        currencies = patterns.get_supported_currencies()

        # Should be a non-empty list
        assert isinstance(currencies, list)
        assert len(currencies) > 0

        # Should be sorted
        assert currencies == sorted(currencies)

        # Should contain expected major currencies
        expected_currencies = {"USD", "EUR", "GBP", "JPY", "CAD", "AUD", "CHF"}
        assert expected_currencies.issubset(set(currencies))

        # All currencies should be 3 characters
        for currency in currencies:
            assert len(currency) == 3

    def test_get_amount_ranges_by_currency(self, patterns):
        """Test getting amount ranges by currency."""
        ranges = patterns.get_amount_ranges_by_currency()

        # Should have ranges for all currencies in the amounts dict
        expected_currencies = set(patterns.CURRENCY_AMOUNTS.keys())
        actual_currencies = set(ranges.keys())
        assert actual_currencies == expected_currencies

        # Each range should have min, max, and typical values
        for _currency, range_data in ranges.items():
            assert "min" in range_data
            assert "max" in range_data
            assert "typical" in range_data

            # Check types
            assert isinstance(range_data["min"], Decimal)
            assert isinstance(range_data["max"], Decimal)
            assert isinstance(range_data["typical"], Decimal)

            # Check logical ordering
            assert range_data["min"] <= range_data["typical"] <= range_data["max"]

            # Check values are positive
            assert range_data["min"] > 0
            assert range_data["max"] > 0
            assert range_data["typical"] > 0

    def test_currency_pair_weights_structure(self, patterns):
        """Test the structure of currency pair weights."""
        weights = patterns.CURRENCY_PAIR_WEIGHTS

        # Should be non-empty
        assert len(weights) > 0

        # Each key should be a tuple of two strings
        for (from_curr, to_curr), weight in weights.items():
            assert isinstance(from_curr, str)
            assert isinstance(to_curr, str)
            assert len(from_curr) == 3
            assert len(to_curr) == 3
            assert from_curr != to_curr  # Different currencies
            assert isinstance(weight, int)
            assert weight > 0

    def test_currency_amounts_structure(self, patterns):
        """Test the structure of currency amounts."""
        amounts = patterns.CURRENCY_AMOUNTS

        # Should be non-empty
        assert len(amounts) > 0

        # Each currency should have a list of positive decimal amounts
        for currency, amount_list in amounts.items():
            assert isinstance(currency, str)
            assert len(currency) == 3
            assert isinstance(amount_list, list)
            assert len(amount_list) > 0

            # All amounts should be positive Decimals
            for amount in amount_list:
                assert isinstance(amount, Decimal)
                assert amount > 0

            # List should be sorted (typically ascending)
            sorted_amounts = sorted(amount_list)
            assert amount_list == sorted_amounts

    def test_weighted_pair_distribution(self, patterns):
        """Test that weighted pair distribution matches expectations."""
        # Generate many requests and check distribution approximates weights
        requests = [patterns.generate_random_request() for _ in range(1000)]
        pair_counts = {}

        for request in requests:
            pair = (request["from_currency"], request["to_currency"])
            pair_counts[pair] = pair_counts.get(pair, 0) + 1

        # Check that higher weighted pairs appear more frequently
        total_weight = sum(patterns.CURRENCY_PAIR_WEIGHTS.values())

        for pair, count in pair_counts.items():
            expected_ratio = patterns.CURRENCY_PAIR_WEIGHTS[pair] / total_weight
            actual_ratio = count / 1000

            # Allow for significant variance due to randomness (within 100% of expected)
            # This is a statistical test and can have natural variation
            tolerance = max(expected_ratio * 1.0, 0.015)  # At least 1.5% tolerance
            assert abs(actual_ratio - expected_ratio) < tolerance

    def test_get_all_currency_pairs_with_amounts(self, patterns):
        """Test getting all currency pairs with their appropriate amounts."""
        pairs_with_amounts = patterns.get_all_currency_pairs_with_amounts()

        # Should be a dictionary
        assert isinstance(pairs_with_amounts, dict)
        assert len(pairs_with_amounts) > 0

        # Keys should be currency pair strings (FROM_TO format)
        for pair_str, amounts in pairs_with_amounts.items():
            assert isinstance(pair_str, str)
            assert "_" in pair_str
            from_currency, to_currency = pair_str.split("_")
            assert len(from_currency) == 3
            assert len(to_currency) == 3

            # Verify the pair exists in CURRENCY_PAIR_WEIGHTS
            assert (from_currency, to_currency) in patterns.CURRENCY_PAIR_WEIGHTS

            # Values should be lists of amounts appropriate for the from_currency
            assert isinstance(amounts, list)
            assert len(amounts) > 0

            # All amounts should be positive floats
            for amount in amounts:
                assert isinstance(amount, float)
                assert amount > 0

            # Amounts should match those defined for the from_currency
            expected_amounts = [float(amt) for amt in patterns.CURRENCY_AMOUNTS[from_currency]]
            assert amounts == expected_amounts

    def test_get_all_currency_pairs_list(self, patterns):
        """Test getting list of all currency pairs."""
        pairs_list = patterns.get_all_currency_pairs_list()

        # Should be a list
        assert isinstance(pairs_list, list)
        assert len(pairs_list) > 0

        # Each item should be a currency pair string
        for pair_str in pairs_list:
            assert isinstance(pair_str, str)
            assert "_" in pair_str
            from_currency, to_currency = pair_str.split("_")
            assert len(from_currency) == 3
            assert len(to_currency) == 3

            # Verify the pair exists in CURRENCY_PAIR_WEIGHTS
            assert (from_currency, to_currency) in patterns.CURRENCY_PAIR_WEIGHTS

        # Should contain all pairs from CURRENCY_PAIR_WEIGHTS
        expected_pairs = {f"{fc}_{tc}" for fc, tc in patterns.CURRENCY_PAIR_WEIGHTS}
        assert set(pairs_list) == expected_pairs

        # List should be sorted
        assert pairs_list == sorted(pairs_list)

    def test_get_all_amounts_for_pairs(self, patterns):
        """Test getting all amounts for specified currency pairs."""
        # Test with a subset of pairs
        test_pairs = ["USD_EUR", "EUR_USD", "JPY_USD", "USD_JPY"]
        amounts_list = patterns.get_all_amounts_for_pairs(test_pairs)

        # Should be a list of unique amounts
        assert isinstance(amounts_list, list)
        assert len(amounts_list) > 0

        # All amounts should be positive floats
        for amount in amounts_list:
            assert isinstance(amount, float)
            assert amount > 0

        # Should contain amounts from all from-currencies in the pairs
        expected_amounts = set()
        for pair_str in test_pairs:
            from_currency = pair_str.split("_")[0]
            if from_currency in patterns.CURRENCY_AMOUNTS:
                expected_amounts.update(
                    float(amt) for amt in patterns.CURRENCY_AMOUNTS[from_currency]
                )

        assert set(amounts_list) == expected_amounts

        # List should be sorted
        assert amounts_list == sorted(amounts_list)

    def test_get_all_amounts_for_pairs_all_pairs(self, patterns):
        """Test getting all amounts for all currency pairs."""
        all_pairs = patterns.get_all_currency_pairs_list()
        amounts_list = patterns.get_all_amounts_for_pairs(all_pairs)

        # Should be a comprehensive list
        assert isinstance(amounts_list, list)
        assert len(amounts_list) > 0

        # Should contain amounts from all currencies that appear as from_currency
        from_currencies = {pair.split("_")[0] for pair in all_pairs}
        expected_amounts = set()
        for from_currency in from_currencies:
            if from_currency in patterns.CURRENCY_AMOUNTS:
                expected_amounts.update(
                    float(amt) for amt in patterns.CURRENCY_AMOUNTS[from_currency]
                )

        assert set(amounts_list) == expected_amounts

        # List should be sorted and unique
        assert amounts_list == sorted(set(amounts_list))

    def test_get_all_amounts_for_pairs_empty_list(self, patterns):
        """Test getting amounts for empty pairs list."""
        amounts_list = patterns.get_all_amounts_for_pairs([])

        # Should return empty list for empty input
        assert amounts_list == []

    def test_get_all_amounts_for_pairs_invalid_pairs(self, patterns):
        """Test getting amounts for invalid currency pairs."""
        # Test with pairs that don't exist
        invalid_pairs = ["XXX_YYY", "ZZZ_AAA"]
        amounts_list = patterns.get_all_amounts_for_pairs(invalid_pairs)

        # Should return empty list since no valid from_currencies
        assert amounts_list == []
