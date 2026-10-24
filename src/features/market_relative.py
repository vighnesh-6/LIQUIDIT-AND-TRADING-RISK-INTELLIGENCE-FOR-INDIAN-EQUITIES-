"""Category 5: Market-Relative Behaviour Features (F46–F51).

Features:
- F46: excess_return_1d (daily_return - nifty_return_1d)
- F47: excess_return_20d (return_20d - nifty_return_20d)
- F48: rolling_beta_60d (60d rolling OLS beta against Nifty 50)
- F49: rolling_corr_60d (60d Pearson correlation with Nifty 50)
- F50: idiosyncratic_vol (vol_20d * sqrt(1 - rolling_corr_60d^2))
- F51: relative_volume (volume_ratio / nifty_volume_ratio)
"""

import pandas as pd


def compute_market_relative_features(
    stock_df: pd.DataFrame,
    benchmark_df: pd.DataFrame,
) -> pd.DataFrame:
    """Computes Category 5 features F46 to F51.

    Args:
        stock_df: Single-stock OHLCV DataFrame sorted chronologically.
        benchmark_df: Nifty 50 benchmark DataFrame sorted chronologically.

    Returns:
        pd.DataFrame: DataFrame containing F46 to F51 columns.
    """
    raise NotImplementedError("Scaffold only — implementation pending Phase 5")
