"""Category 1: Returns and Price Behaviour Features (F01–F10).

Features:
- F01: daily_return (1d)
- F02: log_return (1d)
- F03: return_5d (5d momentum)
- F04: return_20d (20d momentum)
- F05: return_60d (60d momentum)
- F06: return_z5 (5d rolling z-score of returns)
- F07: return_z20 (20d rolling z-score of returns)
- F08: abs_return (|daily_return|)
- F09: price_rel_ma20 (Close / MA20 - 1)
- F10: price_rel_ma60 (Close / MA60 - 1)
"""

import pandas as pd


def compute_returns_features(df: pd.DataFrame) -> pd.DataFrame:
    """Computes Category 1 features F01 to F10.

    Args:
        df: Single-stock OHLCV DataFrame sorted chronologically.

    Returns:
        pd.DataFrame: DataFrame containing F01 to F10 columns.
    """
    raise NotImplementedError("Scaffold only — implementation pending Phase 5")
