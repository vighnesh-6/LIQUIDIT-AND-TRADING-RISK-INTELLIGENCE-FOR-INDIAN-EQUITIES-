"""Storage management module.

Responsible for:
- Idempotent Parquet read and write operations.
- Deduplication key enforcement on (date, ticker).
- Atomic writes via temporary files to avoid partial file corruption.
- Downcasting numeric columns to float32 for RAM and disk efficiency.
"""

from pathlib import Path
from typing import List, Optional
import os
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq


class StreamingParquetWriter:
    """Safely streams pyarrow Tables to a temp Parquet file and atomically replaces on close."""

    def __init__(self, dest_path: Path | str, schema: pa.Schema, compression: str = "snappy") -> None:
        self.dest_path = Path(dest_path)
        self.dest_path.parent.mkdir(parents=True, exist_ok=True)
        self.temp_path = self.dest_path.parent / f"{self.dest_path.stem}_{os.getpid()}_{id(self)}.tmp.parquet"
        self.writer = pq.ParquetWriter(self.temp_path, schema=schema, compression=compression)
        self.closed = False

    def write_table(self, table: pa.Table) -> None:
        """Appends a pyarrow Table chunk to the Parquet file."""
        self.writer.write_table(table)

    def write_dataframe(self, df: pd.DataFrame, schema: Optional[pa.Schema] = None) -> None:
        """Appends a pandas DataFrame chunk to the Parquet file."""
        table = pa.Table.from_pandas(df, schema=schema, preserve_index=False)
        self.write_table(table)

    def close(self) -> Path:
        """Closes the Parquet writer and atomically moves temp file to destination."""
        if not self.closed:
            self.writer.close()
            self.closed = True
            if self.temp_path.exists():
                self.temp_path.replace(self.dest_path)
        return self.dest_path

    def __enter__(self) -> "StreamingParquetWriter":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if not self.closed:
            self.writer.close()
            self.closed = True
            if exc_type is not None:
                if self.temp_path.exists():
                    try:
                        self.temp_path.unlink()
                    except OSError:
                        pass
            else:
                if self.temp_path.exists():
                    self.temp_path.replace(self.dest_path)


class StorageManager:
    """Handles Parquet storage operations with idempotency and atomic writes."""

    def __init__(self, base_data_dir: Path | str = "data") -> None:
        self.base_data_dir = Path(base_data_dir)

    def get_streaming_writer(
        self,
        dest_path: Path | str,
        schema: pa.Schema,
        compression: str = "snappy",
    ) -> StreamingParquetWriter:
        """Returns a StreamingParquetWriter instance for memory-efficient chunked writes."""
        return StreamingParquetWriter(dest_path, schema=schema, compression=compression)

    def write_parquet_atomic(
        self,
        df: pd.DataFrame,
        dest_path: Path | str,
        compression: str = "snappy",
    ) -> Path:
        """Writes DataFrame to a temp file and renames atomically to dest_path.

        Args:
            df: DataFrame to write.
            dest_path: Final target Parquet path.
            compression: Parquet compression codec (default: 'snappy').

        Returns:
            Path: Written file path.
        """
        dest = Path(dest_path)
        dest.parent.mkdir(parents=True, exist_ok=True)
        temp_path = dest.parent / f"{dest.stem}_{os.getpid()}_{id(df)}.tmp.parquet"

        # Downcast float64 to float32 for RAM & storage efficiency
        df_to_save = df.copy()
        for col in df_to_save.select_dtypes(include=["float64"]).columns:
            df_to_save[col] = df_to_save[col].astype("float32")

        try:
            df_to_save.to_parquet(temp_path, index=False, compression=compression)
            temp_path.replace(dest)
        finally:
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except OSError:
                    pass

        return dest

    def read_parquet(self, src_path: Path | str, columns: Optional[List[str]] = None) -> pd.DataFrame:
        """Reads Parquet file with optional column pruning for memory efficiency.

        Args:
            src_path: Parquet file path.
            columns: Optional list of columns to load.

        Returns:
            pd.DataFrame: Loaded DataFrame.
        """
        src = Path(src_path)
        if not src.exists():
            raise FileNotFoundError(f"Parquet file not found: {src}")
        return pd.read_parquet(src, columns=columns)

    def upsert_records(
        self,
        existing_path: Path | str,
        new_df: pd.DataFrame,
        dedup_keys: List[str] = ["date", "ticker"],
    ) -> pd.DataFrame:
        """Appends new records and deduplicates based on keys.

        Args:
            existing_path: Path to current Parquet file.
            new_df: Incoming batch of records.
            dedup_keys: Unique composite key.

        Returns:
            pd.DataFrame: Deduplicated integrated DataFrame.
        """
        dest = Path(existing_path)
        if dest.exists() and dest.stat().st_size > 0:
            existing_df = self.read_parquet(dest)
            combined = pd.concat([existing_df, new_df], ignore_index=True)
        else:
            combined = new_df.copy()

        # Ensure dedup keys exist
        valid_keys = [k for k in dedup_keys if k in combined.columns]
        if valid_keys:
            deduped = combined.drop_duplicates(subset=valid_keys, keep="last")
            if "date" in deduped.columns:
                deduped = deduped.sort_values(by="date", ascending=True).reset_index(drop=True)
        else:
            deduped = combined.reset_index(drop=True)

        self.write_parquet_atomic(deduped, dest)
        return deduped

    def is_file_valid(self, path: Path | str) -> bool:
        """Checks if file exists and has non-zero size."""
        p = Path(path)
        return p.exists() and p.is_file() and p.stat().st_size > 0
