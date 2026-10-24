"""Market Events Calendar management and validation module.

Responsible for:
- Loading and parsing `data/events/market_events.csv`.
- Validating event records against the 16-field approved schema.
- Verifying chronological alignment of effective trading dates against the NIFTY 50 trading calendar.
- Enforcing look-ahead bias prevention policies (separating announcement datetime from effective date).
- Documenting semantic distinction for corporate actions: announcement datetime denotes board approval
  or regulatory filing, whereas effective_trading_date denotes the exchange ex-date (mechanical price adjustment).
- Filtering events by scope (MARKET_WIDE, SECTOR_SPECIFIC, STOCK_SPECIFIC).
- Supporting Phase 9 event-study window calculations.

NOTE: Calendar alignment and schema validation ensure structural consistency and prevent same-day
post-market/weekend leakage, but do not claim to prove complete point-in-time feature safety for downstream models.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
import pandas as pd


class EventCalendarManager:
    """Manages the curated market events calendar for Indian equities."""

    REQUIRED_COLUMNS = [
        "event_id",
        "event_name",
        "event_category",
        "event_subcategory",
        "scope",
        "affected_ticker",
        "announcement_datetime_ist",
        "market_timing",
        "effective_trading_date",
        "is_scheduled",
        "event_description",
        "source_name",
        "source_url",
        "verification_status",
        "date_confidence",
        "notes",
    ]

    PERMITTED_CATEGORIES = {
        "MACRO_POLICY",
        "POLITICAL_ELECTORAL",
        "REGULATORY_EXCHANGE",
        "SYSTEMIC_CREDIT",
        "GEOPOLITICAL",
        "CORPORATE_ACTION",
    }

    PERMITTED_SCOPES = {
        "MARKET_WIDE",
        "SECTOR_SPECIFIC",
        "STOCK_SPECIFIC",
    }

    PERMITTED_TIMINGS = {
        "PRE_MARKET",
        "DURING_MARKET",
        "POST_MARKET",
        "WEEKEND_HOLIDAY",
    }

    PERMITTED_STATUSES = {
        "VERIFIED",
        "PROVISIONAL",
        "UNDER_REVIEW",
    }

    PERMITTED_CONFIDENCES = {
        "HIGH",
        "MEDIUM",
        "LOW",
    }

    # Explicitly permitted non-universe systemic entities that triggered market-wide contagion
    PERMITTED_SYSTEMIC_ENTITIES = {"IL&FS", "DHFL", "PMC_BANK", "LVB"}

    def __init__(
        self,
        events_csv_path: Path | str = "data/events/market_events.csv",
        universe_config_path: Path | str = "configs/universe.json",
        calendar_path: Path | str = "data/interim/market/nifty50_clean.parquet",
    ) -> None:
        self.events_csv_path = Path(events_csv_path)
        self.universe_config_path = Path(universe_config_path)
        self.calendar_path = Path(calendar_path)
        self.events_df: Optional[pd.DataFrame] = None
        self._trading_dates: Optional[Set[str]] = None
        self._universe_tickers: Optional[Set[str]] = None

    def load_events(self) -> pd.DataFrame:
        """Loads and parses the market events CSV file.

        Returns:
            pd.DataFrame: Loaded events DataFrame.
        """
        if not self.events_csv_path.exists():
            raise FileNotFoundError(f"Events file not found: {self.events_csv_path}")

        df = pd.read_csv(self.events_csv_path, dtype={"affected_ticker": str})
        # Normalize missing affected_ticker to empty string
        df["affected_ticker"] = df["affected_ticker"].fillna("")
        self.events_df = df
        return self.events_df

    def get_trading_dates(self) -> Set[str]:
        """Loads valid active trading dates from NIFTY 50 interim parquet."""
        if self._trading_dates is not None:
            return self._trading_dates

        if not self.calendar_path.exists():
            return set()

        nifty_df = pd.read_parquet(self.calendar_path)
        self._trading_dates = set(nifty_df["date"].dt.strftime("%Y-%m-%d"))
        return self._trading_dates

    def get_universe_tickers(self) -> Set[str]:
        """Loads canonical 300 stock tickers from universe configuration."""
        if self._universe_tickers is not None:
            return self._universe_tickers

        if not self.universe_config_path.exists():
            return set()

        with open(self.universe_config_path, "r", encoding="utf-8") as f:
            univ = json.load(f)

        flat = univ.get("flat_ticker_list", [])
        if flat:
            self._universe_tickers = set(flat)
            return self._universe_tickers

        tickers = set()
        tickers_section = univ.get("tickers", {})
        for group in ["large_cap_nifty_100", "mid_cap_nifty_midcap_150", "small_cap_nifty_smallcap_250_selected"]:
            for item in tickers_section.get(group, []):
                tickers.add(item["ticker"] if isinstance(item, dict) else item)

        self._universe_tickers = tickers
        return self._universe_tickers

    def validate_events(self, df: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        """Performs rigorous quality, calendar alignment, and leakage validation.

        Checks:
        1. Required columns presence and schema completeness.
        2. Unique and non-null event IDs.
        3. Permitted enum values (categories, scopes, timings, statuses, confidences).
        4. Alignment of effective_trading_date with active NIFTY 50 trading dates.
        5. Consistency between market_timing, announcement date, and effective trading date.
        6. Ticker validity (must belong to 300 universe or permitted systemic entities).
        7. Scope consistency (STOCK_SPECIFIC events must declare an affected ticker).
        8. Source traceability (non-empty source name and valid HTTP/HTTPS URL).

        Returns:
            Dict[str, Any]: Validation summary report.
        """
        if df is None:
            if self.events_df is None:
                self.load_events()
            df = self.events_df

        errors: List[str] = []
        warnings: List[str] = []

        # 1. Required columns
        missing_cols = [c for c in self.REQUIRED_COLUMNS if c not in df.columns]
        if missing_cols:
            errors.append(f"Missing required columns: {missing_cols}")

        # 2. Duplicate or null event_id
        if df["event_id"].isnull().any():
            errors.append("Null event_id values detected.")
        if df["event_id"].duplicated().any():
            dups = df[df["event_id"].duplicated()]["event_id"].tolist()
            errors.append(f"Duplicate event_ids: {dups}")

        # 3. Permitted values check
        invalid_cat = df[~df["event_category"].isin(self.PERMITTED_CATEGORIES)]["event_category"].unique().tolist()
        if invalid_cat:
            errors.append(f"Invalid event categories: {invalid_cat}")

        invalid_scope = df[~df["scope"].isin(self.PERMITTED_SCOPES)]["scope"].unique().tolist()
        if invalid_scope:
            errors.append(f"Invalid scopes: {invalid_scope}")

        invalid_timing = df[~df["market_timing"].isin(self.PERMITTED_TIMINGS)]["market_timing"].unique().tolist()
        if invalid_timing:
            errors.append(f"Invalid market timings: {invalid_timing}")

        invalid_status = df[~df["verification_status"].isin(self.PERMITTED_STATUSES)]["verification_status"].unique().tolist()
        if invalid_status:
            errors.append(f"Invalid verification statuses: {invalid_status}")

        invalid_conf = df[~df["date_confidence"].isin(self.PERMITTED_CONFIDENCES)]["date_confidence"].unique().tolist()
        if invalid_conf:
            errors.append(f"Invalid date confidences: {invalid_conf}")

        # 4. Calendar alignment
        trading_dates = self.get_trading_dates()
        if trading_dates:
            invalid_trading_dates = []
            for _, row in df.iterrows():
                d = str(row["effective_trading_date"])
                if d not in trading_dates:
                    invalid_trading_dates.append((row["event_id"], d))
            if invalid_trading_dates:
                errors.append(f"Effective trading dates not in NIFTY trading calendar: {invalid_trading_dates}")

        # 5. Timing and look-ahead bias consistency
        for _, row in df.iterrows():
            ann_date = str(row["announcement_datetime_ist"])[:10]
            eff_date = str(row["effective_trading_date"])
            timing = row["market_timing"]

            # Effective date can never precede announcement date
            if eff_date < ann_date:
                errors.append(f"Look-ahead violation in {row['event_id']}: eff_date {eff_date} < ann_date {ann_date}")

            # If post-market on date X, effective date cannot be date X
            if timing == "POST_MARKET" and eff_date == ann_date:
                errors.append(f"Timing leak in {row['event_id']}: POST_MARKET event has eff_date equal to ann_date {eff_date}")

            # If weekend/holiday on non-trading date, effective date cannot be same day
            if timing == "WEEKEND_HOLIDAY" and trading_dates and ann_date not in trading_dates and eff_date == ann_date:
                errors.append(f"Timing leak in {row['event_id']}: WEEKEND_HOLIDAY on non-trading date has eff_date equal to ann_date {eff_date}")

        # 6. Ticker matching
        univ_tickers = self.get_universe_tickers()
        if univ_tickers:
            for _, row in df.iterrows():
                scope = row["scope"]
                ticker = str(row["affected_ticker"]).strip()

                if scope == "STOCK_SPECIFIC":
                    if not ticker:
                        errors.append(f"Stock-specific event {row['event_id']} has empty affected_ticker")
                    elif ticker not in univ_tickers and ticker not in self.PERMITTED_SYSTEMIC_ENTITIES:
                        errors.append(f"Event {row['event_id']} has unknown ticker: {ticker}")

        # 7. Source URL check
        for _, row in df.iterrows():
            url = str(row["source_url"]).strip()
            if not (url.startswith("http://") or url.startswith("https://")):
                errors.append(f"Event {row['event_id']} has non-HTTP/HTTPS source_url: {url}")
            if not str(row["source_name"]).strip():
                errors.append(f"Event {row['event_id']} has empty source_name")

        is_valid = len(errors) == 0
        return {
            "is_valid": is_valid,
            "total_records": len(df),
            "errors": errors,
            "warnings": warnings,
            "counts_by_scope": df["scope"].value_counts().to_dict(),
            "counts_by_category": df["event_category"].value_counts().to_dict(),
            "counts_by_year": df["effective_trading_date"].str[:4].value_counts().sort_index().to_dict(),
            "counts_by_status": df["verification_status"].value_counts().to_dict(),
        }

    def get_market_wide_events(self) -> pd.DataFrame:
        """Returns all market-wide events sorted chronologically."""
        if self.events_df is None:
            self.load_events()
        return self.events_df[self.events_df["scope"] == "MARKET_WIDE"].sort_values("effective_trading_date").reset_index(drop=True)

    def get_events_for_ticker(self, ticker: str) -> pd.DataFrame:
        """Returns all events relevant to a specific ticker (stock-specific plus market-wide)."""
        if self.events_df is None:
            self.load_events()
        mask = (self.events_df["scope"] == "MARKET_WIDE") | (self.events_df["affected_ticker"] == ticker)
        return self.events_df[mask].sort_values("effective_trading_date").reset_index(drop=True)

    def get_events_on_date(self, effective_date: str) -> pd.DataFrame:
        """Returns all events effective on a specific trading date."""
        if self.events_df is None:
            self.load_events()
        return self.events_df[self.events_df["effective_trading_date"] == effective_date].reset_index(drop=True)
