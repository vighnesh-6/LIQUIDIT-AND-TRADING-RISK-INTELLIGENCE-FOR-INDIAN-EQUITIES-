"""Category 3: Liquidity and Trading-Activity Proxies (F23–F36).

Features:
- F23: log_volume (ln(Volume + 1))
- F24: volume_ma20 (20d rolling mean volume)
- F25: volume_ratio (Volume / volume_ma20)
- F26: volume_z20 (20d rolling volume z-score)
- F27: amihud_ratio (|daily_return| / (Volume * Close) * 1e6; excluded if Volume=0)
- F28: amihud_ma20 (20d rolling mean of Amihud ratio)
- F29: amihud_z20 (20d rolling Amihud z-score)
- F30: turnover_value (Volume * Close)
- F31: log_turnover (ln(turnover_value + 1))
- F32: turnover_ma20 (20d rolling turnover)
- F33: turnover_ratio (turnover_value / turnover_ma20)
- F34: zero_return_flag (1 if |daily_return| < 1e-4 else 0)
- F35: zero_vol_flag (1 if Volume == 0 else 0)
- F36: low_volume_streak (5d rolling sum of volume_ratio < 0.3)
"""

import pandas as pd


def compute_liquidity_features(df: pd.DataFrame) -> pd.DataFrame:
    """Computes Category 3 features F23 to F36.

    Args:
        df: Single-stock OHLCV DataFrame sorted chronologically.

    Returns:
        pd.DataFrame: DataFrame containing F23 to F36 columns.
    """
    raise NotImplementedError("Scaffold only — implementation pending Phase 5")
