"""Page 5: Data Quality & Pipeline Health.

Displays:
- Pipeline execution health and timestamp of last daily refresh.
- Freshness status with visual alert if latest predictions are > 2 trading days old.
- Historical run manifests from data/manifests/ (ticker coverage, failed tickers, quality flags).
- Hardware memory and storage footprint.
"""

import streamlit as st


def render_page() -> None:
    st.header("🛡️ Pipeline Health & Data Quality Monitor")
    st.caption("Inspect pipeline freshness, data hygiene gates, and run manifests.")

    st.info("Pipeline health metrics will populate from data/manifests/ in Phase 11.")


if __name__ == "__main__":
    render_page()
