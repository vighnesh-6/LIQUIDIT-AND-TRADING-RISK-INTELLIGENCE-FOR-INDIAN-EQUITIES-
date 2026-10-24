"""Historical data acquisition and backfill script.

Responsible for:
- One-time bulk acquisition of historical daily OHLCV for all 300 stocks in canonical universe.
- Downloading Nifty 50 benchmark (^NSEI), Bank Nifty (^NSEBANK), and India VIX (^INDIAVIX).
- Storing immutable raw snapshots to `data/raw/stocks/` and `data/raw/market/` in Parquet format.
- Executing ingestion data quality checks via `DataValidator`.
- Writing a comprehensive, truthful audit manifest to `data/manifests/`.
- Resumable and idempotent: skips already successfully downloaded and validated tickers unless --force is specified.
"""

import argparse
import datetime
import json
import logging
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import yfinance as yf

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.data.universe import UniverseManager
from src.data.fetcher import DataFetcher
from src.data.validator import DataValidator
from src.data.storage import StorageManager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("backfill_history")


def run_backfill(
    start_date: str = "2018-01-01",
    end_date: Optional[str] = None,
    batch_size: int = 20,
    delay: float = 1.0,
    force: bool = False,
    universe_config_path: str = "configs/universe.json",
    raw_stocks_dir: str = "data/raw/stocks",
    raw_market_dir: str = "data/raw/market",
    manifest_dir: str = "data/manifests",
) -> Path:
    """Executes the full historical market data acquisition workflow.

    Args:
        start_date: Historical start date string (YYYY-MM-DD).
        end_date: Optional end date string (YYYY-MM-DD).
        batch_size: Number of tickers downloaded per batch.
        delay: Delay in seconds between requests to avoid rate limits.
        force: If True, re-download already existing files.
        universe_config_path: Path to universe configuration JSON.
        raw_stocks_dir: Directory for stock Parquet files.
        raw_market_dir: Directory for market index Parquet files.
        manifest_dir: Directory for manifest JSON output.

    Returns:
        Path: Path to the generated manifest JSON file.
    """
    run_timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    start_perf = time.time()

    stocks_path = Path(raw_stocks_dir)
    market_path = Path(raw_market_dir)
    manifests_path = Path(manifest_dir)

    stocks_path.mkdir(parents=True, exist_ok=True)
    market_path.mkdir(parents=True, exist_ok=True)
    manifests_path.mkdir(parents=True, exist_ok=True)

    # Initialize modules
    universe_mgr = UniverseManager(config_path=universe_config_path)
    universe_val = universe_mgr.validate_universe()
    if not universe_val["is_valid"]:
        logger.error(f"Universe validation failed: {universe_val}")
        raise ValueError("Canonical universe in configs/universe.json failed validation.")

    all_stock_tickers = universe_mgr.get_all_tickers()
    segment_map = universe_mgr.get_segment_mapping()

    benchmark_ticker = universe_mgr.get_benchmark_ticker()  # ^NSEI
    bank_nifty_ticker = universe_mgr.get_bank_nifty_ticker()  # ^NSEBANK
    vix_ticker = universe_mgr.get_vix_candidate_ticker() or "^INDIAVIX"  # ^INDIAVIX

    market_tickers = [benchmark_ticker, bank_nifty_ticker, vix_ticker]

    fetcher = DataFetcher(request_delay_seconds=delay, max_retries=3, backoff_factor=2.0, auto_adjust=True)
    validator = DataValidator(min_valid_trading_days=200, stale_price_threshold=3, extreme_move_threshold=0.50)
    storage = StorageManager()

    logger.info("=" * 70)
    logger.info("STARTING HISTORICAL DATA ACQUISITION")
    logger.info(f"Target date range: {start_date} to {end_date or 'latest'}")
    logger.info(f"Stock universe: {len(all_stock_tickers)} stocks across 3 segments")
    logger.info(f"Market indices: {market_tickers}")
    logger.info(f"yfinance version: {yf.__version__}")
    logger.info("=" * 70)

    # Manifest accumulator
    manifest: Dict[str, Any] = {
        "manifest_type": "historical_data_collection",
        "run_timestamp_utc": run_timestamp,
        "requested_date_range": {
            "start_date": start_date,
            "end_date": end_date or "latest",
        },
        "environment": {
            "python_version": sys.version,
            "yfinance_version": yf.__version__,
            "pandas_version": pd.__version__,
        },
        "universe_metadata": {
            "source": "NSE Indices Limited (niftyindices.com)",
            "config_path": universe_config_path,
            "large_cap_count": universe_val["large_count"],
            "mid_cap_count": universe_val["mid_count"],
            "small_cap_count": universe_val["small_count"],
            "total_stocks_requested": len(all_stock_tickers),
        },
        "market_indices": {},
        "stocks": {
            "requested": len(all_stock_tickers),
            "succeeded": 0,
            "failed": 0,
            "skipped_resumed": 0,
            "details": {},
        },
        "quality_summary": {
            "stocks_with_warnings": 0,
            "stocks_with_zero_volume_days": 0,
            "stocks_with_stale_prices": 0,
            "stocks_with_extreme_moves": 0,
            "total_zero_volume_days": 0,
            "total_extreme_move_instances": 0,
            "total_stale_price_days": 0,
        },
        "storage_paths": {
            "stocks_dir": str(stocks_path),
            "market_dir": str(market_path),
        },
        "execution_duration_seconds": 0.0,
    }

    # 1. Download Market Indices
    logger.info("\n--- Phase 1: Acquiring Market Indices ---")
    benchmark_df: Optional[pd.DataFrame] = None

    for idx_ticker in market_tickers:
        dest_file = market_path / f"{idx_ticker}.parquet"
        logger.info(f"Processing index {idx_ticker}...")

        if not force and storage.is_file_valid(dest_file):
            logger.info(f"Index {idx_ticker} already exists at {dest_file}. Loading for validation.")
            df = storage.read_parquet(dest_file)
        else:
            df = fetcher.fetch_ticker_history(idx_ticker, start_date=start_date, end_date=end_date)
            if not df.empty:
                storage.write_parquet_atomic(df, dest_file)
            time.sleep(delay)

        validated_df, report = validator.validate_ticker_series(df, idx_ticker)
        manifest["market_indices"][idx_ticker] = {
            "status": "SUCCESS" if report["is_valid"] or report["row_count"] >= 200 else "FAILED",
            "file_path": str(dest_file),
            "row_count": report["row_count"],
            "start_date": report["start_date"],
            "end_date": report["end_date"],
            "null_counts": report["null_counts"],
            "zero_volume_days": report["zero_volume_days"],
            "warnings": report["warnings"],
        }

        if idx_ticker == benchmark_ticker and not validated_df.empty:
            benchmark_df = validated_df

        logger.info(
            f"Index {idx_ticker}: rows={report['row_count']}, "
            f"start={report['start_date']}, end={report['end_date']}, "
            f"status={manifest['market_indices'][idx_ticker]['status']}"
        )

    # 2. Download 300 Stocks in Batches
    logger.info("\n--- Phase 2: Acquiring 300 Stock Histories ---")
    succeeded_count = 0
    failed_count = 0
    skipped_resumed_count = 0

    total_stocks = len(all_stock_tickers)
    total_batches = (total_stocks + batch_size - 1) // batch_size

    for i in range(0, total_stocks, batch_size):
        batch = all_stock_tickers[i : i + batch_size]
        batch_num = (i // batch_size) + 1
        logger.info(f"\n[Batch {batch_num}/{total_batches}] Processing {len(batch)} tickers ({batch[0]} to {batch[-1]})...")

        pending_tickers = []
        for ticker in batch:
            dest_file = stocks_path / f"{ticker}.parquet"
            segment = segment_map.get(ticker, "unknown")

            if not force and storage.is_file_valid(dest_file):
                try:
                    df = storage.read_parquet(dest_file)
                    validated_df, report = validator.validate_ticker_series(df, ticker)
                    if report["row_count"] >= 200:
                        skipped_resumed_count += 1
                        succeeded_count += 1
                        logger.info(f"[{ticker}] (Resume) Loaded {report['row_count']} rows ({report['start_date']} to {report['end_date']})")
                        _record_stock_manifest(manifest, ticker, segment, str(dest_file), report, benchmark_df, validator)
                        continue
                except Exception as e:
                    logger.warning(f"[{ticker}] Existing file corrupted ({e}). Adding to download list.")

            pending_tickers.append(ticker)

        if pending_tickers:
            logger.info(f"Fetching batch of {len(pending_tickers)} pending tickers...")
            batch_data = fetcher.fetch_batch_history(
                pending_tickers,
                start_date=start_date,
                end_date=end_date,
                batch_size=len(pending_tickers),
            )

            for ticker in pending_tickers:
                dest_file = stocks_path / f"{ticker}.parquet"
                segment = segment_map.get(ticker, "unknown")
                df = batch_data.get(ticker, pd.DataFrame())

                if df.empty:
                    logger.error(f"[{ticker}] FAILED: Received empty data frame from yfinance.")
                    failed_count += 1
                    manifest["stocks"]["details"][ticker] = {
                        "segment": segment,
                        "status": "FAILED",
                        "file_path": None,
                        "row_count": 0,
                        "start_date": None,
                        "end_date": None,
                        "error": "Empty data returned after max retries",
                        "warnings": ["Download returned empty time series"],
                    }
                else:
                    validated_df, report = validator.validate_ticker_series(df, ticker)
                    storage.write_parquet_atomic(validated_df, dest_file)
                    succeeded_count += 1
                    logger.info(
                        f"[{ticker}] SUCCESS: {report['row_count']} rows "
                        f"({report['start_date']} to {report['end_date']}) | "
                        f"warnings={len(report['warnings'])}"
                    )
                    _record_stock_manifest(manifest, ticker, segment, str(dest_file), report, benchmark_df, validator)

        logger.info(f"Completed Batch {batch_num}/{total_batches}. Total Succeeded: {succeeded_count}, Failed: {failed_count}")

    # Finalize manifest statistics
    manifest["stocks"]["succeeded"] = succeeded_count
    manifest["stocks"]["failed"] = failed_count
    manifest["stocks"]["skipped_resumed"] = skipped_resumed_count
    manifest["execution_duration_seconds"] = round(time.time() - start_perf, 2)

    # Save manifest
    manifest_filename = f"manifest_data_collection_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    manifest_file_path = manifests_path / manifest_filename
    with open(manifest_file_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    logger.info("=" * 70)
    logger.info("DATA ACQUISITION COMPLETE")
    logger.info(f"Total stocks requested: {total_stocks}")
    logger.info(f"Total succeeded: {succeeded_count} (Resumed: {skipped_resumed_count}, Newly downloaded: {succeeded_count - skipped_resumed_count})")
    logger.info(f"Total failed: {failed_count}")
    logger.info(f"Execution duration: {manifest['execution_duration_seconds']} seconds")
    logger.info(f"Manifest written to: {manifest_file_path}")
    logger.info("=" * 70)

    return manifest_file_path


def _record_stock_manifest(
    manifest: Dict[str, Any],
    ticker: str,
    segment: str,
    file_path: str,
    report: Dict[str, Any],
    benchmark_df: Optional[pd.DataFrame],
    validator: DataValidator,
) -> None:
    """Helper to update manifest with per-stock report and aggregate quality counts."""
    manifest["stocks"]["details"][ticker] = {
        "segment": segment,
        "status": "SUCCESS" if report["row_count"] > 0 else "FAILED",
        "file_path": file_path,
        "row_count": report["row_count"],
        "start_date": report["start_date"],
        "end_date": report["end_date"],
        "has_minimum_history": report["has_minimum_history"],
        "null_counts": report["null_counts"],
        "nonpositive_prices": report["nonpositive_prices"],
        "zero_volume_days": report["zero_volume_days"],
        "extreme_moves_count": report["extreme_moves_count"],
        "extreme_move_dates": report["extreme_move_dates"],
        "stale_price_streaks": report["stale_price_streaks"],
        "stale_price_days": report["stale_price_days"],
        "max_stale_streak": report["max_stale_streak"],
        "warnings": report["warnings"],
    }

    # Quality aggregates
    qs = manifest["quality_summary"]
    if report["warnings"]:
        qs["stocks_with_warnings"] += 1
    if report["zero_volume_days"] > 0:
        qs["stocks_with_zero_volume_days"] += 1
        qs["total_zero_volume_days"] += report["zero_volume_days"]
    if report["extreme_moves_count"] > 0:
        qs["stocks_with_extreme_moves"] += 1
        qs["total_extreme_move_instances"] += report["extreme_moves_count"]
    if report["stale_price_streaks"] > 0:
        qs["stocks_with_stale_prices"] += 1
        qs["total_stale_price_days"] += report["stale_price_days"]


def main() -> None:
    parser = argparse.ArgumentParser(description="Acquire historical market data for 300 stocks and indices.")
    parser.add_argument("--start-date", type=str, default="2018-01-01", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", type=str, default=None, help="End date (YYYY-MM-DD)")
    parser.add_argument("--batch-size", type=int, default=20, help="Batch size for downloads")
    parser.add_argument("--delay", type=float, default=1.0, help="Delay in seconds between ticker downloads")
    parser.add_argument("--force", action="store_true", help="Force re-download even if files exist")
    parser.add_argument("--universe-config", type=str, default="configs/universe.json", help="Path to universe.json")

    args = parser.parse_args()

    run_backfill(
        start_date=args.start_date,
        end_date=args.end_date,
        batch_size=args.batch_size,
        delay=args.delay,
        force=args.force,
        universe_config_path=args.universe_config,
    )


if __name__ == "__main__":
    main()
