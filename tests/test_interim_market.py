"""Focused unit and contract tests for interim market index datasets and interim folder structure."""

from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from src.data.validator import DataValidator


@pytest.fixture
def synthetic_index_data():
    """Generates synthetic index OHLCV DataFrame."""
    dates = pd.date_range("2024-01-01", periods=20, freq="B")
    np.random.seed(42)
    prices = 20000.0 + np.cumsum(np.random.randn(20) * 100)

    df = pd.DataFrame(
        {
            "Date": dates,
            "Open": (prices - 20).astype("float32"),
            "High": (prices + 50).astype("float32"),
            "Low": (prices - 50).astype("float32"),
            "Close": prices.astype("float32"),
            "Volume": np.full(20, 100000, dtype="int64"),
        }
    )
    return df


def test_clean_market_index_unit(synthetic_index_data):
    """Verifies DataValidator.clean_market_index standardizes columns, sorts, and computes returns."""
    validator = DataValidator()
    cleaned = validator.clean_market_index(synthetic_index_data, ticker="^TEST")

    # Column schema
    assert "date" in cleaned.columns
    assert "ticker" in cleaned.columns
    assert "open" in cleaned.columns
    assert "high" in cleaned.columns
    assert "low" in cleaned.columns
    assert "close" in cleaned.columns
    assert "volume" in cleaned.columns
    assert "prev_close" in cleaned.columns
    assert "daily_return" in cleaned.columns
    assert "is_valid_ohlcv" in cleaned.columns
    assert "is_zero_volume" in cleaned.columns
    assert "is_extreme_move" in cleaned.columns

    # Ticker assigned
    assert (cleaned["ticker"] == "^TEST").all()

    # Row count preserved
    assert len(cleaned) == len(synthetic_index_data)

    # All OHLC relationships valid
    assert cleaned["is_valid_ohlcv"].all()

    # Chronologically sorted
    assert cleaned["date"].is_monotonic_increasing


def test_clean_market_index_vix_behavior():
    """Verifies that VIX volume=0 is correctly flagged without failing validation."""
    validator = DataValidator()
    dates = pd.date_range("2024-01-01", periods=10, freq="B")
    vix_df = pd.DataFrame(
        {
            "date": dates,
            "open": np.full(10, 15.0, dtype="float32"),
            "high": np.full(10, 16.0, dtype="float32"),
            "low": np.full(10, 14.0, dtype="float32"),
            "close": np.full(10, 15.5, dtype="float32"),
            "volume": np.zeros(10, dtype="int64"),
        }
    )

    cleaned = validator.clean_market_index(vix_df, ticker="^INDIAVIX")
    assert len(cleaned) == 10
    assert cleaned["is_valid_ohlcv"].all()
    # Structural zero volume for VIX flagged True
    assert cleaned["is_zero_volume"].all()
    assert "daily_change" in cleaned.columns


def test_clean_market_index_detects_corrupt_ohlcv():
    """Verifies that high < low or nonpositive prices are flagged in is_valid_ohlcv."""
    validator = DataValidator()
    dates = pd.date_range("2024-01-01", periods=5, freq="B")
    df = pd.DataFrame(
        {
            "date": dates,
            "open": [100.0, 100.0, 100.0, 100.0, 100.0],
            "high": [105.0, 95.0, 105.0, 105.0, 105.0],  # row 1: high < low
            "low": [95.0, 98.0, 95.0, 95.0, 95.0],
            "close": [102.0, 100.0, 0.0, 102.0, 102.0],  # row 2: zero close
            "volume": [1000, 1000, 1000, 1000, 1000],
        }
    )

    cleaned = validator.clean_market_index(df, ticker="^TEST")
    assert bool(cleaned.loc[1, "is_valid_ohlcv"]) is False
    assert bool(cleaned.loc[2, "is_valid_ohlcv"]) is False
    assert bool(cleaned.loc[0, "is_valid_ohlcv"]) is True


# =====================================================================
# Contract Tests for Physical On-Disk Files
# =====================================================================

STOCKS_INTERIM_PATH = Path("data/interim/stocks/ohlcv_clean.parquet")
MARKET_DIR = Path("data/interim/market")
NIFTY50_PATH = MARKET_DIR / "nifty50_clean.parquet"
BANKNIFTY_PATH = MARKET_DIR / "banknifty_clean.parquet"
INDIAVIX_PATH = MARKET_DIR / "india_vix_clean.parquet"


@pytest.mark.skipif(not STOCKS_INTERIM_PATH.exists(), reason="Clean stock interim dataset not present")
def test_interim_stocks_dataset_contract():
    """Verifies stock interim dataset structure, row count, ticker count, and benchmark columns."""
    df = pd.read_parquet(STOCKS_INTERIM_PATH)

    # 1. Total row count matches full interim inventory
    assert len(df) == 565190

    # 2. 300 unique stock tickers
    unique_tickers = df["ticker"].nunique()
    assert unique_tickers == 300

    # 3. Market indices NOT appended as stock rows
    assert "^NSEI" not in df["ticker"].values
    assert "^NSEBANK" not in df["ticker"].values
    assert "^INDIAVIX" not in df["ticker"].values

    # 4. Zero duplicate (date, ticker) keys
    assert df.duplicated(subset=["date", "ticker"]).sum() == 0

    # 5. Preserved benchmark columns
    benchmark_cols = [
        "benchmark_close",
        "benchmark_return",
        "nifty_close",
        "nifty_return",
        "is_benchmark_available",
        "is_muhurat_session",
        "benchmark_close_fallback",
        "benchmark_return_fallback",
    ]
    for col in benchmark_cols:
        assert col in df.columns, f"Missing benchmark column: {col}"

    # 6. Reconciled active trading day count (zero-volume rows filtered)
    zero_vol_count = int(df["is_zero_volume"].sum())
    assert zero_vol_count == 751
    assert len(df[~df["is_zero_volume"]]) == 564439


@pytest.mark.skipif(not NIFTY50_PATH.exists(), reason="Clean Nifty 50 dataset not present")
def test_interim_nifty50_contract():
    """Verifies Nifty 50 interim dataset structure, row count, and validity."""
    df = pd.read_parquet(NIFTY50_PATH)

    assert len(df) == 2171
    assert df["ticker"].unique().tolist() == ["^NSEI"]
    assert df["is_valid_ohlcv"].all()
    assert df["date"].is_monotonic_increasing
    assert "daily_return" in df.columns


@pytest.mark.skipif(not BANKNIFTY_PATH.exists(), reason="Clean Bank Nifty dataset not present")
def test_interim_banknifty_contract():
    """Verifies Bank Nifty interim dataset structure, row count, and validity."""
    df = pd.read_parquet(BANKNIFTY_PATH)

    assert len(df) == 2172
    assert df["ticker"].unique().tolist() == ["^NSEBANK"]
    assert df["is_valid_ohlcv"].all()
    assert df["date"].is_monotonic_increasing
    assert "daily_return" in df.columns


@pytest.mark.skipif(not INDIAVIX_PATH.exists(), reason="Clean India VIX dataset not present")
def test_interim_india_vix_contract():
    """Verifies India VIX interim dataset structure, row count, and validity."""
    df = pd.read_parquet(INDIAVIX_PATH)

    assert len(df) == 2156
    assert df["ticker"].unique().tolist() == ["^INDIAVIX"]
    assert df["is_valid_ohlcv"].all()
    assert df["is_zero_volume"].all()  # Structural for VIX
    assert df["date"].is_monotonic_increasing
    assert "daily_return" in df.columns
    assert "daily_change" in df.columns
