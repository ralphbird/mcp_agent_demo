"""Unit tests for Load Test models."""

import pytest

from load_tester.models.load_test import LoadTestConfig, _get_all_amounts, _get_all_currency_pairs


class TestLoadTestConfig:
    """Test LoadTestConfig functionality."""

    def test_default_config_initialization(self):
        """Test LoadTestConfig initialization with defaults."""
        config = LoadTestConfig()

        # Should use default values
        assert config.requests_per_second == 1.0
        assert len(config.currency_pairs) > 0  # Should get all pairs from factory
        assert len(config.amounts) > 0  # Should get all amounts from factory

        # Default factories should return comprehensive lists
        assert isinstance(config.currency_pairs, list)
        assert isinstance(config.amounts, list)

        # All currency pairs should be valid format
        for pair in config.currency_pairs:
            assert isinstance(pair, str)
            assert "_" in pair
            parts = pair.split("_")
            assert len(parts) == 2
            assert len(parts[0]) == 3  # FROM currency
            assert len(parts[1]) == 3  # TO currency

        # All amounts should be positive floats
        for amount in config.amounts:
            assert isinstance(amount, float)
            assert amount > 0

    def test_custom_config_initialization(self):
        """Test LoadTestConfig initialization with custom values."""
        custom_pairs = ["USD_EUR", "GBP_JPY"]
        custom_amounts = [100.0, 500.0, 1000.0]
        custom_rps = 5.0

        config = LoadTestConfig(
            requests_per_second=custom_rps,
            currency_pairs=custom_pairs,
            amounts=custom_amounts,
        )

        assert config.requests_per_second == custom_rps
        assert config.currency_pairs == custom_pairs
        assert config.amounts == custom_amounts

    def test_create_full_config_default_rps(self):
        """Test create_full_config with default RPS."""
        config = LoadTestConfig.create_full_config()

        assert config.requests_per_second == 1.0
        assert len(config.currency_pairs) > 0
        assert len(config.amounts) > 0

        # Should use ALL available pairs and amounts
        expected_pairs = _get_all_currency_pairs()
        expected_amounts = _get_all_amounts()

        assert config.currency_pairs == expected_pairs
        assert config.amounts == expected_amounts

    def test_create_full_config_custom_rps(self):
        """Test create_full_config with custom RPS."""
        custom_rps = 10.0
        config = LoadTestConfig.create_full_config(requests_per_second=custom_rps)

        assert config.requests_per_second == custom_rps
        assert len(config.currency_pairs) > 0
        assert len(config.amounts) > 0

        # Should still use ALL available pairs and amounts
        expected_pairs = _get_all_currency_pairs()
        expected_amounts = _get_all_amounts()

        assert config.currency_pairs == expected_pairs
        assert config.amounts == expected_amounts

    def test_ensure_complete_config_with_populated_fields(self):
        """Test ensure_complete_config when fields are already populated."""
        original_pairs = ["USD_EUR", "GBP_JPY"]
        original_amounts = [100.0, 500.0]
        original_rps = 5.0

        config = LoadTestConfig(
            requests_per_second=original_rps,
            currency_pairs=original_pairs,
            amounts=original_amounts,
        )

        complete_config = config.ensure_complete_config()

        # Should return same values since they're already populated
        assert complete_config.requests_per_second == original_rps
        assert complete_config.currency_pairs == original_pairs
        assert complete_config.amounts == original_amounts

    def test_ensure_complete_config_with_empty_currency_pairs(self):
        """Test ensure_complete_config when currency_pairs is empty."""
        config = LoadTestConfig(
            requests_per_second=3.0,
            currency_pairs=[],  # Empty list
            amounts=[100.0, 500.0],
        )

        complete_config = config.ensure_complete_config()

        # Should populate currency_pairs with defaults but keep other fields
        assert complete_config.requests_per_second == 3.0
        assert len(complete_config.currency_pairs) > 0
        assert complete_config.currency_pairs == _get_all_currency_pairs()
        assert complete_config.amounts == [100.0, 500.0]

    def test_ensure_complete_config_with_empty_amounts(self):
        """Test ensure_complete_config when amounts is empty."""
        config = LoadTestConfig(
            requests_per_second=3.0,
            currency_pairs=["USD_EUR", "GBP_JPY"],
            amounts=[],  # Empty list
        )

        complete_config = config.ensure_complete_config()

        # Should populate amounts with defaults but keep other fields
        assert complete_config.requests_per_second == 3.0
        assert complete_config.currency_pairs == ["USD_EUR", "GBP_JPY"]
        assert len(complete_config.amounts) > 0
        assert complete_config.amounts == _get_all_amounts()

    def test_ensure_complete_config_with_both_empty(self):
        """Test ensure_complete_config when both currency_pairs and amounts are empty."""
        config = LoadTestConfig(
            requests_per_second=7.5,
            currency_pairs=[],  # Empty list
            amounts=[],  # Empty list
        )

        complete_config = config.ensure_complete_config()

        # Should populate both with defaults
        assert complete_config.requests_per_second == 7.5
        assert len(complete_config.currency_pairs) > 0
        assert complete_config.currency_pairs == _get_all_currency_pairs()
        assert len(complete_config.amounts) > 0
        assert complete_config.amounts == _get_all_amounts()

    def test_ensure_complete_config_immutability(self):
        """Test that ensure_complete_config doesn't modify the original config."""
        original_pairs = ["USD_EUR"]
        original_amounts = [100.0]

        config = LoadTestConfig(
            requests_per_second=2.0,
            currency_pairs=original_pairs,
            amounts=original_amounts,
        )

        complete_config = config.ensure_complete_config()

        # Original config should be unchanged
        assert config.currency_pairs == original_pairs
        assert config.amounts == original_amounts

        # Complete config should be the same (no changes needed)
        assert complete_config.currency_pairs == original_pairs
        assert complete_config.amounts == original_amounts

    def test_ensure_complete_config_creates_new_instance(self):
        """Test that ensure_complete_config creates a new instance."""
        config = LoadTestConfig(currency_pairs=[], amounts=[])
        complete_config = config.ensure_complete_config()

        # Should be different instances
        assert config is not complete_config

        # Original should still have empty lists
        assert config.currency_pairs == []
        assert config.amounts == []

        # Complete should have populated lists
        assert len(complete_config.currency_pairs) > 0
        assert len(complete_config.amounts) > 0

    def test_validate_requests_per_second_bounds(self):
        """Test that requests_per_second validation works."""
        # Valid values should work
        config = LoadTestConfig(requests_per_second=1.0)
        assert config.requests_per_second == 1.0

        config = LoadTestConfig(requests_per_second=1000.0)
        assert config.requests_per_second == 1000.0

        # Test boundary values
        config = LoadTestConfig(requests_per_second=0.1)
        assert config.requests_per_second == 0.1

        # Invalid values should raise ValidationError
        with pytest.raises(ValueError):
            LoadTestConfig(requests_per_second=0.0)  # Not greater than 0

        with pytest.raises(ValueError):
            LoadTestConfig(requests_per_second=-1.0)  # Negative

        with pytest.raises(ValueError):
            LoadTestConfig(requests_per_second=1001.0)  # Greater than 1000


