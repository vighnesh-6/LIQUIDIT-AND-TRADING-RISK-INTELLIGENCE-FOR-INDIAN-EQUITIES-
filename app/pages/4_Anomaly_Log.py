"""Page 4: Anomaly Log Browser.

Displays:
- Historical audit log of stock-days flagged as anomalous by unsupervised Isolation Forest.
- Interactive filtering by ticker, date range, and market cap tier.
- Anomaly score distributions and contextual feature drivers.
"""

import streamlit as st


def render_page() -> None:
    st.header("⚡ Anomaly Log: Unsupervised Statistical Outliers")
    st.caption("Browse historical observations flagged as structurally unusual by Isolation Forest.")

    st.info("Anomaly log tables will activate following model training and scoring in Phase 11.")


if __name__ == "__main__":
    render_page()
