"""DDoS Attack simulation control page for the dashboard."""

import time
from typing import Any

import requests
import streamlit as st

from dashboard.utils import API_BASE_URL, LOAD_TESTER_URL


def show_attack_simulation_page():
    """Display the DDoS attack simulation control page."""
    st.header("🚨 DDoS Attack Simulation")
    st.markdown(
        """
        This page allows you to simulate DDoS attacks against the Currency Conversion API
        for testing monitoring, alerting, and investigation capabilities.

        **⚠️ Warning**: This will generate high load against the API. Use only in development/demo environments.
        """
    )

    # Create two columns for baseline and attack controls
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("👥 Baseline Traffic")
        st.markdown("Simulate normal user activity")

        baseline_rps = st.slider(
            "Baseline RPS", min_value=1, max_value=20, value=10, help="Normal user request rate"
        )

        baseline_users = st.number_input(
            "Number of Users",
            min_value=5,
            max_value=50,
            value=20,
            help="Number of different users making requests",
        )

        if st.button("🟢 Start Baseline Traffic", key="start_baseline"):
            start_baseline_traffic(baseline_rps, baseline_users)

        if st.button("🔴 Stop Baseline Traffic", key="stop_baseline"):
            stop_baseline_traffic()

    with col2:
        st.subheader("⚡ Attack Traffic")
        st.markdown("Simulate DDoS attack from single user")

        attack_rps = st.slider(
            "Attack RPS",
            min_value=50,
            max_value=500,
            value=100,
            help="Attack request rate (should trigger alerts)",
        )

        attack_pattern = st.selectbox(
            "Attack Pattern",
            ["Sustained", "Gradual Ramp", "Burst Waves"],
            help="Type of attack pattern to simulate",
        )

        # Show pattern details
        if attack_pattern == "Sustained":
            st.info("💡 Maintains constant high RPS for extended period")
        elif attack_pattern == "Gradual Ramp":
            st.info("💡 Starts low and gradually increases to target RPS over 2 minutes")
        elif attack_pattern == "Burst Waves":
            st.info("💡 Alternates between high and low RPS in 30-second waves")

        if st.button("🚨 Start Attack", key="start_attack"):
            start_attack_traffic(attack_rps, attack_pattern)

        if st.button("🛑 Stop Attack", key="stop_attack"):
            stop_attack_traffic()

    # Advanced Pattern Controls (if pattern is active)
    st.subheader("🎛️ Manual Pattern Controls")

    # Gradual Ramp Controls
    if st.session_state.get("ramp_active", False):
        col1, col2 = st.columns(2)

        with col1:
            current_rps = st.session_state.get("ramp_current", 0)
            target_rps = st.session_state.get("ramp_target", 0)
            st.metric("Current RPS", current_rps)
            st.metric("Target RPS", target_rps)

        with col2:
            if st.button("📈 Ramp Up (+25%)", key="ramp_up"):
                ramp_attack_up()

            if st.button("📉 Ramp Down (-25%)", key="ramp_down"):
                ramp_attack_down()

    # Burst Wave Controls
    elif st.session_state.get("burst_active", False):
        col1, col2 = st.columns(2)

        with col1:
            burst_state = st.session_state.get("burst_state", "high")
            high_rps = st.session_state.get("burst_high", 0)
            low_rps = st.session_state.get("burst_low", 0)
            current_rps = high_rps if burst_state == "high" else low_rps

            st.metric("Burst State", burst_state.title())
            st.metric("Current RPS", current_rps)

        with col2:
            if st.button("⬆️ High Burst", key="burst_high"):
                switch_to_high_burst()

            if st.button("⬇️ Low Burst", key="burst_low"):
                switch_to_low_burst()

    # Status display
    st.subheader("📊 Current Status")

    # Refresh button
    col1, col2, col3 = st.columns([1, 1, 3])
    with col1:
        if st.button("🔄 Refresh Status"):
            st.rerun()

    with col2:
        auto_refresh = st.checkbox("Auto-refresh (5s)", value=False)

    # Auto-refresh logic
    if auto_refresh:
        time.sleep(5)
        st.rerun()

    # Get status of concurrent load tests
    status_data = get_load_test_status()

    if status_data:
        display_status_table(status_data)
    else:
        st.info("No active load tests")

    # Demo Workflow
    st.subheader("🎯 Complete Demo Workflow")

    # Demo workflow tabs
    tab1, tab2, tab3 = st.tabs(
        ["📋 Pre-Attack Setup", "🚨 During Attack", "🔍 Post-Attack Investigation"]
    )

    with tab1:
        show_pre_attack_workflow()

    with tab2:
        show_during_attack_workflow()

    with tab3:
        show_post_attack_workflow()

    # Monitoring links
    st.subheader("🔍 Quick Investigation Links")
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📈 Grafana Dashboard"):
            st.markdown("[Open Grafana →](http://localhost:3000)", unsafe_allow_html=True)

    with col2:
        if st.button("🔍 Jaeger Traces"):
            st.markdown("[Open Jaeger →](http://localhost:16686)", unsafe_allow_html=True)

    with col3:
        if st.button("📊 User Activity Analysis"):
            show_user_activity_analysis()


