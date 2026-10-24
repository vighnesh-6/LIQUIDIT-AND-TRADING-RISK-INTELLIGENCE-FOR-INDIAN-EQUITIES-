"""Shared pytest fixtures for the Liquidity and Trading-Risk Intelligence test suite."""

import pytest
import pandas as pd
import numpy as np


@pytest.fixture
def synthetic_ohlcv_data() -> pd.DataFrame:
    """Provides a small synthetic OHLCV DataFrame for testing feature formulas without network calls."""
    dates = pd.date_range("2023-01-01", periods=100, freq="B")
    np.random.seed(42)
    close = 100 + np.cumsum(np.random.normal(0, 1.5, size=len(dates)))
    high = close + np.random.uniform(0.5, 2.0, size=len(dates))
    low = close - np.random.uniform(0.5, 2.0, size=len(dates))
    open_ = low + np.random.uniform(0.2, 1.5, size=len(dates))
    volume = np.random.randint(10000, 500000, size=len(dates))

    df = pd.DataFrame(
        {
            "date": dates,
            "ticker": "TEST.NS",
            "open": open_.astype("float32"),
            "high": high.astype("float32"),
            "low": low.astype("float32"),
            "close": close.astype("float32"),
            "volume": volume.astype("int64"),
        }
    )
    return df


@pytest.fixture
def synthetic_benchmark_data() -> pd.DataFrame:
    """Provides small synthetic Nifty 50 benchmark time series."""
    dates = pd.date_range("2023-01-01", periods=100, freq="B")
    np.random.seed(101)
    close = 18000 + np.cumsum(np.random.normal(0, 50.0, size=len(dates)))
    volume = np.random.randint(1000000, 5000000, size=len(dates))

    df = pd.DataFrame(
        {
            "date": dates,
            "ticker": "^NSEI",
            "open": (close - 10).astype("float32"),
            "high": (close + 25).astype("float32"),
            "low": (close - 25).astype("float32"),
            "close": close.astype("float32"),
            "volume": volume.astype("int64"),
        }
    )
    return df
