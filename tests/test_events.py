"""Unit and integration tests for Market Events Calendar and EventCalendarManager."""

from pathlib import Path
import pandas as pd
import pytest

from src.data.events import EventCalendarManager

EVENTS_CSV_PATH = Path("data/events/market_events.csv")
TEMPLATE_CSV_PATH = Path("data/events/market_events_template.csv")
CALENDAR_PATH = Path("data/interim/market/nifty50_clean.parquet")


def test_events_file_exists_and_non_empty():
    """Verifies that the canonical market_events.csv exists and contains substantial records."""
    assert EVENTS_CSV_PATH.exists(), f"Missing {EVENTS_CSV_PATH}"
    df = pd.read_csv(EVENTS_CSV_PATH)
    assert len(df) >= 70, f"Expected >= 70 events, got {len(df)}"


def test_template_preserved_unchanged():
    """Verifies that the original market_events_template.csv is preserved intact."""
    assert TEMPLATE_CSV_PATH.exists(), f"Missing {TEMPLATE_CSV_PATH}"
    assert TEMPLATE_CSV_PATH.stat().st_size == 3419, "Template file was modified!"


def test_events_validation_suite():
    """Runs full schema, calendar alignment, and look-ahead validation via EventCalendarManager."""
    manager = EventCalendarManager(
        events_csv_path=EVENTS_CSV_PATH,
        calendar_path=CALENDAR_PATH,
    )
    report = manager.validate_events()
    assert report["is_valid"] is True, f"Validation failed with errors: {report['errors']}"
    assert report["total_records"] >= 70