def start_baseline_traffic(rps: int, users: int) -> None:
    """Start baseline traffic simulation."""
    try:
        # Calculate RPS per user to distribute load
        rps_per_user = max(0.1, rps / users)

        # Start multiple concurrent tests to simulate different users
        for i in range(min(users, 10)):  # Limit to 10 concurrent tests
            test_id = f"baseline_user_{i + 1}"

            payload = {
                "config": {"requests_per_second": rps_per_user, "error_injection_enabled": False}
            }

            response = requests.post(
                f"{LOAD_TESTER_URL}/api/load-test/concurrent/{test_id}/start",
                json=payload,
                timeout=10,
            )

            if response.status_code != 200:
                st.error(f"Failed to start baseline user {i + 1}: {response.text}")
                return

        st.success(f"✅ Started baseline traffic: {rps} RPS across {min(users, 10)} users")

    except Exception as e:
        st.error(f"❌ Error starting baseline traffic: {e}")


def start_attack_traffic(rps: int, pattern: str) -> None:
    """Start attack traffic simulation with different patterns."""
    try:
        if pattern == "Sustained":
            _start_sustained_attack(rps)
        elif pattern == "Gradual Ramp":
            _start_gradual_ramp_attack(rps)
        elif pattern == "Burst Waves":
            _start_burst_wave_attack(rps)
        else:
            st.error(f"Unknown attack pattern: {pattern}")

    except Exception as e:
        st.error(f"❌ Error starting {pattern} attack: {e}")


def _start_sustained_attack(rps: int) -> None:
    """Start a sustained high-RPS attack."""
    test_id = "ddos_attack"

    payload = {"config": {"requests_per_second": rps, "error_injection_enabled": False}}

    response = requests.post(
        f"{LOAD_TESTER_URL}/api/load-test/concurrent/{test_id}/start", json=payload, timeout=10
    )

    if response.status_code == 200:
        st.success(f"🚨 Started sustained attack: {rps} RPS")
        st.warning("⚠️ Monitor Grafana for alerts and response time impact")
    else:
        st.error(f"❌ Failed to start sustained attack: {response.text}")


