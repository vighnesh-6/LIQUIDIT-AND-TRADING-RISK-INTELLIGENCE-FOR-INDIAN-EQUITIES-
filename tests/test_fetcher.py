"""Unit tests for DataFetcher module (offline, mock / synthetic data)."""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
from src.data.fetcher import DataFetcher


def test_fetcher_initialization():
    """Verifies default parameters for DataFetcher."""
    fetcher = DataFetcher(request_delay_seconds=1.0, max_retries=3)
    assert fetcher.request_delay_seconds == 1.0
    assert fetcher.max_retries == 3
    assert fetcher.auto_adjust is True


def test_normalize_ohlcv_single_level():
    """Verifies normalization of standard single-level OHLCV DataFrame."""
    fetcher = DataFetcher()
    dates = pd.date_range("2024-01-01", periods=5, freq="D", tz="Asia/Kolkata")
    raw = pd.DataFrame(
        {
            "Open": [100.0, 101.0, 102.0, 103.0, 104.0],
            "High": [105.0, 106.0, 107.0, 108.0, 109.0],
            "Low": [95.0, 96.0, 97.0, 98.0, 99.0],
            "Close": [102.0, 103.0, 104.0, 105.0, 106.0],
            "Volume": [1000, 2000, 3000, 4000, 5000],
        },
        index=dates,
    )

    norm = fetcher._normalize_ohlcv(raw, "MOCK.NS")
    expected_cols = ["date", "ticker", "open", "high", "low", "close", "volume"]
    assert list(norm.columns) == expected_cols
    assert len(norm) == 5
    assert norm["ticker"].iloc[0] == "MOCK.NS"
    # Ensure timezone has been stripped to tz-naive
    assert norm["date"].dt.tz is None
    assert norm["open"].dtype == "float32"
    assert norm["volume"].dtype == "int64"


def test_normalize_ohlcv_multiindex():
    """Verifies normalization when yfinance returns MultiIndex columns."""
    fetcher = DataFetcher()
    dates = pd.date_range("2024-01-01", periods=3, freq="D")
    cols = pd.MultiIndex.from_tuples(
        [
            ("Close", "MOCK.NS"),
            ("High", "MOCK.NS"),
            ("Low", "MOCK.NS"),
            ("Open", "MOCK.NS"),
            ("Volume", "MOCK.NS"),
        ],
        names=["Price", "Ticker"],
    )
    data = np.array(
        [
            [102.0, 105.0, 95.0, 100.0, 1000],
            [103.0, 106.0, 96.0, 101.0, 2000],
            [104.0, 107.0, 97.0, 102.0, 3000],
        ]
    )
    raw = pd.DataFrame(data, index=dates, columns=cols)

    norm = fetcher._normalize_ohlcv(raw, "MOCK.NS")
    assert list(norm.columns) == ["date", "ticker", "open", "high", "low", "close", "volume"]
    assert len(norm) == 3
    assert norm["ticker"].iloc[0] == "MOCK.NS"


def test_normalize_ohlcv_empty():
    """Verifies that normalizing empty DataFrame returns an empty DataFrame with required schema."""
    fetcher = DataFetcher()
    norm = fetcher._normalize_ohlcv(pd.DataFrame(), "EMPTY.NS")
    assert list(norm.columns) == ["date", "ticker", "open", "high", "low", "close", "volume"]
    assert norm.empty


@patch("src.data.fetcher.yf.download")
def test_fetch_ticker_history_retry_success(mock_download):
    """Verifies retry mechanism when first attempt throws an exception but second succeeds."""
    fetcher = DataFetcher(request_delay_seconds=0.01, max_retries=2, backoff_factor=1.0)
    dates = pd.date_range("2024-01-01", periods=2, freq="D")
    sample_df = pd.DataFrame(
        {"Open": [100, 101], "High": [105, 106], "Low": [95, 96], "Close": [102, 103], "Volume": [1000, 2000]},
        index=dates,
    )

    mock_download.side_effect = [Exception("Rate limit simulated"), sample_df]

    result = fetcher.fetch_ticker_history("MOCK.NS", start_date="2024-01-01")
    assert not result.empty
    assert len(result) == 2
    assert mock_download.call_count == 2
