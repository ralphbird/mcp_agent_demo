"""Load testing control page for the dashboard."""

from typing import Any

import requests
import streamlit as st

from dashboard.utils import LOAD_TESTER_URL


def show_attack_simulation_page():
    """Display the load testing control page."""
    st.header("🔥 Load Testing Control")
    st.markdown(
        """
        This page allows you to run various load testing scenarios against the external Currency API
        for performance testing and validation.

        **⚠️ Note**: This will generate load against the external API. Ensure the API is ready to handle test traffic.
        """
    )

    # Create two columns for different test types
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("👥 Baseline Load Test")
        st.markdown("Simulate steady user traffic")

        baseline_rps = st.slider(
            "Requests per Second", min_value=1, max_value=50, value=10, help="Steady request rate"
        )

        duration = st.number_input(
            "Duration (seconds)",
            min_value=10,
            max_value=600,
            value=60,
            help="How long to run the test",
        )

        if st.button("🟢 Start Baseline Test", key="start_baseline"):
            start_load_test("baseline", baseline_rps, duration)

    with col2:
        st.subheader("⚡ Burst Load Test")
        st.markdown("Test with burst traffic patterns")

        burst_rps = st.slider(
            "Peak RPS",
            min_value=10,
            max_value=200,
            value=50,
            help="Peak request rate during bursts",
        )

        burst_duration = st.number_input(
            "Burst Duration (seconds)",
            min_value=5,
            max_value=120,
            value=30,
            help="Duration of each burst",
        )

        if st.button("⚡ Start Burst Test", key="start_burst"):
            start_load_test("burst", burst_rps, burst_duration)

    # Control buttons
    st.subheader("🎛️ Test Controls")
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🔴 Stop All Tests", key="stop_all"):
            stop_all_tests()

    with col2:
        if st.button("🔄 Refresh Status", key="refresh"):
            st.rerun()

    with col3:
        if st.button("📊 Get Report", key="get_report"):
            show_test_report()

    # Status display
    st.subheader("📊 Current Test Status")

    # Get status of load tests
    status_data = get_load_test_status()

    if status_data:
        display_status_table(status_data)
    else:
        st.info("No active load tests")

    # Performance metrics
    st.subheader("📈 Performance Summary")

    if status_data and status_data.get("stats"):
        stats = status_data["stats"]
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Requests", stats.get("total_requests", 0))

        with col2:
            st.metric("Success Rate", f"{stats.get('success_rate', 0):.1%}")

        with col3:
            st.metric("Avg Response (ms)", f"{stats.get('avg_response_time_ms', 0):.1f}")

        with col4:
            st.metric("Current RPS", f"{stats.get('requests_per_second', 0):.1f}")


def start_load_test(test_type: str, rps: float, duration: int) -> None:
    """Start a load test with the specified parameters."""
    try:
        config = {
            "requests_per_second": rps,
            "duration_seconds": duration,
            "currency_pairs": [["USD", "EUR"], ["GBP", "USD"], ["JPY", "EUR"]],
            "amounts": [100, 500, 1000],
            "error_injection_enabled": test_type == "burst",
            "error_injection_rate": 0.05 if test_type == "burst" else 0.01,
        }

        response = requests.post(f"{LOAD_TESTER_URL}/api/load-test/start", json=config, timeout=10)

        if response.status_code == 200:
            st.success(f"✅ {test_type.title()} load test started successfully!")
        else:
            st.error(f"❌ Failed to start load test: {response.text}")

    except Exception as e:
        st.error(f"❌ Error starting load test: {e!s}")


def stop_all_tests() -> None:
    """Stop all running load tests."""
    try:
        response = requests.post(f"{LOAD_TESTER_URL}/api/load-test/stop", timeout=10)

        if response.status_code == 200:
            st.success("✅ All load tests stopped successfully!")
        else:
            st.error(f"❌ Failed to stop tests: {response.text}")

    except Exception as e:
        st.error(f"❌ Error stopping tests: {e!s}")


def get_load_test_status() -> dict[str, Any] | None:
    """Get the current status of load tests."""
    try:
        response = requests.get(f"{LOAD_TESTER_URL}/api/load-test/status", timeout=10)

        if response.status_code == 200:
            return response.json()
        return None

    except Exception as e:
        st.error(f"❌ Error getting status: {e!s}")
        return None


def show_test_report() -> None:
    """Display the test report."""
    try:
        response = requests.get(f"{LOAD_TESTER_URL}/api/load-test/report", timeout=10)

        if response.status_code == 200:
            report = response.json()
            st.json(report)
        else:
            st.error("❌ No test report available")

    except Exception as e:
        st.error(f"❌ Error getting report: {e!s}")


def display_status_table(status_data: dict[str, Any]) -> None:
    """Display the status of load tests in a table format."""
    if not status_data:
        return

    # Display current test status
    status = status_data.get("status", "unknown")
    config = status_data.get("config", {})
    stats = status_data.get("stats", {})

    # Status indicator
    status_color = "🟢" if status == "running" else "🔴" if status == "stopped" else "🟡"
    st.write(f"**Status**: {status_color} {status.upper()}")

    if config:
        st.write(f"**Configuration**: {config.get('requests_per_second', 0)} RPS")

    if stats:
        col1, col2 = st.columns(2)

        with col1:
            st.write("**Statistics:**")
            st.write(f"- Total Requests: {stats.get('total_requests', 0)}")
            st.write(f"- Successful: {stats.get('successful_requests', 0)}")
            st.write(f"- Failed: {stats.get('failed_requests', 0)}")

        with col2:
            st.write("**Performance:**")
            st.write(f"- Avg Response: {stats.get('avg_response_time_ms', 0):.1f}ms")
            st.write(f"- Min Response: {stats.get('min_response_time_ms', 0):.1f}ms")
            st.write(f"- Max Response: {stats.get('max_response_time_ms', 0):.1f}ms")
