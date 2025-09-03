"""Exchange rates page."""

import pandas as pd
import streamlit as st

from dashboard.utils import get_current_rates


def show_rates_page():
    """Show the exchange rates page."""
    st.header("📊 Current Exchange Rates")

    rates_data = get_current_rates()
    if not rates_data:
        st.error("Unable to load rates data")
        return

    st.info(
        f"Base Currency: {rates_data['base_currency']} | Last Updated: {rates_data['timestamp']}"
    )

    # Create DataFrame for better display
    rates_df = pd.DataFrame(rates_data["rates"])
    rates_df["rate"] = rates_df["rate"].astype(float)
    rates_df = rates_df.sort_values("currency")

    # Display rates table
    st.subheader("Exchange Rates Table")
    st.dataframe(
        rates_df,
        column_config={
            "currency": "Currency",
            "rate": st.column_config.NumberColumn("Rate (to USD)", format="%.6f"),
            "last_updated": "Last Updated",
        },
        hide_index=True,
        use_container_width=True,
    )
