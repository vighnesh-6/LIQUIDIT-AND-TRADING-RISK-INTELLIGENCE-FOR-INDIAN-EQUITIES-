"""Unit tests for DataValidator module (offline, synthetic fixtures)."""

import pytest
import pandas as pd
import numpy as np
from src.data.validator import DataValidator


def test_validator_clean_series(synthetic_ohlcv_data):
    """Verifies that clean synthetic data passes validation checks."""
    validator = DataValidator(min_valid_trading_days=50, stale_price_threshold=3, extreme_move_threshold=0.50)
    df_val, report = validator.validate_ticker_series(synthetic_ohlcv_data, "TEST.NS")

    assert report["is_valid"] is True
    assert report["row_count"] == 100
    assert report["has_minimum_history"] is True
    assert report["duplicate_dates"] == 0
    assert report["nonpositive_prices"] == 0
    assert report["high_less_than_low"] == 0


def test_validator_flags_nonpositive_prices(synthetic_ohlcv_data):
    """Verifies that zero or negative prices trigger validation failure."""
    validator = DataValidator(min_valid_trading_days=50)
    corrupted = synthetic_ohlcv_data.copy()
    corrupted.loc[10, "close"] = -5.0
    corrupted.loc[20, "low"] = 0.0

    df_val, report = validator.validate_ticker_series(corrupted, "TEST.NS")
    assert report["is_valid"] is False
    assert report["nonpositive_prices"] == 2
    assert any("non-positive" in w for w in report["warnings"])


def test_validator_flags_duplicate_dates(synthetic_ohlcv_data):
    """Verifies that duplicate dates are detected."""
    validator = DataValidator(min_valid_trading_days=50)
    corrupted = synthetic_ohlcv_data.copy()
    corrupted.loc[5, "date"] = corrupted.loc[4, "date"]

    df_val, report = validator.validate_ticker_series(corrupted, "TEST.NS")
    assert report["duplicate_dates"] == 1
    assert any("duplicate dates" in w for w in report["warnings"])


def test_validator_flags_zero_volume_days(synthetic_ohlcv_data):
    """Verifies that zero volume rows are tracked in quality audit."""
    validator = DataValidator(min_valid_trading_days=50)
    corrupted = synthetic_ohlcv_data.copy()
    corrupted.loc[15, "volume"] = 0
    corrupted.loc[16, "volume"] = 0

    df_val, report = validator.validate_ticker_series(corrupted, "TEST.NS")
    assert report["zero_volume_days"] == 2
    assert any("zero-volume" in w for w in report["warnings"])


def test_validator_flags_extreme_moves(synthetic_ohlcv_data):
    """Verifies that single-day jumps exceeding the threshold (e.g. >50%) are flagged."""
    validator = DataValidator(min_valid_trading_days=50, extreme_move_threshold=0.50)
    corrupted = synthetic_ohlcv_data.copy()
    # Spike close price on day 30 by 80%
    corrupted.loc[30, "close"] = corrupted.loc[29, "close"] * 1.80

    df_val, report = validator.validate_ticker_series(corrupted, "TEST.NS")
    assert report["extreme_moves_count"] >= 1
    assert len(report["extreme_move_dates"]) >= 1


def test_validator_flags_stale_prices(synthetic_ohlcv_data):
    """Verifies that unchanged closing prices for >=3 consecutive days are detected."""
    validator = DataValidator(min_valid_trading_days=50, stale_price_threshold=3)
    corrupted = synthetic_ohlcv_data.copy()
    # Set rows 10, 11, 12, 13 to identical close
    fixed_price = corrupted.loc[10, "close"]
    corrupted.loc[11, "close"] = fixed_price
    corrupted.loc[12, "close"] = fixed_price
    corrupted.loc[13, "close"] = fixed_price

    df_val, report = validator.validate_ticker_series(corrupted, "TEST.NS")
    assert report["stale_price_streaks"] == 1
    assert report["stale_price_days"] == 4
    assert report["max_stale_streak"] == 4


def test_benchmark_alignment_check(synthetic_ohlcv_data, synthetic_benchmark_data):
    """Verifies benchmark alignment validation logic."""
    validator = DataValidator()
    # Both synthetic datasets share the exact same dates
    assert validator.check_benchmark_alignment(synthetic_ohlcv_data, synthetic_benchmark_data) is True

    # Empty data should return False
    assert validator.check_benchmark_alignment(pd.DataFrame(), synthetic_benchmark_data) is False


