"""Load testing control page for the dashboard."""

import time
from typing import Any

import requests
import streamlit as st

from dashboard.utils import LOAD_TESTER_URL


def check_and_handle_auto_stop_timers():
    """Check if any tests should be automatically stopped based on duration."""
    if "auto_stop_timer" not in st.session_state:
        return

    current_time = time.time()
    tests_to_stop = []

    for test_id, timer_info in st.session_state.auto_stop_timer.items():
        elapsed_time = current_time - timer_info["start_time"]
        if elapsed_time >= timer_info["duration"]:
            tests_to_stop.append(test_id)

    # Stop expired tests
    for test_id in tests_to_stop:
        timer_info = st.session_state.auto_stop_timer[test_id]
        try:
            response = requests.post(f"{LOAD_TESTER_URL}/api/load-test/stop", timeout=10)
            if response.status_code == 200:
                st.success(
                    f"✅ {timer_info['test_type'].title()} test automatically stopped after {timer_info['duration']} seconds"
                )
            else:
                st.warning(f"⚠️ Failed to auto-stop {timer_info['test_type']} test: {response.text}")
        except Exception as e:
            st.error(f"❌ Error auto-stopping {timer_info['test_type']} test: {e!s}")

        # Remove from session state
        del st.session_state.auto_stop_timer[test_id]


