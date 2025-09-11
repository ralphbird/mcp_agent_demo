"""Test results page."""

import pandas as pd
import plotly.express as px
import streamlit as st

from dashboard.utils import (
    check_analytics_service_health,
    get_load_test_report,
    get_load_test_status,
)


def show_test_results_page():
    """Show the load test results and analysis page."""
    st.header("📊 Load Test Results & Analysis")

    # Check load tester health (only show if there's an issue)
    analytics_service_health = check_analytics_service_health()
    if not analytics_service_health:
        st.error("❌ Load Tester service is not accessible")
        st.info("Make sure the Load Tester service is running at http://localhost:8001")
        return

    # Get current test status for context
    status = get_load_test_status()
    if not status:
        return

    # Show current test status for context
    st.subheader("📈 Current Test Status")
    status_color = {
        "idle": "🟢",
        "starting": "🟡",
        "running": "🔴",
        "stopping": "🟡",
        "stopped": "🟠",
        "error": "❌",
    }.get(status["status"], "⚪")

    st.info(f"{status_color} **Status**: {status['status'].upper()}")

    # Test Results and Analysis
    st.subheader("📊 Test Analysis & Results")

    if status["status"] in ["stopped", "error"] or st.button("🔄 Refresh Report"):
        report = get_load_test_report()
        if report and report.get("stats", {}).get("total_requests", 0) > 0:
            # Performance Grade
            grade_color = {"A": "🟢", "B": "🟡", "C": "🟠", "D": "🔴", "F": "⚫"}.get(
                report["performance_grade"], "⚪"
            )

            st.success(f"{grade_color} **Performance Grade: {report['performance_grade']}**")

            # Key Metrics
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Total Requests", f"{report['stats']['total_requests']:,}")
            with col2:
                st.metric("Success Rate", f"{report['success_rate']:.1f}%")
            with col3:
                st.metric("Avg Response Time", f"{report['stats']['avg_response_time_ms']:.1f}ms")
            with col4:
                st.metric("Achieved RPS", f"{report['avg_rps_achieved']:.2f}")

            # Performance Chart
            if report["stats"]["total_requests"] > 0:
                chart_data = pd.DataFrame(
                    {
                        "Metric": ["Successful", "Failed"],
                        "Count": [
                            report["stats"]["successful_requests"],
                            report["stats"]["failed_requests"],
                        ],
                        "Percentage": [report["success_rate"], 100 - report["success_rate"]],
                    }
                )

                fig = px.pie(
                    chart_data,
                    values="Count",
                    names="Metric",
                    title="Request Success/Failure Distribution",
                    color_discrete_map={"Successful": "#28a745", "Failed": "#dc3545"},
                )
                st.plotly_chart(fig, use_container_width=True)

            # Recommendations
            if report.get("recommendations"):
                st.subheader("💡 Performance Recommendations")
                for i, rec in enumerate(report["recommendations"], 1):
                    st.info(f"**{i}.** {rec}")

            # Detailed Stats
            with st.expander("📋 Detailed Statistics"):
                stats_data = {
                    "Metric": [
                        "Total Requests",
                        "Successful Requests",
                        "Failed Requests",
                        "Average Response Time",
                        "Minimum Response Time",
                        "Maximum Response Time",
                        "Target RPS",
                        "Achieved RPS",
                    ],
                    "Value": [
                        f"{report['stats']['total_requests']:,}",
                        f"{report['stats']['successful_requests']:,}",
                        f"{report['stats']['failed_requests']:,}",
                        f"{report['stats']['avg_response_time_ms']:.1f}ms",
                        f"{report['stats']['min_response_time_ms']:.1f}ms",
                        f"{report['stats']['max_response_time_ms']:.1f}ms",
                        f"{report['requests_per_second']:.1f}",
                        f"{report['avg_rps_achieved']:.2f}",
                    ],
                }
                st.dataframe(pd.DataFrame(stats_data), use_container_width=True)
        else:
            st.info("No test results available. Run a load test to see performance analysis.")
            st.markdown("Navigate to the **Load Testing** page to start a new test.")

    # Navigation hint
    st.subheader("🎮 Need to run a test?")
    st.info("Go to the **Load Testing** page to start, stop, or configure load tests.")
