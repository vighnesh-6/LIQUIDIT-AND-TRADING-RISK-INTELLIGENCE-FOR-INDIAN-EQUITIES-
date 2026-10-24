"""Data acquisition module.

Responsible for:
- Fetching historical and daily incremental OHLCV data via `yfinance`.
- Downloading Nifty 50 benchmark (`^NSEI`), Bank Nifty (`^NSEBANK`), and India VIX (`^INDIAVIX`).
- Enforcing exponential backoff, retry logic, and request rate-limiting.
- Gracefully handling failed tickers and logging failures into manifest metadata.
"""

import logging
import time
from typing import Any, Dict, List, Optional
import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)


class DataFetcher:
    """Acquires market data via yfinance with rate-limiting and retry logic."""

    def __init__(
        self,
        request_delay_seconds: float = 1.0,
        max_retries: int = 3,
        backoff_factor: float = 2.0,
        auto_adjust: bool = True,
    ) -> None:
        self.request_delay_seconds = request_delay_seconds
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.auto_adjust = auto_adjust

    def _normalize_ohlcv(self, raw_df: pd.DataFrame, ticker: str) -> pd.DataFrame:
        """Normalizes yfinance output DataFrame into standardized schema.

        Target columns: ['date', 'ticker', 'open', 'high', 'low', 'close', 'volume']
        """
        if raw_df is None or raw_df.empty:
            return pd.DataFrame(columns=["date", "ticker", "open", "high", "low", "close", "volume"])

        df = raw_df.copy()

        # Handle MultiIndex columns (common in yfinance >=0.2.36)
        if isinstance(df.columns, pd.MultiIndex):
            new_cols = []
            for col in df.columns:
                name = col[0] if isinstance(col, tuple) else str(col)
                new_cols.append(name.strip().lower())
            df.columns = new_cols
        else:
            df.columns = [str(c).strip().lower() for c in df.columns]

        # Reset index to extract date
        if "date" not in df.columns:
            df = df.reset_index()

        # Rename Date/Datetime to date
        for d_col in ["date", "datetime", "index", "Date"]:
            if d_col in df.columns:
                df = df.rename(columns={d_col: "date"})
                break

        # Standardize date format: tz-naive UTC normalized
        df["date"] = pd.to_datetime(df["date"]).dt.tz_localize(None)

        df["ticker"] = ticker

        # Ensure required OHLCV columns exist
        required = ["open", "high", "low", "close", "volume"]
        for col in required:
            if col not in df.columns:
                df[col] = float("nan")

        # Drop rows where close is NaN (non-trading days)
        df = df.dropna(subset=["close"]).copy()

        # Select and order columns
        df = df[["date", "ticker", "open", "high", "low", "close", "volume"]].copy()

        # Fill volume nulls with 0 and convert types
        df["volume"] = df["volume"].fillna(0).astype("int64")
        for col in ["open", "high", "low", "close"]:
            df[col] = df[col].astype("float32")

        # Sort and deduplicate
        df = df.drop_duplicates(subset=["date", "ticker"], keep="last")
        df = df.sort_values(by="date", ascending=True).reset_index(drop=True)

        return df

    def fetch_ticker_history(
        self,
        ticker: str,
        start_date: str,
        end_date: Optional[str] = None,
    ) -> pd.DataFrame:
        """Fetches OHLCV historical time series for a single ticker with retry and backoff.

        Args:
            ticker: Yahoo Finance ticker (e.g. 'RELIANCE.NS').
            start_date: YYYY-MM-DD start date.
            end_date: Optional YYYY-MM-DD end date.

        Returns:
            pd.DataFrame: Standardized OHLCV DataFrame.
        """
        current_delay = self.request_delay_seconds

        for attempt in range(1, self.max_retries + 1):
            try:
                kwargs = {
                    "tickers": ticker,
                    "start": start_date,
                    "auto_adjust": self.auto_adjust,
                    "progress": False,
                }
                if end_date:
                    kwargs["end"] = end_date

                raw = yf.download(**kwargs)

                if raw is not None and not raw.empty:
                    normalized = self._normalize_ohlcv(raw, ticker)
                    if not normalized.empty:
                        return normalized

                logger.warning(
                    f"Attempt {attempt}/{self.max_retries} returned empty data for {ticker}. "
                    f"Backing off for {current_delay:.1f}s."
                )
            except Exception as e:
                logger.warning(
                    f"Attempt {attempt}/{self.max_retries} failed for {ticker}: {e}. "
                    f"Backing off for {current_delay:.1f}s."
                )

            if attempt < self.max_retries:
                time.sleep(current_delay)
                current_delay *= self.backoff_factor

        logger.error(f"Exhausted all {self.max_retries} retries for ticker: {ticker}")
        return pd.DataFrame(columns=["date", "ticker", "open", "high", "low", "close", "volume"])

    def fetch_batch_history(
        self,
        tickers: List[str],
        start_date: str,
        end_date: Optional[str] = None,
        batch_size: int = 20,
    ) -> Dict[str, pd.DataFrame]:
        """Fetches batch of tickers in chunks of batch_size with delay to prevent rate limits.

        Args:
            tickers: List of ticker strings.
            start_date: Start date string.
            end_date: Optional end date string.
            batch_size: Number of tickers per batch.

        Returns:
            Dict[str, pd.DataFrame]: Dictionary mapping ticker -> OHLCV DataFrame.
        """
        results: Dict[str, pd.DataFrame] = {}

        for i in range(0, len(tickers), batch_size):
            chunk = tickers[i : i + batch_size]
            current_delay = self.request_delay_seconds
            raw_batch = None

            # Attempt batch download
            for attempt in range(1, self.max_retries + 1):
                try:
                    kwargs = {
                        "tickers": chunk,
                        "start": start_date,
                        "auto_adjust": self.auto_adjust,
                        "progress": False,
                    }
                    if end_date:
                        kwargs["end"] = end_date

                    raw_batch = yf.download(**kwargs)
                    if raw_batch is not None and not raw_batch.empty:
                        break
                except Exception as e:
                    logger.warning(f"Batch download attempt {attempt} failed: {e}")

                if attempt < self.max_retries:
                    time.sleep(current_delay)
                    current_delay *= self.backoff_factor

            # Extract per-ticker series from batch
            for ticker in chunk:
                ticker_df = pd.DataFrame()
                if raw_batch is not None and not raw_batch.empty:
                    try:
                        if isinstance(raw_batch.columns, pd.MultiIndex):
                            # MultiIndex format: (Price, Ticker)
                            cols = raw_batch.columns.levels[0]
                            # Find matching level
                            has_ticker = False
                            if "Ticker" in raw_batch.columns.names:
                                has_ticker = ticker in raw_batch.columns.get_level_values("Ticker")
                            else:
                                has_ticker = ticker in raw_batch.columns.get_level_values(1)

                            if has_ticker:
                                sub = pd.DataFrame(index=raw_batch.index)
                                for price_col in ["Open", "High", "Low", "Close", "Volume"]:
                                    if (price_col, ticker) in raw_batch.columns:
                                        sub[price_col.lower()] = raw_batch[(price_col, ticker)]
                                    elif price_col in raw_batch and ticker in raw_batch[price_col]:
                                        sub[price_col.lower()] = raw_batch[price_col][ticker]

                                sub = sub.dropna(subset=["close"]).reset_index()
                                sub = sub.rename(columns={sub.columns[0]: "date"})
                                sub["date"] = pd.to_datetime(sub["date"]).dt.tz_localize(None)
                                sub["ticker"] = ticker
                                ticker_df = self._normalize_ohlcv(sub, ticker)
                        else:
                            # Single ticker returned
                            ticker_df = self._normalize_ohlcv(raw_batch, ticker)
                    except Exception as e:
                        logger.warning(f"Failed to extract {ticker} from batch: {e}")

                # If extraction was empty, fall back to individual fetch
                if ticker_df.empty:
                    logger.info(f"Ticker {ticker} missing from batch, falling back to individual fetch...")
                    ticker_df = self.fetch_ticker_history(ticker, start_date=start_date, end_date=end_date)

                results[ticker] = ticker_df

            time.sleep(self.request_delay_seconds)

        return results

    def fetch_benchmark_history(
        self,
        benchmark_ticker: str = "^NSEI",
        start_date: str = "2018-01-01",
        end_date: Optional[str] = None,
    ) -> pd.DataFrame:
        """Fetches benchmark historical index data."""
        return self.fetch_ticker_history(benchmark_ticker, start_date=start_date, end_date=end_date)

    def fetch_vix_history(
        self,
        vix_ticker: str = "^INDIAVIX",
        start_date: str = "2018-01-01",
        end_date: Optional[str] = None,
    ) -> pd.DataFrame:
        """Fetches India VIX data if candidate ticker is verified."""
        return self.fetch_ticker_history(vix_ticker, start_date=start_date, end_date=end_date)

    def fetch_index_history(
        self,
        index_ticker: str,
        start_date: str = "2018-01-01",
        end_date: Optional[str] = None,
    ) -> pd.DataFrame:
        """Fetches arbitrary index historical data (e.g. ^NSEBANK)."""
        return self.fetch_ticker_history(index_ticker, start_date=start_date, end_date=end_date)
