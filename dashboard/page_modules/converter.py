"""Currency converter page."""

import streamlit as st

from dashboard.utils import convert_currency, get_current_rates


def show_converter_page():
    """Show the currency converter page."""
    st.header("💰 Currency Converter")

    # Get current rates for currency options
    rates_data = get_current_rates()
    if not rates_data:
        st.error("Unable to load currency data")
        return

    currencies = [rate["currency"] for rate in rates_data["rates"]]

    # Input form
    col1, col2, col3 = st.columns(3)

    with col1:
        amount = st.number_input(
            "Amount",
            min_value=0.01,
            value=100.0,
            step=0.01,
            format="%.2f",
        )

    with col2:
        from_currency = st.selectbox("From Currency", currencies, index=currencies.index("USD"))

    with col3:
        to_currency = st.selectbox("To Currency", currencies, index=currencies.index("EUR"))

    if st.button("Convert", type="primary"):
        if from_currency == to_currency:
            st.warning("Please select different currencies")
        else:
            result = convert_currency(amount, from_currency, to_currency)
            if result:
                st.success("✅ Conversion successful!")

                # Display result
                col1, col2 = st.columns(2)
                with col1:
                    st.metric(
                        "Original Amount",
                        f"{float(result['amount']):.2f} {result['from_currency']}",
                    )
                with col2:
                    st.metric(
                        "Converted Amount",
                        f"{float(result['converted_amount']):.2f} {result['to_currency']}",
                    )

                # Additional details
                st.subheader("Conversion Details")
                details_data = {
                    "Exchange Rate": f"{float(result['exchange_rate']):.6f}",
                    "Conversion ID": result["conversion_id"],
                    "Timestamp": result["conversion_timestamp"],
                    "Rate Source": result["metadata"]["rate_source"],
                }

                for key, value in details_data.items():
                    st.text(f"{key}: {value}")
