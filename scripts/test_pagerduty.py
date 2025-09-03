#!/usr/bin/env python3
"""Test PagerDuty integration for Currency API monitoring.

This script sends a test alert to PagerDuty to verify the integration is working.
"""

import os
import sys
from datetime import datetime

try:
    import requests
except ImportError:
    print("❌ ERROR: 'requests' library not found")
    print("Install with: poetry add requests")
    print("Or run with: poetry run python scripts/test_pagerduty.py")
    print(
        "Or use the Docker environment: docker-compose exec api python /app/scripts/test_pagerduty.py"
    )
    sys.exit(1)


def send_pagerduty_event(
    integration_key: str,
    event_action: str = "trigger",
    severity: str = "info",
    summary: str = "Test alert",
    source: str = "currency-api-test",
    component: str = "currency-api",
    group: str = "test",
    custom_details: dict | None = None,
) -> dict:
    """Send an event to PagerDuty Events API v2.

    Args:
        integration_key: PagerDuty integration key
        event_action: 'trigger', 'acknowledge', or 'resolve'
        severity: 'critical', 'error', 'warning', or 'info'
        summary: Brief text summary of the event
        source: Unique location of the affected system
        component: Component of the source which is responsible for the event
        group: Logical grouping of components
        custom_details: Additional details for the event

    Returns:
        Response from PagerDuty API
    """
    url = "https://events.pagerduty.com/v2/enqueue"

    payload = {
        "routing_key": integration_key,
        "event_action": event_action,
        "payload": {
            "summary": summary,
            "source": source,
            "severity": severity,
            "component": component,
            "group": group,
            "class": "currency-api-monitoring",
            "custom_details": custom_details or {},
        },
    }

    if event_action == "trigger":
        # Add a dedup_key for resolve/acknowledge actions
        payload["dedup_key"] = f"currency-api-test-{datetime.now().isoformat()}"

    headers = {
        "Content-Type": "application/json",
    }

    response = requests.post(url, json=payload, headers=headers, timeout=10)
    return response.json()


def test_integration():
    """Test PagerDuty integration with Currency API."""
    print("🧪 Testing PagerDuty Integration for Currency API")
    print("=" * 50)

    # Get integration key from environment
    integration_key = os.getenv("PAGERDUTY_CURRENCY_APP_KEY")

    if not integration_key or integration_key == "your-pagerduty-integration-key-here":
        print("❌ ERROR: PAGERDUTY_CURRENCY_APP_KEY not set or using default value")
        print("\nTo fix this:")
        print("1. Copy .env.example to .env")
        print("2. Set your actual PagerDuty integration key in .env")
        print("3. Restart the Docker containers")
        print("4. Run this test again")
        return False

    print(f"✓ Found integration key: {integration_key[:8]}...")

    # Test 1: Send a test trigger event
    print("\n📤 Sending test trigger event...")

    try:
        response = send_pagerduty_event(
            integration_key=integration_key,
            event_action="trigger",
            severity="warning",
            summary="Currency API Test Alert - Please acknowledge and resolve",
            source="currency-api-test-script",
            component="currency-api",
            group="currency-conversion-system",
            custom_details={
                "test_type": "integration_verification",
                "timestamp": datetime.now().isoformat(),
                "dashboard_url": "http://localhost:3000",
                "api_url": "http://localhost:8000",
                "instructions": "This is a test alert. Please acknowledge and resolve in PagerDuty.",
            },
        )

        if response.get("status") == "success":
            dedup_key = response.get("dedup_key")
            print("✅ Test alert sent successfully!")
            print(f"   Dedup Key: {dedup_key}")
            print(f"   Message: {response.get('message', 'No message')}")

            print("\n📋 Next steps:")
            print("1. Check your PagerDuty dashboard for the new incident")
            print("2. Verify the incident contains the expected details")
            print("3. Acknowledge the incident in PagerDuty")
            print("4. Optionally, resolve the incident")

            return True
        print(f"❌ Failed to send alert: {response}")
        return False

    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def main():
    """Main function."""
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print("Usage: python test_pagerduty.py")
        print("\nThis script tests the PagerDuty integration by sending a test alert.")
        print("Make sure to set PAGERDUTY_CURRENCY_APP_KEY in your .env file first.")
        return

    success = test_integration()

    if success:
        print("\n✅ PagerDuty integration test completed successfully!")
        print("Check your PagerDuty dashboard to verify the alert was received.")
    else:
        print("\n❌ PagerDuty integration test failed!")
        print("Please check your configuration and try again.")
        sys.exit(1)


if __name__ == "__main__":
    main()