def _start_gradual_ramp_attack(target_rps: int) -> None:
    """Start a gradual ramp attack that increases RPS over time."""
    test_id = "ddos_attack"

    # Start with 1/5 of target RPS
    initial_rps = max(5, target_rps // 5)

    payload = {"config": {"requests_per_second": initial_rps, "error_injection_enabled": False}}

    response = requests.post(
        f"{LOAD_TESTER_URL}/api/load-test/concurrent/{test_id}/start", json=payload, timeout=10
    )

    if response.status_code == 200:
        st.success(
            f"🚨 Started gradual ramp attack: {initial_rps} → {target_rps} RPS over 2 minutes"
        )
        st.warning("⚠️ RPS will automatically increase every 30 seconds")
        st.info("💡 Use the 'Ramp to Higher RPS' button below to manually increase intensity")

        # Store ramp info in session state for manual ramping
        st.session_state["ramp_target"] = target_rps
        st.session_state["ramp_current"] = initial_rps
        st.session_state["ramp_active"] = True
    else:
        st.error(f"❌ Failed to start gradual ramp attack: {response.text}")


def _start_burst_wave_attack(max_rps: int) -> None:
    """Start a burst wave attack (high/low alternating pattern)."""
    test_id = "ddos_attack"

    # Start with first burst at full RPS
    payload = {"config": {"requests_per_second": max_rps, "error_injection_enabled": False}}

    response = requests.post(
        f"{LOAD_TESTER_URL}/api/load-test/concurrent/{test_id}/start", json=payload, timeout=10
    )

    if response.status_code == 200:
        st.success(f"🚨 Started burst wave attack: {max_rps} RPS bursts")
        st.warning(
            f"⚠️ Will alternate between high ({max_rps}) and low ({max_rps // 5}) RPS every 30 seconds"
        )
        st.info("💡 Use manual controls below to simulate the wave pattern")

        # Store burst info in session state
        st.session_state["burst_high"] = max_rps
        st.session_state["burst_low"] = max_rps // 5
        st.session_state["burst_active"] = True
        st.session_state["burst_state"] = "high"  # Start in high burst
    else:
        st.error(f"❌ Failed to start burst wave attack: {response.text}")


def stop_baseline_traffic() -> None:
    """Stop all baseline traffic."""
    try:
        # Get list of active tests
        response = requests.get(f"{LOAD_TESTER_URL}/api/load-test/concurrent/active", timeout=10)

        if response.status_code == 200:
            active_tests = response.json()
            baseline_tests = [test for test in active_tests if test.startswith("baseline_")]

            stopped_count = 0
            for test_id in baseline_tests:
                stop_response = requests.post(
                    f"{LOAD_TESTER_URL}/api/load-test/concurrent/{test_id}/stop", timeout=10
                )
                if stop_response.status_code == 200:
                    stopped_count += 1

            if stopped_count > 0:
                st.success(f"✅ Stopped {stopped_count} baseline traffic generators")
            else:
                st.info("i️ No baseline traffic was running")
        else:
            st.error(f"❌ Failed to get active tests: {response.text}")

    except Exception as e:
        st.error(f"❌ Error stopping baseline traffic: {e}")


def stop_attack_traffic() -> None:
    """Stop attack traffic and clean up session state."""
    try:
        test_id = "ddos_attack"
        response = requests.post(
            f"{LOAD_TESTER_URL}/api/load-test/concurrent/{test_id}/stop", timeout=10
        )

        # Clean up session state regardless of API response
        for key in [
            "ramp_active",
            "ramp_current",
            "ramp_target",
            "burst_active",
            "burst_high",
            "burst_low",
            "burst_state",
        ]:
            if key in st.session_state:
                del st.session_state[key]

        if response.status_code == 200:
            st.success("🛑 Attack stopped")
        elif response.status_code == 404:
            st.info("i️ No attack was running")
        else:
            st.error(f"❌ Failed to stop attack: {response.text}")

    except Exception as e:
        st.error(f"❌ Error stopping attack: {e}")


def get_load_test_status() -> dict[str, Any] | None:
    """Get status of all concurrent load tests."""
    try:
        response = requests.get(f"{LOAD_TESTER_URL}/api/load-test/concurrent/status", timeout=10)

        if response.status_code == 200:
            return response.json()
        return None

    except Exception:
        return None


def display_status_table(status_data: dict[str, Any]) -> None:
    """Display load test status in a table."""
    if not status_data:
        return

    # Prepare table data
    table_data = []
    total_rps = 0

    for test_id, test_status in status_data.items():
        if test_status["status"] in ["running", "starting"]:
            config = test_status.get("config", {})
            stats = test_status.get("stats", {})

            test_type = "🚨 Attack" if test_id == "ddos_attack" else "👤 Baseline"
            rps = config.get("requests_per_second", 0)
            total_rps += rps

            table_data.append(
                {
                    "Type": test_type,
                    "Test ID": test_id,
                    "Status": test_status["status"].title(),
                    "Target RPS": f"{rps:.1f}",
                    "Current RPS": f"{stats.get('requests_per_second', 0):.1f}",
                    "Total Requests": stats.get("total_requests", 0),
                    "Success Rate": f"{((stats.get('successful_requests', 0) / max(stats.get('total_requests', 1), 1)) * 100):.1f}%",
                }
            )

    if table_data:
        st.dataframe(table_data, use_container_width=True)

        # Summary metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total RPS", f"{total_rps:.1f}")
        with col2:
            baseline_count = len([t for t in table_data if "Baseline" in t["Type"]])
            st.metric("Baseline Users", baseline_count)
        with col3:
            attack_active = any("Attack" in t["Type"] for t in table_data)
            st.metric("Attack Status", "🚨 ACTIVE" if attack_active else "🟢 None")


def ramp_attack_up() -> None:
    """Increase attack RPS by 25%."""
    try:
        current_rps = st.session_state.get("ramp_current", 0)
        new_rps = int(current_rps * 1.25)
        target_rps = st.session_state.get("ramp_target", 0)

        # Cap at target RPS
        if new_rps > target_rps:
            new_rps = target_rps

        if new_rps > current_rps:
            # Update the attack test
            payload = {"config": {"requests_per_second": new_rps, "error_injection_enabled": False}}

            response = requests.post(
                f"{LOAD_TESTER_URL}/api/load-test/concurrent/ddos_attack/start",
                json=payload,
                timeout=10,
            )

            if response.status_code == 200:
                st.session_state["ramp_current"] = new_rps
                st.success(f"📈 Ramped up to {new_rps} RPS")
                if new_rps >= target_rps:
                    st.info("🎯 Target RPS reached!")
                st.rerun()
            else:
                st.error(f"❌ Failed to ramp up: {response.text}")
        else:
            st.info("i️ Already at target RPS")

    except Exception as e:
        st.error(f"❌ Error ramping up: {e}")


def ramp_attack_down() -> None:
    """Decrease attack RPS by 25%."""
    try:
        current_rps = st.session_state.get("ramp_current", 0)
        new_rps = max(5, int(current_rps * 0.75))  # Minimum 5 RPS

        if new_rps < current_rps:
            # Update the attack test
            payload = {"config": {"requests_per_second": new_rps, "error_injection_enabled": False}}

            response = requests.post(
                f"{LOAD_TESTER_URL}/api/load-test/concurrent/ddos_attack/start",
                json=payload,
                timeout=10,
            )

            if response.status_code == 200:
                st.session_state["ramp_current"] = new_rps
                st.success(f"📉 Ramped down to {new_rps} RPS")
                st.rerun()
            else:
                st.error(f"❌ Failed to ramp down: {response.text}")
        else:
            st.info("i️ Already at minimum RPS")

    except Exception as e:
        st.error(f"❌ Error ramping down: {e}")


def switch_to_high_burst() -> None:
    """Switch to high burst mode."""
    try:
        high_rps = st.session_state.get("burst_high", 100)

        payload = {"config": {"requests_per_second": high_rps, "error_injection_enabled": False}}

        response = requests.post(
            f"{LOAD_TESTER_URL}/api/load-test/concurrent/ddos_attack/start",
            json=payload,
            timeout=10,
        )

        if response.status_code == 200:
            st.session_state["burst_state"] = "high"
            st.success(f"⬆️ Switched to high burst: {high_rps} RPS")
            st.rerun()
        else:
            st.error(f"❌ Failed to switch to high burst: {response.text}")

    except Exception as e:
        st.error(f"❌ Error switching to high burst: {e}")


def switch_to_low_burst() -> None:
    """Switch to low burst mode."""
    try:
        low_rps = st.session_state.get("burst_low", 20)

        payload = {"config": {"requests_per_second": low_rps, "error_injection_enabled": False}}

        response = requests.post(
            f"{LOAD_TESTER_URL}/api/load-test/concurrent/ddos_attack/start",
            json=payload,
            timeout=10,
        )

        if response.status_code == 200:
            st.session_state["burst_state"] = "low"
            st.success(f"⬇️ Switched to low burst: {low_rps} RPS")
            st.rerun()
        else:
            st.error(f"❌ Failed to switch to low burst: {response.text}")

    except Exception as e:
        st.error(f"❌ Error switching to low burst: {e}")


def show_pre_attack_workflow() -> None:
    """Display pre-attack setup workflow."""
    st.markdown("### 📋 Phase 1: Pre-Attack Setup")

    st.markdown("""
    **Objective**: Establish normal baseline and verify monitoring is working

    **Steps to follow:**
    """)

    # Step-by-step checklist
    steps = [
        (
            "1️⃣ **Start Baseline Traffic**",
            "Use controls above to start 10 RPS baseline with 20 users",
        ),
        ("2️⃣ **Verify Normal Metrics**", "Check Grafana shows ~10 RPS with good response times"),
        ("3️⃣ **Confirm No Alerts**", "Ensure no existing alerts are firing in Grafana"),
        ("4️⃣ **Check User Activity**", "Use 'User Activity Analysis' to see normal user patterns"),
        ("5️⃣ **Setup Monitoring**", "Open Grafana dashboard in separate browser tab for monitoring"),
    ]

    for step, description in steps:
        st.markdown(f"**{step}**")
        st.markdown(f"   {description}")
        st.markdown("")

    # Pre-attack checklist
    st.markdown("**Pre-Attack Checklist:**")

    col1, col2 = st.columns([3, 1])
    with col1:
        baseline_ready = st.checkbox(
            "✅ Baseline traffic is running (~10 RPS)", key="baseline_check"
        )
        grafana_ready = st.checkbox(
            "✅ Grafana dashboard is open and showing metrics", key="grafana_check"
        )
        alerts_ready = st.checkbox("✅ No existing alerts are firing", key="alerts_check")

    with col2:
        if baseline_ready and grafana_ready and alerts_ready:
            st.success("🟢 Ready for Attack!")
        else:
            st.warning("⚠️ Complete setup")

    st.markdown("---")
    st.info("💡 **Tip**: Keep Grafana open during the entire demo to watch real-time impact")


def show_during_attack_workflow() -> None:
    """Display during-attack monitoring workflow."""
    st.markdown("### 🚨 Phase 2: During Attack")

    st.markdown("""
    **Objective**: Execute attack and observe detection systems in action

    **Timeline for Demo:**
    """)

    # Attack timeline
    timeline = [
        ("T+0:00", "🚨 Launch Attack", "Start 'Gradual Ramp' attack (100→300 RPS)"),
        ("T+0:30", "📈 Check Metrics", "Grafana should show increasing RPS"),
        ("T+1:00", "🔔 First Alerts", "Request rate warning alert should fire (>20 RPS)"),
        ("T+1:30", "🚨 Critical Alert", "DDoS alert should fire (>50 RPS sustained)"),
        ("T+2:00", "📉 Performance", "Response time alerts should trigger"),
        ("T+3:00", "🎯 Peak Impact", "Full attack impact visible in all metrics"),
    ]

    for time_marker, event, description in timeline:
        col1, col2, col3 = st.columns([1, 2, 4])
        with col1:
            st.code(time_marker)
        with col2:
            st.markdown(f"**{event}**")
        with col3:
            st.markdown(description)

    # Real-time monitoring checklist
    st.markdown("**Things to Watch For:**")

    monitoring_items = [
        "🔥 **Request Rate Spike**: Grafana 'Request Rate' panel jumps to >50 RPS",
        "⏱️ **Response Time Impact**: Average response time increases >500ms",
        "🔔 **Alert Firing**: Grafana alerts panel shows active DDoS alerts",
        "📊 **Resource Usage**: CPU/Memory usage increases in system metrics",
        "👥 **User Activity**: Single user dominates request patterns",
    ]

    for item in monitoring_items:
        st.markdown(f"- {item}")

    st.markdown("---")
    st.warning("⚠️ **Demo Tip**: Narrate what you see happening in Grafana as metrics change")


def show_post_attack_workflow() -> None:
    """Display post-attack investigation workflow."""
    st.markdown("### 🔍 Phase 3: Post-Attack Investigation")

    st.markdown("""
    **Objective**: Demonstrate how to investigate and identify the attack source

    **Investigation Workflow:**
    """)

    # Investigation steps
    investigation_steps = [
        ("🛑 Stop Attack", "Use controls above to stop attack traffic"),
        ("📊 Review Metrics", "Check Grafana for attack timeline and impact"),
        ("🔍 Identify Timeframe", "Note exact start/end times of the attack"),
        ("👤 Find Attack User", "Use 'User Activity Analysis' to identify high-activity user"),
        ("🗂️ Trace Analysis", "Use Jaeger to examine requests from attack user"),
        ("📝 Evidence Collection", "Document user ID, request patterns, and impact"),
    ]

    for i, (action, description) in enumerate(investigation_steps, 1):
        st.markdown(f"**Step {i}: {action}**")
        st.markdown(f"   {description}")
        st.markdown("")

    # Investigation tools
    st.markdown("**Investigation Tools & Evidence:**")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Metrics Evidence:**")
        st.markdown("- Request rate timeline")
        st.markdown("- Response time degradation")
        st.markdown("- Alert timestamps")
        st.markdown("- Resource utilization impact")

        st.markdown("**Logs Evidence:**")
        st.markdown("- High-volume user requests")
        st.markdown("- Request pattern consistency")
        st.markdown("- Error rate increases")

    with col2:
        st.markdown("**Tracing Evidence:**")
        st.markdown("- User ID in trace attributes")
        st.markdown("- Request frequency patterns")
        st.markdown("- Response time distribution")
        st.markdown("- Service call patterns")

        st.markdown("**User Analysis:**")
        st.markdown("- Requests per minute calculation")
        st.markdown("- Attack user vs. normal users")
        st.markdown("- Time span and consistency")

    # Quick investigation shortcut
    st.markdown("---")
    st.markdown("**Quick Investigation Shortcuts:**")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📊 Get Recent User Activity", key="quick_activity"):
            show_user_activity_analysis()

    with col2:
        if st.button("🔍 Jaeger Attack Filter", key="jaeger_filter"):
            st.info("🔍 **Jaeger Search**: Filter by `user.id` attribute and attack timeframe")

    with col3:
        if st.button("📈 Grafana Timeline", key="grafana_timeline"):
            st.info("📈 **Grafana**: Use time picker to focus on attack window")

    st.markdown("---")
    st.success(
        "🎯 **Demo Complete**: You've successfully demonstrated DDoS detection and investigation!"
    )


def show_user_activity_analysis() -> None:
    """Show user activity analysis from the debug endpoint."""
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/debug/user-activity?minutes=5&limit=10", timeout=10
        )

        if response.status_code == 200:
            data = response.json()

            st.subheader("🔍 User Activity (Last 5 Minutes)")

            if data["users"]:
                # Show summary
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Active Users", data["summary"]["total_active_users"])
                with col2:
                    st.metric("Total Requests", data["summary"]["total_requests"])

                # Show top users
                st.write("**Top Active Users:**")
                user_table = []
                for user in data["users"][:5]:
                    user_table.append(
                        {
                            "User ID": user["user_id"][:8] + "...",
                            "Requests": user["request_count"],
                            "RPS": user["requests_per_minute"],
                            "Duration (min)": user["time_span_minutes"],
                        }
                    )

                st.dataframe(user_table, use_container_width=True)

                # Highlight suspicious activity
                high_activity_users = [u for u in data["users"] if u["requests_per_minute"] > 5]
                if high_activity_users:
                    st.warning(f"⚠️ {len(high_activity_users)} users with >5 RPM detected")
            else:
                st.info("No user activity in the last 5 minutes")
        else:
            st.error(f"❌ Failed to get user activity: {response.text}")

    except Exception as e:
        st.error(f"❌ Error getting user activity: {e}")
