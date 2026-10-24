"""Category 2: Volatility and Downside Risk Features (F11–F22).

Features:
- F11: vol_5d (rolling std of log returns)
- F12: vol_20d (annualized 20d realized volatility)
- F13: vol_60d (annualized 60d realized volatility)
- F14: vol_ratio_5_20 (vol_5d / vol_20d)
- F15: parkinson_vol (20d Parkinson high-low volatility)
- F16: true_range (ATR single-day component)
- F17: atr_20d (Average True Range over 20d)
- F18: downside_vol_20d (semi-deviation of negative log returns)
- F19: sortino_component (return_20d / downside_vol_20d)
- F20: max_drawdown_20d (max loss from 20d rolling peak)
- F21: rsi_14 (Relative Strength Index over 14d)
- F22: vol_of_vol (rolling 60d std of vol_20d)
"""

import pandas as pd


def compute_volatility_features(df: pd.DataFrame) -> pd.DataFrame:
    """Computes Category 2 features F11 to F22.

    Args:
        df: Single-stock OHLCV DataFrame sorted chronologically.

    Returns:
        pd.DataFrame: DataFrame containing F11 to F22 columns.
    """
    raise NotImplementedError("Scaffold only — implementation pending Phase 5")