def test_zero_volume_tagging_and_row_retention(synthetic_ohlcv_data):
    """Verifies that zero-volume rows are flagged and retained without data loss."""
    validator = DataValidator(min_valid_trading_days=50)
    data = synthetic_ohlcv_data.copy()

    # Row 10: zero volume with price unchanged (return == 0)
    data.loc[10, "volume"] = 0
    data.loc[10, "close"] = data.loc[9, "close"]

    # Row 20: zero volume with price changed (return != 0)
    data.loc[20, "volume"] = 0
    data.loc[20, "close"] = data.loc[19, "close"] * 1.02

    cleaned = validator.clean_and_enrich_stock(data, ticker="TEST.NS")

    # Row count strictly preserved (no rows dropped)
    assert len(cleaned) == len(synthetic_ohlcv_data)
    assert cleaned.loc[10, "is_zero_volume"] is True or cleaned.loc[10, "is_zero_volume"] == 1
    assert cleaned.loc[20, "is_zero_volume"] is True or cleaned.loc[20, "is_zero_volume"] == 1
    assert cleaned.loc[15, "is_zero_volume"] is False or cleaned.loc[15, "is_zero_volume"] == 0

    # Suspicious zero volume with non-zero return flagged
    assert cleaned.loc[10, "is_zero_volume_nonzero_return"] is False or cleaned.loc[10, "is_zero_volume_nonzero_return"] == 0
    assert cleaned.loc[20, "is_zero_volume_nonzero_return"] is True or cleaned.loc[20, "is_zero_volume_nonzero_return"] == 1

    # Original prices and volume are preserved intact
    assert cleaned.loc[10, "volume"] == 0
    assert cleaned.loc[20, "volume"] == 0


def test_stale_price_streaks_and_resets():
    """Verifies backward-looking streak counting and resets upon price movements."""
    validator = DataValidator(stale_price_threshold=3)
    closes = pd.Series([100.0, 100.0, 100.0, 100.0, 105.0, 105.0, 105.0])

    streaks = validator.calculate_stale_streaks(closes)
    expected_streaks = [1, 2, 3, 4, 1, 2, 3]
    assert streaks.tolist() == expected_streaks

    is_stale = streaks >= 3
    expected_stale = [False, False, True, True, False, False, True]
    assert is_stale.tolist() == expected_stale


def test_extreme_moves_and_corporate_action_vs_shock():
    """Verifies extreme move classification distinguishing corporate actions from market shocks."""
    validator = DataValidator(extreme_move_threshold=0.50)

    # 1. MOTILALOFS.NS bonus issue on 2024-01-01
    dates = pd.Series([pd.Timestamp("2023-12-29"), pd.Timestamp("2024-01-01")])
    returns = pd.Series([0.01, -0.7461])
    is_ext, is_corp, is_shock = validator.classify_extreme_moves("MOTILALOFS.NS", dates, returns)
    assert is_ext.tolist() == [False, True]
    assert is_corp.tolist() == [False, True]
    assert is_shock.tolist() == [False, False]

    # 2. PATANJALI.NS capital reduction on 2020-01-27
    dates = pd.Series([pd.Timestamp("2020-01-24"), pd.Timestamp("2020-01-27")])
    returns = pd.Series([0.0, -0.9493])
    is_ext, is_corp, is_shock = validator.classify_extreme_moves("PATANJALI.NS", dates, returns)
    assert is_ext.tolist() == [False, True]
    assert is_corp.tolist() == [False, True]
    assert is_shock.tolist() == [False, False]

    # 3. VEDL.NS demerger spin-off on 2026-04-30
    dates = pd.Series([pd.Timestamp("2026-04-29"), pd.Timestamp("2026-04-30")])
    returns = pd.Series([0.02, -0.6490])
    is_ext, is_corp, is_shock = validator.classify_extreme_moves("VEDL.NS", dates, returns)
    assert is_ext.tolist() == [False, True]
    assert is_corp.tolist() == [False, True]
    assert is_shock.tolist() == [False, False]

    # 4. YESBANK.NS RBI moratorium collapse on 2020-03-06
    dates = pd.Series([pd.Timestamp("2020-03-05"), pd.Timestamp("2020-03-06")])
    returns = pd.Series([0.25, -0.5611])
    is_ext, is_corp, is_shock = validator.classify_extreme_moves("YESBANK.NS", dates, returns)
    assert is_ext.tolist() == [False, True]
    assert is_corp.tolist() == [False, False]
    assert is_shock.tolist() == [False, True]

    # 5. YESBANK.NS bailout surge on 2020-03-17
    dates = pd.Series([pd.Timestamp("2020-03-16"), pd.Timestamp("2020-03-17")])
    returns = pd.Series([0.45, 0.5809])
    is_ext, is_corp, is_shock = validator.classify_extreme_moves("YESBANK.NS", dates, returns)
    assert is_ext.tolist() == [False, True]
    assert is_corp.tolist() == [False, False]
    assert is_shock.tolist() == [False, True]

    # 6. Generic unclassified spike
    dates = pd.Series([pd.Timestamp("2023-05-10"), pd.Timestamp("2023-05-11")])
    returns = pd.Series([0.01, 0.60])
    is_ext, is_corp, is_shock = validator.classify_extreme_moves("GENERIC.NS", dates, returns)
    assert is_ext.tolist() == [False, True]
    assert is_corp.tolist() == [False, False]
    assert is_shock.tolist() == [False, False]