def test_events_schema_conformity():
    """Verifies all 16 required columns exist and match expected types."""
    df = pd.read_csv(EVENTS_CSV_PATH)
    expected_cols = [
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
    assert list(df.columns) == expected_cols


def test_events_unique_ids():
    """Verifies primary key uniqueness and ID formatting convention."""
    df = pd.read_csv(EVENTS_CSV_PATH)
    assert df["event_id"].nunique() == len(df)
    for eid in df["event_id"]:
        assert eid.startswith("EVT_")
        parts = eid.split("_")
        assert len(parts) == 3
        assert len(parts[1]) == 4  # Year YYYY
        assert parts[1].isdigit()


def test_events_calendar_alignment():
    """Verifies every effective_trading_date is a valid trading session in NIFTY 50 calendar."""
    if not CALENDAR_PATH.exists():
        pytest.skip("NIFTY 50 interim parquet not present")

    nifty_df = pd.read_parquet(CALENDAR_PATH)
    trading_dates = set(nifty_df["date"].dt.strftime("%Y-%m-%d"))

    df = pd.read_csv(EVENTS_CSV_PATH)
    for _, row in df.iterrows():
        eff_date = str(row["effective_trading_date"])
        assert eff_date in trading_dates, f"Event {row['event_id']} effective date {eff_date} not in NIFTY calendar!"


def test_events_leakage_and_timing_policy():
    """Verifies no look-ahead leakage in effective_trading_date assignment.

    Checks:
    1. Effective date can never precede announcement date.
    2. Post-market announcements cannot take effect on the same day's closing session.
    3. Weekend/holiday announcements on non-trading dates cannot take effect on that same day.
    4. Effective trading dates must align with active trading sessions.

    NOTE: These assertions verify metadata schema conformity and calendar consistency.
    They do NOT claim to prove complete point-in-time feature safety for downstream models,
    which requires pipeline-level feature leakage and lag verification.
    """
    if not CALENDAR_PATH.exists():
        pytest.skip("NIFTY 50 interim parquet not present")

    nifty_df = pd.read_parquet(CALENDAR_PATH)
    trading_dates = set(nifty_df["date"].dt.strftime("%Y-%m-%d"))

    df = pd.read_csv(EVENTS_CSV_PATH)
    for _, row in df.iterrows():
        ann_date = str(row["announcement_datetime_ist"])[:10]
        eff_date = str(row["effective_trading_date"])
        timing = row["market_timing"]

        # Effective date cannot precede announcement date
        assert eff_date >= ann_date, f"Event {row['event_id']} leaks future info: {eff_date} < {ann_date}"

        # Post-market announcement cannot take effect on the same day's close
        if timing == "POST_MARKET":
            assert eff_date > ann_date, f"Event {row['event_id']} post-market same-day leak: {eff_date} == {ann_date}"

        # Weekend or holiday announcements occurring on non-trading dates cannot have eff_date == ann_date
        if timing == "WEEKEND_HOLIDAY" and ann_date not in trading_dates:
            assert eff_date > ann_date, (
                f"Event {row['event_id']} weekend/holiday announcement on non-trading date {ann_date} "
                f"cannot take effect on the same day: {eff_date}"
            )


def test_events_remediated_specific_audit_cases():
    """Verifies specific remediation items for EVT_2020_003 and EVT_2025_001."""
    df = pd.read_csv(EVENTS_CSV_PATH)

    # EVT_2020_003: Saturday 2020 budget session omission documented, Monday preserved, MEDIUM confidence
    e2020 = df[df["event_id"] == "EVT_2020_003"].iloc[0]
    assert e2020["effective_trading_date"] == "2020-02-03"
    assert e2020["date_confidence"] == "MEDIUM", "EVT_2020_003 date_confidence must be MEDIUM due to session omission"
    assert "Saturday" in str(e2020["notes"])
    assert "omitted" in str(e2020["notes"])
    assert "2020-02-01" in str(e2020["announcement_datetime_ist"])
    assert e2020["source_url"] == "https://www.indiabudget.gov.in/budget2020-21/doc/budget_speech.pdf"

    # EVT_2025_001: Saturday 2025 budget classified as WEEKEND_HOLIDAY with calendar alignment rationale
    e2025 = df[df["event_id"] == "EVT_2025_001"].iloc[0]
    assert e2025["market_timing"] == "WEEKEND_HOLIDAY", "EVT_2025_001 timing must be WEEKEND_HOLIDAY for Saturday announcement"
    assert e2025["effective_trading_date"] == "2025-02-03"
    assert "WEEKEND_HOLIDAY" in str(e2025["notes"]) or "Saturday" in str(e2025["notes"])


def test_corporate_actions_ex_date_semantics():
    """Verifies that corporate actions document the distinction between announcement and ex-date semantics."""
    df = pd.read_csv(EVENTS_CSV_PATH)
    corp_actions = df[df["event_category"] == "CORPORATE_ACTION"]
    assert len(corp_actions) >= 10

    for _, row in corp_actions.iterrows():
        notes = str(row["notes"])
        assert "Announcement datetime reflects board approval/filing date" in notes or "ex-date" in notes.lower(), (
            f"Corporate action {row['event_id']} missing explicit announcement vs ex-date semantic note"
        )
        assert row["scope"] == "STOCK_SPECIFIC"
        assert str(row["affected_ticker"]).endswith(".NS")
        # Ex-date must be on or after announcement date
        ann_date = str(row["announcement_datetime_ist"])[:10]
        eff_date = str(row["effective_trading_date"])
        assert eff_date >= ann_date


def test_events_cross_year_coverage():
    """Verifies coverage across all project years 2018 through 2026."""
    df = pd.read_csv(EVENTS_CSV_PATH)
    years = df["effective_trading_date"].str[:4].unique().tolist()
    for y in ["2018", "2019", "2020", "2021", "2022", "2023", "2024", "2025", "2026"]:
        assert y in years, f"Missing event coverage for year {y}"


def test_events_scope_distribution():
    """Verifies presence of market-wide, sector-specific, and stock-specific corporate actions."""
    df = pd.read_csv(EVENTS_CSV_PATH)
    scopes = set(df["scope"].unique())
    assert "MARKET_WIDE" in scopes
    assert "SECTOR_SPECIFIC" in scopes
    assert "STOCK_SPECIFIC" in scopes

    # Check key corporate actions are present
    stock_events = df[df["scope"] == "STOCK_SPECIFIC"]
    stock_tickers = set(stock_events["affected_ticker"].dropna().unique())
    for expected_ticker in ["YESBANK.NS", "MOTILALOFS.NS", "PATANJALI.NS", "VEDL.NS", "RELIANCE.NS"]:
        assert expected_ticker in stock_tickers, f"Missing expected corporate action for {expected_ticker}"


def test_events_source_url_integrity():
    """Verifies all source URLs are valid HTTP/HTTPS and verification statuses are permitted."""
    df = pd.read_csv(EVENTS_CSV_PATH)
    for _, row in df.iterrows():
        url = str(row["source_url"]).strip()
        assert url.startswith("http://") or url.startswith("https://"), f"Bad URL in {row['event_id']}: {url}"
        assert len(str(row["source_name"]).strip()) > 0, f"Empty source_name in {row['event_id']}"
        assert row["verification_status"] in {"VERIFIED", "PROVISIONAL", "UNDER_REVIEW"}

    # Confirm verified source URLs exist and unresolved sources are honestly marked PROVISIONAL
    verified_count = (df["verification_status"] == "VERIFIED").sum()
    provisional_count = (df["verification_status"] == "PROVISIONAL").sum()
    assert verified_count >= 20, f"Expected at least 20 verified events, found {verified_count}"
    assert provisional_count >= 50, f"Expected unresolved generic sources marked PROVISIONAL, found {provisional_count}"
