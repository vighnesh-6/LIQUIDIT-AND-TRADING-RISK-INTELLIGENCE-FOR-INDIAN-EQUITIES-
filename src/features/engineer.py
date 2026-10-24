"""Feature engineering orchestrator.

Responsible for:
- Coordinating computation of all 55 features across all 6 categories.
- Processing one stock at a time to strictly maintain RAM ceiling (<5 GB).
- Downcasting all feature columns to float32.
- Tagging the warm-up period (`is_warmup=True` for first 80 trading days per stock).
- Storing feature matrix into `data/processed/`.
"""

from typing import Optional
import pandas as pd


class FeatureEngineer:
    """Orchestrates feature engineering across all 55 audited features."""

    def __init__(
        self,
        warmup_rows: int = 80,
        output_dtype: str = "float32",
    ) -> None:
        self.warmup_rows = warmup_rows
        self.output_dtype = output_dtype

    def compute_stock_features(
        self,
        stock_df: pd.DataFrame,
        benchmark_df: pd.DataFrame,
        vix_df: Optional[pd.DataFrame] = None,
    ) -> pd.DataFrame:
        """Computes full 55-feature matrix for a single stock time series.

        Args:
            stock_df: Cleaned OHLCV DataFrame for single ticker.
            benchmark_df: Cleaned Nifty 50 benchmark DataFrame.
            vix_df: Optional supplementary India VIX DataFrame.

        Returns:
            pd.DataFrame: Feature matrix containing F01-F55 with `is_warmup` flag.
        """
        raise NotImplementedError("Scaffold only — implementation pending Phase 5")

    def process_universe(
        self,
        clean_ohlcv_path: str,
        benchmark_path: str,
        output_path: str,
    ) -> None:
        """Iterates sequentially stock-by-stock to write processed feature matrix.

        Args:
            clean_ohlcv_path: Path to data/interim/stocks/ clean Parquet.
            benchmark_path: Path to data/interim/market/ benchmark Parquet.
            output_path: Path to data/processed/ target Parquet.
        """
        raise NotImplementedError("Scaffold only — implementation pending Phase 5")
