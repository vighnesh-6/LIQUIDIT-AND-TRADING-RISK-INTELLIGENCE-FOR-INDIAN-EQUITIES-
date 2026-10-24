"""Page 3: Portfolio Risk Aggregator.

Displays:
- User portfolio builder (up to 30 custom tickers with optional weightings).
- Aggregate weighted Liquidity Risk Score.
- Count and percentage of portfolio holdings flagged with high forward risk (HRE_prob > 0.50).
- Liquidity concentration warnings across market-cap segments.
"""

import streamlit as st


def render_page() -> None:
    st.header("💼 Portfolio Liquidity & Trading-Risk Aggregator")
    st.caption("Evaluate aggregate liquidity risk exposure and concentration across user-defined holdings.")

    st.info("Portfolio risk analysis will activate after scoring pipeline deployment in Phase 11.")


if __name__ == "__main__":
    render_page()
