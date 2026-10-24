"""Reusable Plotly charting components for Streamlit."""

from typing import Any, Optional
import pandas as pd
import plotly.graph_objects as go


def build_risk_trajectory_chart(
    df: pd.DataFrame,
    date_col: str = "date",
    score_col: str = "lrs",
    prob_col: Optional[str] = "hre_prob",
) -> go.Figure:
    """Builds interactive dual-axis Plotly chart displaying LRS and HRE_prob over time.

    Args:
        df: Scored stock DataFrame.
        date_col: Date column name.
        score_col: LRS column name.
        prob_col: Forward probability column name.

    Returns:
        go.Figure: Plotly figure object.
    """
    raise NotImplementedError("Scaffold only — implementation pending Phase 11")


def build_risk_gauge(score: float, title: str = "Current LRS") -> go.Figure:
    """Builds risk gauge widget color-coded by audited risk band thresholds.

    Args:
        score: Liquidity risk score (0-100).
        title: Gauge title.

    Returns:
        go.Figure: Plotly gauge figure.
    """
    raise NotImplementedError("Scaffold only — implementation pending Phase 11")
