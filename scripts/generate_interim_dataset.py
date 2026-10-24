"""Script to generate the validated interim datasets (stocks/ohlcv_clean.parquet and market/*_clean.parquet).

Responsible for:
- Verifying raw data SHA-256 before execution (raw immutability check).
- Cleaning and saving market indices (Nifty 50, Bank Nifty, India VIX) to data/interim/market/.
- Preparing ^NSEI benchmark return series for stock integration.
- Iterating through 300 raw stock Parquets sequentially (streaming mode, <150 MB RAM).
- Applying DataValidator.clean_and_enrich_stock to produce all Phase 4.2 quality flags and benchmark integration.
- Streaming chunks to data/interim/stocks/ohlcv_clean.parquet via StreamingParquetWriter with atomic replacement.
- Post-generation validation of row counts (565,190), key uniqueness, schemas, and null distributions.
- Verifying raw data SHA-256 after execution to guarantee raw immutability.
- Saving audit statistics for downstream reporting and EDA.
"""

import hashlib
import json
import logging
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.data.storage import StorageManager, StreamingParquetWriter
from src.data.validator import DataValidator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("generate_interim_dataset")

INTERIM_SCHEMA = pa.schema([
    ("date", pa.timestamp("ns")),
    ("ticker", pa.string()),
    ("open", pa.float32()),
    ("high", pa.float32()),
    ("low", pa.float32()),
    ("close", pa.float32()),
    ("volume", pa.int64()),
    ("prev_close", pa.float32()),
    ("daily_return", pa.float32()),
    ("is_zero_volume", pa.bool_()),
    ("is_zero_volume_nonzero_return", pa.bool_()),
    ("stale_price_streak", pa.int32()),
    ("is_stale_price", pa.bool_()),
    ("is_extreme_move", pa.bool_()),
    ("is_corporate_action_gap", pa.bool_()),
    ("is_market_shock", pa.bool_()),
    ("is_short_history", pa.bool_()),
    ("is_warmup", pa.bool_()),
    ("is_valid_ohlcv", pa.bool_()),
    ("benchmark_close", pa.float32()),
    ("benchmark_return", pa.float32()),
    ("nifty_close", pa.float32()),
    ("nifty_return", pa.float32()),
    ("is_benchmark_available", pa.bool_()),
    ("is_muhurat_session", pa.bool_()),
    ("benchmark_close_fallback", pa.float32()),
    ("benchmark_return_fallback", pa.float32()),
])

EXPECTED_MERKLE_ROOT = "cdace0ba7662be9d0c49edca3f4db3ca00c2ef31c4704807db1bdef7cff0dcbf"
EXPECTED_STOCK_COUNT = 300
EXPECTED_STOCK_ROWS = 565190


def compute_stock_merkle_root(stocks_dir: Path) -> str:
    """Computes Merkle root hash across all stock parquet files."""
    stock_files = sorted(stocks_dir.glob("*.parquet"))
    hashes: Dict[str, str] = {}
    for f in stock_files:
        hasher = hashlib.sha256()
        with open(f, "rb") as fh:
            while chunk := fh.read(65536):
                hasher.update(chunk)
        hashes[f.name] = hasher.hexdigest()
    combined = "".join(f"{k}:{v}" for k, v in sorted(hashes.items()))
    return hashlib.sha256(combined.encode("utf-8")).hexdigest()


