"""Page 1: Market Overview.

Displays:
- Top/Bottom ranked stocks by rule-based Liquidity Risk Score (LRS).
- Top stocks flagged by forward High-Risk Event probability (HRE_prob).
- Cross-sectional distribution of risk scores by market cap segment (Large, Mid, Small).
- Pipeline last-updated timestamp.
"""

import streamlit as st


def render_page() -> None:
    st.header("📊 Market Overview: Liquidity & Trading-Risk Regime")
    st.caption("Cross-sectional risk distribution across the 300-stock universe.")

    st.info("Market overview visualizations will render when data/predictions/ files are populated in Phase 10.")


if __name__ == "__main__":
    render_page()