def show_attack_simulation_page():
    """Display the load testing control page."""
    # Check for auto-stop timers first
    check_and_handle_auto_stop_timers()

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

        continuous_mode = st.checkbox(
            "🔄 Continuous Baseline",
            help="Run baseline continuously until manually stopped",
        )

        duration = None
        if not continuous_mode:
            duration = st.number_input(
                "Duration (seconds)",
                min_value=10,
                max_value=600,
                value=60,
                help="How long to run the test",
            )

        if st.button("🟢 Start Baseline Test", key="start_baseline"):
            if continuous_mode:
                start_continuous_baseline(baseline_rps)
            elif duration is not None:
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
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("🔴 Stop All Tests", key="stop_all"):
            stop_all_tests()

    with col2:
        if st.button("🛑 Stop Baseline", key="stop_baseline"):
            stop_baseline_test()

    with col3:
        if st.button("🔄 Refresh Status", key="refresh"):
            st.rerun()

    with col4:
        if st.button("📊 Get Report", key="get_report"):
            show_test_report()

    # Status display
    st.subheader("📊 Current Test Status")

    # Check for active timers and display countdown
    if "auto_stop_timer" in st.session_state and st.session_state.auto_stop_timer:
        current_time = time.time()
        for _test_id, timer_info in st.session_state.auto_stop_timer.items():
            elapsed_time = current_time - timer_info["start_time"]
            remaining_time = max(0, timer_info["duration"] - elapsed_time)

            if remaining_time > 0:
                minutes = int(remaining_time // 60)
                seconds = int(remaining_time % 60)
                st.info(
                    f"⏱️ {timer_info['test_type'].title()} test will auto-stop in: {minutes:02d}:{seconds:02d}"
                )

    # Get status of both main and baseline load tests
    main_status = get_load_test_status()
    baseline_status = get_baseline_test_status()

    # Display baseline status
    if baseline_status:
        st.write("**🔄 Continuous Baseline Test**")
        display_status_table(baseline_status, test_name="Baseline")
        st.divider()

    # Display main test status
    if main_status and main_status.get("status") != "idle":
        st.write("**⚡ Main Load Test**")
        display_status_table(main_status, test_name="Main")
    elif not baseline_status:
        st.info("No active load tests")

    # Performance metrics - combine stats from both tests
    st.subheader("📈 Performance Summary (1-Minute Rolling Average)")

    # Calculate combined metrics
    combined_stats = {}
    if baseline_status and baseline_status.get("stats"):
        combined_stats = baseline_status["stats"].copy()

    if main_status and main_status.get("stats"):
        main_stats = main_status["stats"]
        if combined_stats:
            # Add main test stats to baseline stats
            combined_stats["total_requests"] += main_stats.get("total_requests", 0)
            combined_stats["successful_requests"] += main_stats.get("successful_requests", 0)
            combined_stats["failed_requests"] += main_stats.get("failed_requests", 0)
            combined_stats["requests_per_second"] += main_stats.get("requests_per_second", 0)
            # Average response time weighted by request count
            if combined_stats["total_requests"] > 0:
                total_baseline = (
                    baseline_status["stats"].get("total_requests", 0) if baseline_status else 0
                )
                total_main = main_stats.get("total_requests", 0)
                if total_baseline + total_main > 0:
                    baseline_avg = (
                        baseline_status["stats"].get("avg_response_time_ms", 0)
                        if baseline_status
                        else 0
                    )
                    main_avg = main_stats.get("avg_response_time_ms", 0)
                    combined_stats["avg_response_time_ms"] = (
                        baseline_avg * total_baseline + main_avg * total_main
                    ) / (total_baseline + total_main)
        else:
            combined_stats = main_stats

    if combined_stats:
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Requests", combined_stats.get("total_requests", 0))

        with col2:
            success_rate = 0
            total = combined_stats.get("total_requests", 0)
            successful = combined_stats.get("successful_requests", 0)
            if total > 0:
                success_rate = successful / total
            st.metric("Success Rate", f"{success_rate:.1%}")

        with col3:
            st.metric("Avg Response", f"{combined_stats.get('avg_response_time_ms', 0):.1f}ms")

        with col4:
            st.metric("Combined RPS", f"{combined_stats.get('requests_per_second', 0):.1f}")

    # Auto-refresh for countdown timer
    if "auto_stop_timer" in st.session_state and st.session_state.auto_stop_timer:
        time.sleep(1)  # Small delay before refresh
        st.rerun()


def start_continuous_baseline(rps: float) -> None:
    """Start a continuous baseline load test using concurrent API."""
    try:
        # Use minimal config - let the API populate all currency pairs and amounts automatically
        config = {
            "requests_per_second": rps,
            "error_injection_enabled": True,
            "error_injection_rate": 0.02,  # Low error rate for realistic baseline
        }

        response = requests.post(
            f"{LOAD_TESTER_URL}/api/load-test/concurrent/baseline/start",
            json={"config": config},
            timeout=10,
        )

        if response.status_code == 200:
            st.success("✅ Continuous baseline load test started successfully!")
        else:
            st.error(f"❌ Failed to start baseline test: {response.text}")

    except Exception as e:
        st.error(f"❌ Error starting baseline test: {e!s}")


def start_load_test(test_type: str, rps: float, duration: int) -> None:
    """Start a load test with the specified parameters."""
    try:
        # Use minimal config - let the API populate all currency pairs and amounts automatically
        config = {
            "requests_per_second": rps,
            "error_injection_enabled": test_type == "burst",
            "error_injection_rate": 0.05 if test_type == "burst" else 0.01,
        }

        response = requests.post(
            f"{LOAD_TESTER_URL}/api/load-test/start", json={"config": config}, timeout=10
        )

        if response.status_code == 200:
            st.success(
                f"✅ {test_type.title()} load test started successfully! Will run for {duration} seconds."
            )

            # Schedule automatic stop after duration
            if "auto_stop_timer" not in st.session_state:
                st.session_state.auto_stop_timer = {}

            st.session_state.auto_stop_timer[test_type] = {
                "start_time": time.time(),
                "duration": duration,
                "test_type": test_type,
            }
        else:
            st.error(f"❌ Failed to start load test: {response.text}")

    except Exception as e:
        st.error(f"❌ Error starting load test: {e!s}")


def stop_baseline_test() -> None:
    """Stop the continuous baseline load test."""
    try:
        response = requests.post(
            f"{LOAD_TESTER_URL}/api/load-test/concurrent/baseline/stop", timeout=10
        )

        if response.status_code == 200:
            st.success("✅ Baseline load test stopped successfully!")
        else:
            st.error(f"❌ Failed to stop baseline test: {response.text}")

    except Exception as e:
        st.error(f"❌ Error stopping baseline test: {e!s}")


def stop_all_tests() -> None:
    """Stop all running load tests."""
    try:
        # Stop main load test
        response1 = requests.post(f"{LOAD_TESTER_URL}/api/load-test/stop", timeout=10)

        # Stop all concurrent tests (including baseline)
        response2 = requests.post(
            f"{LOAD_TESTER_URL}/api/load-test/concurrent/stop-all", timeout=10
        )

        if response1.status_code == 200 and response2.status_code == 200:
            st.success("✅ All load tests stopped successfully!")
        else:
            st.error(
                f"❌ Failed to stop some tests. Main: {response1.text}, Concurrent: {response2.text}"
            )

        # Clear any auto-stop timers
        if "auto_stop_timer" in st.session_state:
            st.session_state.auto_stop_timer.clear()

    except Exception as e:
        st.error(f"❌ Error stopping tests: {e!s}")


def get_baseline_test_status() -> dict[str, Any] | None:
    """Get the current status of the baseline load test."""
    try:
        response = requests.get(
            f"{LOAD_TESTER_URL}/api/load-test/concurrent/baseline/status", timeout=10
        )

        if response.status_code == 200:
            return response.json()
        return None

    except Exception:
        # Baseline test not running or doesn't exist
        return None


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


def display_status_table(status_data: dict[str, Any], test_name: str = "Test") -> None:
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
