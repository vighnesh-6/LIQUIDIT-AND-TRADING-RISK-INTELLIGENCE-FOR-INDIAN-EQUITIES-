"""Main Streamlit Application Entrypoint.

ML-Based Liquidity and Trading-Risk Intelligence for Indian Equities.

Responsibilities:
- Reads predictions from data/predictions/.
- Displays summary risk metrics and navigation across multi-page views.
- Read-only dashboard: never performs model training or raw data download.
"""

import streamlit as st


def main() -> None:
    st.set_page_config(
        page_title="Liquidity & Trading-Risk Intelligence | Indian Equities",
        page_icon="📈",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.title("📈 ML-Based Liquidity & Trading-Risk Intelligence")
    st.subheader("Decision-support system for 300 Indian Equities")

    st.markdown(
        """
        > **Notice:** System scaffold initialized. Live data backfill and model artifacts
        > will populate this dashboard following execution of Phase 3 through Phase 10.
        """
    )

    st.info(
        "Please select an intelligence module from the sidebar navigation:\n"
        "- **1. Overview:** Market-wide liquidity risk ranking and sector distributions.\n"
        "- **2. Stock Detail:** Single-ticker historical LRS, F01-F55 features, and HRE probabilities.\n"
        "- **3. Portfolio Risk:** Portfolio-level aggregate liquidity concentration.\n"
        "- **4. Anomaly Log:** Unsupervised Isolation Forest historical anomaly detections.\n"
        "- **5. Data Quality:** Data pipeline health, freshness audit, and run manifests."
    )


if __name__ == "__main__":
    main()
