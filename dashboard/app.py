"""Streamlit dashboard for currency conversion API."""

import streamlit as st

from dashboard.page_modules.converter import show_converter_page
from dashboard.page_modules.historical import show_historical_trends_page
from dashboard.page_modules.load_testing import show_load_testing_page
from dashboard.page_modules.rates import show_rates_page
from dashboard.page_modules.test_results import show_test_results_page
from dashboard.utils import check_api_health


def main():
    """Main Streamlit application."""
    st.set_page_config(
        page_title="Currency Conversion Dashboard",
        page_icon="💱",
        layout="wide",
    )

    st.title("💱 Currency Conversion Dashboard")
    st.markdown("A demo dashboard for the Currency Conversion API")

    # Check API health (only show if there's an issue)
    health = check_api_health()
    if not health:
        st.error("❌ API is not accessible")
        st.stop()

    # Sidebar for navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox(
        "Choose a page",
        [
            "Currency Converter",
            "Exchange Rates",
            "Historical Trends",
            "Load Testing",
            "Test Results",
        ],
    )

    if page == "Currency Converter":
        show_converter_page()
    elif page == "Exchange Rates":
        show_rates_page()
    elif page == "Historical Trends":
        show_historical_trends_page()
    elif page == "Load Testing":
        show_load_testing_page()
    elif page == "Test Results":
        show_test_results_page()


if __name__ == "__main__":
    main()