def test_missing_benchmark_dates_and_fallback_behavior():
    """Verifies handling of missing benchmark sessions with zero future lookahead."""
    validator = DataValidator(min_valid_trading_days=5)

    stock_dates = pd.to_datetime(["2019-10-25", "2019-10-27", "2019-10-28", "2019-10-29"])
    stock_df = pd.DataFrame({
        "date": stock_dates,
        "ticker": "TEST.NS",
        "open": [100.0, 102.0, 101.0, 103.0],
        "high": [105.0, 104.0, 103.0, 106.0],
        "low": [98.0, 100.0, 99.0, 101.0],
        "close": [101.0, 102.0, 102.0, 104.0],
        "volume": [10000, 5000, 8000, 12000],
    })

    # Benchmark missing 2019-10-27 (Diwali Muhurat session)
    bm_raw = pd.DataFrame({
        "date": pd.to_datetime(["2019-10-25", "2019-10-28", "2019-10-29"]),
        "close": [11500.0, 11600.0, 11650.0],
    })
    bm_prep = validator.prepare_benchmark_series(bm_raw)

    cleaned = validator.clean_and_enrich_stock(stock_df, benchmark_df=bm_prep, ticker="TEST.NS")

    assert len(cleaned) == 4

    # 2019-10-27 (index 1) check:
    muhurat_row = cleaned.iloc[1]
    assert muhurat_row["is_benchmark_available"] is False or muhurat_row["is_benchmark_available"] == 0
    assert muhurat_row["is_muhurat_session"] is True or muhurat_row["is_muhurat_session"] == 1
    assert np.isnan(muhurat_row["benchmark_close"])
    assert np.isnan(muhurat_row["benchmark_return"])

    # Fallback close is forward-filled from 2019-10-25 (no future leakage!)
    assert muhurat_row["benchmark_close_fallback"] == 11500.0
    # Fallback return is 0.0
    assert muhurat_row["benchmark_return_fallback"] == 0.0

    # 2019-10-28 (index 2) check:
    regular_row = cleaned.iloc[2]
    assert regular_row["is_benchmark_available"] is True or regular_row["is_benchmark_available"] == 1
    assert regular_row["is_muhurat_session"] is False or regular_row["is_muhurat_session"] == 0
    assert regular_row["benchmark_close"] == 11600.0
    assert regular_row["benchmark_close_fallback"] == 11600.0


