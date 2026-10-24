"""Supervised target construction module.

Responsible for:
- Constructing the forward-looking binary label `HRE_5d` (High-Risk Event in t+1 to t+5).
- Conditions triggering HRE = 1 on any of the next 5 trading days:
  1. amihud_ratio > 95th percentile cross-sectionally
  2. volume_ratio < 0.20
  3. overnight_gap_abs > 0.05 (5%)
  4. LRS > 75.0
- Enforcing strict future leakage protection: live scored rows must have HRE_5d = NaN.
- Ensuring target label is never passed as a model input feature.
"""

from typing import Optional
import pandas as pd


def construct_hre_target(
    df: pd.DataFrame,
    forward_window: int = 5,
    amihud_threshold_quantile: float = 0.95,
    volume_ratio_threshold: float = 0.20,
    gap_threshold: float = 0.05,
    lrs_threshold: float = 75.0,
) -> pd.Series:
    """Constructs the HRE_5d binary target strictly using future data (t+1 to t+5).

    Args:
        df: Feature DataFrame with date, ticker, LRS, and trigger columns.
        forward_window: Lookahead trading days (default: 5).
        amihud_threshold_quantile: Quantile threshold for extreme illiquidity.
        volume_ratio_threshold: Volume drought threshold.
        gap_threshold: Overnight absolute gap threshold.
        lrs_threshold: Critical LRS threshold.

    Returns:
        pd.Series: Binary target (0 or 1 for historical training rows; NaN for recent live rows).
    """
    raise NotImplementedError("Scaffold only — implementation pending Phase 7")