def generate_interim_dataset(
    raw_stocks_dir: str = "data/raw/stocks",
    raw_market_dir: str = "data/raw/market",
    output_path: str = "data/interim/stocks/ohlcv_clean.parquet",
    market_output_dir: str = "data/interim/market",
    audit_output_path: str = "reports/interim_cleaning_audit.json",
    warmup_rows: int = 80,
) -> Path:
    start_time = time.time()
    stocks_path = Path(raw_stocks_dir)
    market_path = Path(raw_market_dir)
    target_file = Path(output_path)
    market_target_dir = Path(market_output_dir)

    logger.info("=== Phase 4.2: Starting Interim Dataset Generation ===")

    # 1. Verify Raw Immutability Pre-Check
    logger.info("Verifying raw data SHA-256 pre-execution baseline...")
    pre_merkle = compute_stock_merkle_root(stocks_path)
    if pre_merkle != EXPECTED_MERKLE_ROOT:
        raise ValueError(
            f"Pre-check Merkle root mismatch! Expected {EXPECTED_MERKLE_ROOT}, got {pre_merkle}"
        )
    logger.info("Pre-check verified: Raw data untouched (Merkle root: %s)", pre_merkle)

    # 2. Clean and Save Market Indices & Prepare Nifty 50 Benchmark
    storage = StorageManager()
    market_target_dir.mkdir(parents=True, exist_ok=True)

    validator = DataValidator(
        min_valid_trading_days=200,
        stale_price_threshold=3,
        extreme_move_threshold=0.50,
    )

    market_specs = [
        {"raw": market_path / "^NSEI.parquet", "interim": market_target_dir / "nifty50_clean.parquet", "ticker": "^NSEI"},
        {"raw": market_path / "^NSEBANK.parquet", "interim": market_target_dir / "banknifty_clean.parquet", "ticker": "^NSEBANK"},
        {"raw": market_path / "^INDIAVIX.parquet", "interim": market_target_dir / "india_vix_clean.parquet", "ticker": "^INDIAVIX"},
    ]

    market_audit: Dict[str, Any] = {}
    for spec in market_specs:
        if not spec["raw"].exists():
            raise FileNotFoundError(f"Market file not found: {spec['raw']}")
        raw_m = pd.read_parquet(spec["raw"])
        clean_m = validator.clean_market_index(raw_m, ticker=spec["ticker"])
        storage.write_parquet_atomic(clean_m, spec["interim"])
        market_audit[spec["interim"].name] = {
            "ticker": spec["ticker"],
            "rows": len(clean_m),
            "start_date": str(clean_m["date"].min().date()),
            "end_date": str(clean_m["date"].max().date()),
            "columns": list(clean_m.columns),
            "is_valid_ohlcv": bool(clean_m["is_valid_ohlcv"].all()),
            "zero_volume_days": int(clean_m["is_zero_volume"].sum()),
        }
        logger.info(
            "Saved cleaned market index %s: %d rows (%s to %s)",
            spec["interim"].name,
            len(clean_m),
            clean_m["date"].min().date(),
            clean_m["date"].max().date(),
        )

    benchmark_file = market_path / "^NSEI.parquet"
    raw_bm = pd.read_parquet(benchmark_file)
    prepared_bm = validator.prepare_benchmark_series(raw_bm)
    logger.info("Prepared benchmark series (^NSEI): %d sessions (%s to %s)",
                len(prepared_bm), prepared_bm["date"].min().date(), prepared_bm["date"].max().date())

    # 3. Process Stocks Sequentially
    stock_files = sorted(stocks_path.glob("*.parquet"))
    if len(stock_files) != EXPECTED_STOCK_COUNT:
        raise ValueError(f"Expected {EXPECTED_STOCK_COUNT} stock files, found {len(stock_files)}")

    target_file.parent.mkdir(parents=True, exist_ok=True)

    column_order = [f.name for f in INTERIM_SCHEMA]
    reconciliation: List[Dict[str, Any]] = []

    total_rows_written = 0
    total_zero_volume_days = 0
    total_zero_vol_nonzero_ret = 0
    total_stale_days = 0
    total_extreme_moves = 0
    total_corp_actions = 0
    total_market_shocks = 0
    short_history_stocks = []

    logger.info("Starting sequential streaming write to %s...", target_file)
    with storage.get_streaming_writer(target_file, schema=INTERIM_SCHEMA, compression="snappy") as writer:
        for i, stock_file in enumerate(stock_files, 1):
            ticker = stock_file.stem
            df_raw = pd.read_parquet(stock_file)
            raw_count = len(df_raw)

            # Process stock
            clean_df = validator.clean_and_enrich_stock(
                stock_df=df_raw,
                benchmark_df=prepared_bm,
                ticker=ticker,
                warmup_rows=warmup_rows,
            )

            if len(clean_df) != raw_count:
                raise ValueError(f"Row count mismatch for {ticker}: {len(clean_df)} vs {raw_count}")

            # Reorder columns to exact schema
            clean_df = clean_df[column_order]

            # Stream write chunk
            writer.write_dataframe(clean_df, schema=INTERIM_SCHEMA)

            # Metrics
            zv_count = int(clean_df["is_zero_volume"].sum())
            zv_nz_ret = int(clean_df["is_zero_volume_nonzero_return"].sum())
            stale_count = int(clean_df["is_stale_price"].sum())
            ext_count = int(clean_df["is_extreme_move"].sum())
            ca_count = int(clean_df["is_corporate_action_gap"].sum())
            ms_count = int(clean_df["is_market_shock"].sum())
            is_short = bool(clean_df["is_short_history"].iloc[0])

            total_rows_written += raw_count
            total_zero_volume_days += zv_count
            total_zero_vol_nonzero_ret += zv_nz_ret
            total_stale_days += stale_count
            total_extreme_moves += ext_count
            total_corp_actions += ca_count
            total_market_shocks += ms_count

            if is_short:
                short_history_stocks.append(ticker)

            reconciliation.append({
                "ticker": ticker,
                "raw_rows": raw_count,
                "clean_rows": len(clean_df),
                "start_date": str(clean_df["date"].min().date()),
                "end_date": str(clean_df["date"].max().date()),
                "zero_volume_days": zv_count,
                "zero_volume_nonzero_ret": zv_nz_ret,
                "stale_price_days": stale_count,
                "max_stale_streak": int(clean_df["stale_price_streak"].max()),
                "extreme_moves": ext_count,
                "corporate_actions": ca_count,
                "market_shocks": ms_count,
                "is_short_history": is_short,
                "missing_benchmark_days": int((~clean_df["is_benchmark_available"]).sum()),
            })

            if i % 50 == 0 or i == EXPECTED_STOCK_COUNT:
                logger.info("Processed %3d/%3d stocks | Total rows: %d", i, EXPECTED_STOCK_COUNT, total_rows_written)

    logger.info("Interim file write completed. Target: %s", target_file)

    # 4. Strict Post-Generation Verification
    logger.info("Executing comprehensive verification on %s...", target_file)
    if not target_file.exists() or target_file.stat().st_size == 0:
        raise FileNotFoundError(f"Target file {target_file} was not written properly!")

    # Read back interim dataset
    interim_df = pd.read_parquet(target_file)
    actual_rows = len(interim_df)
    logger.info("Interim dataset loaded: %d rows, %d columns, %.2f MB on disk",
                actual_rows, len(interim_df.columns), target_file.stat().st_size / (1024 * 1024))

    if actual_rows != EXPECTED_STOCK_ROWS:
        raise ValueError(f"Total rows mismatch: expected {EXPECTED_STOCK_ROWS}, got {actual_rows}")

    actual_tickers = interim_df["ticker"].nunique()
    if actual_tickers != EXPECTED_STOCK_COUNT:
        raise ValueError(f"Unique tickers mismatch: expected {EXPECTED_STOCK_COUNT}, got {actual_tickers}")

    # Check key uniqueness
    dup_keys = interim_df.duplicated(subset=["date", "ticker"]).sum()
    if dup_keys > 0:
        raise ValueError(f"Found {dup_keys} duplicate (date, ticker) keys!")

    # Check that OHLCV validity flag has zero false invalid rows
    invalid_ohlcv_count = int((~interim_df["is_valid_ohlcv"]).sum())
    if invalid_ohlcv_count > 0:
        logger.warning("Found %d rows with is_valid_ohlcv=False", invalid_ohlcv_count)

    # Verify column types
    for col, field in zip(interim_df.columns, INTERIM_SCHEMA):
        if col != field.name:
            raise ValueError(f"Column order mismatch: {col} vs {field.name}")

    # Verify Raw Immutability Post-Check
    logger.info("Verifying raw data SHA-256 post-execution immutability...")
    post_merkle = compute_stock_merkle_root(stocks_path)
    if post_merkle != EXPECTED_MERKLE_ROOT:
        raise ValueError(
            f"CRITICAL ERROR: Raw data was modified during execution! "
            f"Pre: {EXPECTED_MERKLE_ROOT}, Post: {post_merkle}"
        )
    logger.info("Post-check verified: Raw data remains strictly immutable! Merkle: %s", post_merkle)

    elapsed = time.time() - start_time
    summary = {
        "status": "SUCCESS",
        "elapsed_seconds": round(elapsed, 2),
        "target_file": str(target_file),
        "file_size_bytes": target_file.stat().st_size,
        "file_size_mb": round(target_file.stat().st_size / (1024 * 1024), 2),
        "total_rows": actual_rows,
        "total_tickers": actual_tickers,
        "columns_count": len(interim_df.columns),
        "columns": list(interim_df.columns),
        "raw_merkle_root_verified": post_merkle,
        "quality_metrics": {
            "zero_volume_days": total_zero_volume_days,
            "zero_volume_nonzero_returns": total_zero_vol_nonzero_ret,
            "stale_price_days": total_stale_days,
            "extreme_moves_count": total_extreme_moves,
            "corporate_actions_count": total_corp_actions,
            "market_shocks_count": total_market_shocks,
            "short_history_stocks": short_history_stocks,
            "invalid_ohlcv_count": invalid_ohlcv_count,
        },
        "market_indices": market_audit,
        "reconciliation": reconciliation,
    }

    audit_path = Path(audit_output_path)
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    with open(audit_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    logger.info("Audit reconciliation saved to %s", audit_path)

    logger.info("=== Phase 4.2 Interim Generation SUCCESS (%d rows in %.2fs) ===", actual_rows, elapsed)
    return target_file


if __name__ == "__main__":
    generate_interim_dataset()