def test_duplicate_dates_and_invalid_ohlcv(synthetic_ohlcv_data):
    """Verifies that invalid OHLC bounds and nonpositive prices trigger is_valid_ohlcv=False."""
    validator = DataValidator(min_valid_trading_days=50)
    data = synthetic_ohlcv_data.copy()

    # High < Low inversion
    data.loc[10, "high"] = 50.0
    data.loc[10, "low"] = 100.0

    # Nonpositive price
    data.loc[20, "close"] = -1.0

    # Close > High violation
    data.loc[30, "close"] = data.loc[30, "high"] + 5.0

    # Negative volume
    data.loc[40, "volume"] = -500

    cleaned = validator.clean_and_enrich_stock(data, ticker="TEST.NS")

    assert len(cleaned) == len(synthetic_ohlcv_data)
    assert (cleaned.loc[10, "is_valid_ohlcv"] is False) or (cleaned.loc[10, "is_valid_ohlcv"] == 0)
    assert (cleaned.loc[20, "is_valid_ohlcv"] is False) or (cleaned.loc[20, "is_valid_ohlcv"] == 0)
    assert (cleaned.loc[30, "is_valid_ohlcv"] is False) or (cleaned.loc[30, "is_valid_ohlcv"] == 0)
    assert (cleaned.loc[40, "is_valid_ohlcv"] is False) or (cleaned.loc[40, "is_valid_ohlcv"] == 0)
    assert (cleaned.loc[15, "is_valid_ohlcv"] is True) or (cleaned.loc[15, "is_valid_ohlcv"] == 1)


def test_short_history_and_warmup_indicators():
    """Verifies tagging of short-history tickers (<200 rows) and initial warmup window rows."""
    validator = DataValidator(min_valid_trading_days=200)

    # 91 rows (like VAML.NS, VOGL.NS, VISL.NS)
    short_df = pd.DataFrame({
        "date": pd.date_range("2026-06-15", periods=91, freq="B"),
        "ticker": "VAML.NS",
        "open": np.full(91, 100.0, dtype="float32"),
        "high": np.full(91, 102.0, dtype="float32"),
        "low": np.full(91, 98.0, dtype="float32"),
        "close": np.full(91, 101.0, dtype="float32"),
        "volume": np.full(91, 10000, dtype="int64"),
    })

    cleaned_short = validator.clean_and_enrich_stock(short_df, ticker="VAML.NS", warmup_rows=80)
    assert len(cleaned_short) == 91
    assert cleaned_short["is_short_history"].all() is True or cleaned_short["is_short_history"].all() == 1
    # Warmup flag: rows 0..79 are True, rows 80..90 are False
    assert cleaned_short.loc[:79, "is_warmup"].all() is True or cleaned_short.loc[:79, "is_warmup"].all() == 1
    assert (~cleaned_short.loc[80:, "is_warmup"]).all() is True or (~cleaned_short.loc[80:, "is_warmup"]).all() == 1

    # 250 rows (regular full history)
    long_df = pd.DataFrame({
        "date": pd.date_range("2025-01-01", periods=250, freq="B"),
        "ticker": "RELIANCE.NS",
        "open": np.full(250, 1000.0, dtype="float32"),
        "high": np.full(250, 1020.0, dtype="float32"),
        "low": np.full(250, 980.0, dtype="float32"),
        "close": np.full(250, 1010.0, dtype="float32"),
        "volume": np.full(250, 50000, dtype="int64"),
    })
    cleaned_long = validator.clean_and_enrich_stock(long_df, ticker="RELIANCE.NS", warmup_rows=80)
    assert len(cleaned_long) == 250
    assert (~cleaned_long["is_short_history"]).all() is True or (~cleaned_long["is_short_history"]).all() == 1


def test_row_count_preservation_and_key_uniqueness(synthetic_ohlcv_data, synthetic_benchmark_data):
    """Verifies that enrichment never multiplies rows, preserves (date, ticker) uniqueness, and preserves raw prices."""
    validator = DataValidator(min_valid_trading_days=50)
    bm_prep = validator.prepare_benchmark_series(synthetic_benchmark_data)

    cleaned = validator.clean_and_enrich_stock(synthetic_ohlcv_data, benchmark_df=bm_prep, ticker="TEST.NS")

    # Exact row count preservation
    assert len(cleaned) == len(synthetic_ohlcv_data)

    # Unique (date, ticker)
    duplicates = cleaned.duplicated(subset=["date", "ticker"]).sum()
    assert duplicates == 0

    # Exact equality of raw numeric values (no clipping or alteration of raw prices)
    for col in ["open", "high", "low", "close", "volume"]:
        np.testing.assert_array_equal(cleaned[col].values, synthetic_ohlcv_data[col].values)

