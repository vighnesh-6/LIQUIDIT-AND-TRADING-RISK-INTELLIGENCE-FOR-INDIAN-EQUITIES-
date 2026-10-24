"""Category 4: Price-Gap and Price-Impact Proxies (F37–F45).

Features:
- F37: daily_range ((High - Low) / Close)
- F38: daily_range_ma20 (20d rolling mean of daily range)
- F39: range_z20 (20d rolling daily range z-score)
- F40: overnight_gap ((Open_t - Close_{t-1}) / Close_{t-1})
- F41: overnight_gap_abs (|overnight_gap|)
- F42: gap_z20 (20d rolling overnight gap z-score)
- F43: cs_spread_est (Corwin-Schultz 2012 2-day spread estimator; clipped at 0)
- F44: cs_spread_ma10 (10d rolling mean of cs_spread_est)
- F45: intraday_return ((Close - Open) / Open)
"""

import pandas as pd


def compute_gap_features(df: pd.DataFrame) -> pd.DataFrame:
    """Computes Category 4 features F37 to F45.

    Args:
        df: Single-stock OHLCV DataFrame sorted chronologically.

    Returns:
        pd.DataFrame: DataFrame containing F37 to F45 columns.
    """
    raise NotImplementedError("Scaffold only — implementation pending Phase 5")
