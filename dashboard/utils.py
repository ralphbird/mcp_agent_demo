"""Utility functions for the currency conversion dashboard."""

import os

import requests

# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
LOAD_TESTER_URL = os.getenv("LOAD_TESTER_URL", "http://localhost:8001")


def check_api_health():
    """Check if the API is healthy."""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException:
        return None


def check_load_tester_health():
    """Check if load tester service is healthy."""
    try:
        response = requests.get(f"{LOAD_TESTER_URL}/", timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException:
        return None


def get_current_rates():
    """Get current exchange rates."""
    try:
        response = requests.get(f"{API_BASE_URL}/api/v1/rates", timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException:
        return None


def convert_currency(amount: float, from_currency: str, to_currency: str):
    """Convert currency using the API."""
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/v1/convert",
            json={
                "amount": amount,
                "from_currency": from_currency,
                "to_currency": to_currency,
            },
            timeout=10,
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException:
        return None


def get_rates_history(currency: str | None = None, days: int = 30):
    """Get historical exchange rates."""
    try:
        params = {"days": str(days)}
        if currency:
            params["currency"] = currency

        response = requests.get(f"{API_BASE_URL}/api/v1/rates/history", params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException:
        return None


def convert_rates_to_base(history_data, base_currency):
    """Convert historical rates to a different base currency."""
    if not history_data or not history_data.get("rates"):
        return history_data

    # Group rates by date
    rates_by_date = {}
    for rate in history_data["rates"]:
        date = rate["recorded_at"][:10]  # Extract date part
        if date not in rates_by_date:
            rates_by_date[date] = {}
        rates_by_date[date][rate["currency"]] = float(rate["rate"])

    # Convert to new base
    converted_rates = []
    for date, currencies in rates_by_date.items():
        if base_currency not in currencies:
            continue  # Skip dates where base currency is not available

        base_rate = currencies[base_currency]
        for currency, rate in currencies.items():
            if currency != base_currency:
                # Convert: new_rate = old_rate / base_rate
                new_rate = rate / base_rate
                converted_rates.append(
                    {
                        "currency": currency,
                        "rate": new_rate,
                        "recorded_at": f"{date}T12:00:00Z",
                    }
                )

    return {"rates": converted_rates}


# Load testing utility functions
def get_load_test_status():
    """Get the current status of the load test."""
    try:
        response = requests.get(f"{LOAD_TESTER_URL}/api/load-test/status", timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException:
        return None


def get_load_test_scenarios():
    """Get available load test scenarios."""
    try:
        response = requests.get(f"{LOAD_TESTER_URL}/api/load-test/scenarios", timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException:
        return {}


def get_scenario_details(scenario: str):
    """Get details for a specific scenario."""
    try:
        response = requests.get(f"{LOAD_TESTER_URL}/api/load-test/scenarios/{scenario}", timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException:
        return None


def start_load_test_scenario(scenario: str):
    """Start a load test using a predefined scenario."""
    try:
        response = requests.post(
            f"{LOAD_TESTER_URL}/api/load-test/scenarios/{scenario}/start", timeout=30
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException:
        return None


def start_custom_load_test(config: dict):
    """Start a custom load test."""
    try:
        response = requests.post(
            f"{LOAD_TESTER_URL}/api/load-test/start",
            json={"config": config},
            timeout=30,
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException:
        return None


def stop_load_test():
    """Stop the current load test."""
    try:
        response = requests.post(f"{LOAD_TESTER_URL}/api/load-test/stop", timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException:
        return None


def get_load_test_report():
    """Get comprehensive load test report."""
    try:
        response = requests.get(f"{LOAD_TESTER_URL}/api/load-test/report", timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException:
        return None