class TestLoadTestHelperFunctions:
    """Test helper functions for load test configuration."""

    def test_get_all_currency_pairs(self):
        """Test _get_all_currency_pairs function."""
        pairs = _get_all_currency_pairs()

        assert isinstance(pairs, list)
        assert len(pairs) > 0

        # All should be valid currency pair strings
        for pair in pairs:
            assert isinstance(pair, str)
            assert "_" in pair
            from_currency, to_currency = pair.split("_")
            assert len(from_currency) == 3
            assert len(to_currency) == 3

        # Should be sorted
        assert pairs == sorted(pairs)

    def test_get_all_amounts(self):
        """Test _get_all_amounts function."""
        amounts = _get_all_amounts()

        assert isinstance(amounts, list)
        assert len(amounts) > 0

        # All should be positive floats
        for amount in amounts:
            assert isinstance(amount, float)
            assert amount > 0

        # Should be sorted and unique
        assert amounts == sorted(set(amounts))

    def test_helper_functions_consistency(self):
        """Test that helper functions return consistent results."""
        # Multiple calls should return identical results
        pairs1 = _get_all_currency_pairs()
        pairs2 = _get_all_currency_pairs()
        assert pairs1 == pairs2

        amounts1 = _get_all_amounts()
        amounts2 = _get_all_amounts()
        assert amounts1 == amounts2

    def test_helper_functions_comprehensive_coverage(self):
        """Test that helper functions provide comprehensive coverage."""
        pairs = _get_all_currency_pairs()
        amounts = _get_all_amounts()

        # Should have significant coverage
        assert len(pairs) >= 20  # Expect at least 20 currency pairs
        assert len(amounts) >= 15  # Expect at least 15 different amounts

        # Should include major currency pairs
        expected_pairs = ["USD_EUR", "EUR_USD", "USD_GBP", "GBP_USD", "USD_JPY", "JPY_USD"]
        for pair in expected_pairs:
            assert pair in pairs, f"Expected major pair {pair} not found"

        # Should include reasonable amount ranges
        assert any(100 <= amount <= 1000 for amount in amounts), "Should include mid-range amounts"
        assert any(amount >= 10000 for amount in amounts), "Should include large amounts"

    def test_error_injection_defaults(self):
        """Test LoadTestConfig error injection defaults."""
        config = LoadTestConfig()

        assert config.error_injection_enabled is False
        assert config.error_injection_rate == 0.05

    def test_error_injection_custom_values(self):
        """Test LoadTestConfig with custom error injection values."""
        config = LoadTestConfig(
            error_injection_enabled=True,
            error_injection_rate=0.15,
        )

        assert config.error_injection_enabled is True
        assert config.error_injection_rate == 0.15

    def test_error_injection_rate_validation(self):
        """Test error injection rate validation."""
        # Valid rates should work
        config = LoadTestConfig(error_injection_rate=0.0)
        assert config.error_injection_rate == 0.0

        config = LoadTestConfig(error_injection_rate=0.25)
        assert config.error_injection_rate == 0.25

        config = LoadTestConfig(error_injection_rate=0.5)
        assert config.error_injection_rate == 0.5

        # Invalid rates should raise ValidationError
        with pytest.raises(ValueError):
            LoadTestConfig(error_injection_rate=-0.1)  # Negative

        with pytest.raises(ValueError):
            LoadTestConfig(error_injection_rate=0.6)  # Greater than 0.5

    def test_create_full_config_with_error_injection(self):
        """Test create_full_config with error injection parameters."""
        config = LoadTestConfig.create_full_config(
            requests_per_second=10.0,
            error_injection_enabled=True,
            error_injection_rate=0.10,
        )

        assert config.requests_per_second == 10.0
        assert config.error_injection_enabled is True
        assert config.error_injection_rate == 0.10

        # Should still have full pairs and amounts
        assert len(config.currency_pairs) > 0
        assert len(config.amounts) > 0

    def test_create_full_config_error_injection_defaults(self):
        """Test create_full_config uses error injection defaults."""
        config = LoadTestConfig.create_full_config(requests_per_second=5.0)

        assert config.requests_per_second == 5.0
        assert config.error_injection_enabled is False
        assert config.error_injection_rate == 0.05

    def test_ensure_complete_config_preserves_error_injection(self):
        """Test ensure_complete_config preserves error injection settings."""
        original_config = LoadTestConfig(
            requests_per_second=3.0,
            currency_pairs=[],  # Empty, should be populated
            amounts=[],  # Empty, should be populated
            error_injection_enabled=True,
            error_injection_rate=0.20,
        )

        complete_config = original_config.ensure_complete_config()

        # Should populate empty fields but preserve error injection settings
        assert len(complete_config.currency_pairs) > 0
        assert len(complete_config.amounts) > 0
        assert complete_config.error_injection_enabled is True
        assert complete_config.error_injection_rate == 0.20
