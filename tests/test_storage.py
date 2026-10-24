"""Unit tests for StorageManager module (offline, temporary directory)."""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from src.data.storage import StorageManager


def test_storage_manager_initialization(tmp_path):
    """Verifies initialization and path configuration."""
    manager = StorageManager(base_data_dir=tmp_path)
    assert manager.base_data_dir == tmp_path


def test_write_parquet_atomic_and_downcast(tmp_path, synthetic_ohlcv_data):
    """Verifies that write_parquet_atomic writes file, downcasts float64 to float32, and cleans up temp files."""
    manager = StorageManager(base_data_dir=tmp_path)
    dest_path = tmp_path / "test_stock.parquet"

    # Make one float64 column to test downcasting
    df = synthetic_ohlcv_data.copy()
    df["open"] = df["open"].astype("float64")

    written_path = manager.write_parquet_atomic(df, dest_path)
    assert written_path.exists()
    assert written_path.stat().st_size > 0

    # Ensure no lingering temp files in directory
    temp_files = list(tmp_path.glob("*.tmp.parquet"))
    assert len(temp_files) == 0

    # Verify read back and downcasting
    loaded = pd.read_parquet(written_path)
    assert len(loaded) == len(df)
    assert loaded["open"].dtype == "float32"


def test_read_parquet_column_pruning(tmp_path, synthetic_ohlcv_data):
    """Verifies that read_parquet supports loading a subset of columns."""
    manager = StorageManager(base_data_dir=tmp_path)
    dest_path = tmp_path / "stock_prune.parquet"
    manager.write_parquet_atomic(synthetic_ohlcv_data, dest_path)

    loaded = manager.read_parquet(dest_path, columns=["date", "close", "volume"])
    assert list(loaded.columns) == ["date", "close", "volume"]
    assert len(loaded) == len(synthetic_ohlcv_data)


def test_upsert_records_deduplication(tmp_path, synthetic_ohlcv_data):
    """Verifies that upsert_records deduplicates on (date, ticker) and preserves latest values."""
    manager = StorageManager(base_data_dir=tmp_path)
    dest_path = tmp_path / "upsert_test.parquet"

    # Initial write of first 50 rows
    initial_batch = synthetic_ohlcv_data.iloc[:50].copy()
    manager.write_parquet_atomic(initial_batch, dest_path)

    # Overlapping batch: rows 40 to 60 (with modified close price for row 45)
    overlap_batch = synthetic_ohlcv_data.iloc[40:60].copy()
    overlap_batch.loc[overlap_batch.index[5], "close"] = 999.0

    upserted = manager.upsert_records(dest_path, overlap_batch, dedup_keys=["date", "ticker"])
    assert len(upserted) == 60

    # Verify deduplication kept the latest row
    updated_date = overlap_batch.iloc[5]["date"]
    matched = upserted[upserted["date"] == updated_date]
    assert len(matched) == 1
    assert matched["close"].values[0] == pytest.approx(999.0, abs=1e-2)


def test_read_parquet_nonexistent_file(tmp_path):
    """Verifies that reading a nonexistent parquet file raises FileNotFoundError."""
    manager = StorageManager(base_data_dir=tmp_path)
    with pytest.raises(FileNotFoundError):
        manager.read_parquet(tmp_path / "nonexistent.parquet")


def test_streaming_parquet_writer(tmp_path, synthetic_ohlcv_data):
    """Verifies that StreamingParquetWriter writes chunk-by-chunk and finalizes atomically."""
    import pyarrow as pa
    manager = StorageManager(base_data_dir=tmp_path)
    dest_path = tmp_path / "streamed.parquet"

    # Schema from DataFrame
    table_sample = pa.Table.from_pandas(synthetic_ohlcv_data.iloc[:5], preserve_index=False)
    schema = table_sample.schema

    chunk1 = synthetic_ohlcv_data.iloc[:40]
    chunk2 = synthetic_ohlcv_data.iloc[40:]

    with manager.get_streaming_writer(dest_path, schema=schema) as writer:
        writer.write_dataframe(chunk1, schema=schema)
        writer.write_dataframe(chunk2, schema=schema)

    assert dest_path.exists()
    assert dest_path.stat().st_size > 0
    # No lingering temp files
    assert len(list(tmp_path.glob("*.tmp.parquet"))) == 0

    loaded = pd.read_parquet(dest_path)
    assert len(loaded) == len(synthetic_ohlcv_data)
    assert list(loaded.columns) == list(synthetic_ohlcv_data.columns)

