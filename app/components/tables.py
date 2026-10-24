"""Formatted data tables and risk summary cards."""

import pandas as pd
import streamlit as st


def render_risk_summary_table(df: pd.DataFrame) -> None:
    """Renders formatted table of stocks with color-coded risk bands.

    Args:
        df: Scored universe DataFrame.
    """
    raise NotImplementedError("Scaffold only — implementation pending Phase 11")
