# DEPLOYMENT AND DAILY REFRESH
## ML-Based Liquidity and Trading-Risk Intelligence for Indian Equities

**Version:** 1.0
**Status:** Design Document — Pre-Implementation

---

## 1. Core Deployment Principle

The deployed system must fetch the latest available daily market data itself. It cannot depend on manual data downloads. This requirement is addressed through a **local scheduled pipeline** running on the user's Windows laptop.

**Important distinction:** A deployed Streamlit app is a visualization frontend, NOT a scheduler. The Streamlit app reads data; it cannot trigger data downloads or model scoring on a schedule. These tasks require a separate scheduled job that runs independently of whether the dashboard is open.

---

## 2. Local vs. Cloud Scheduling: Comparison

| Dimension | Local (Windows Task Scheduler) | Cloud (e.g., GitHub Actions, AWS Lambda) |
|---|---|---|
| **Cost** | Free | Free tier limited; may incur costs for longer runs |
| **Setup complexity** | Low; native Windows tool | Moderate; requires cloud account and configuration |
| **Data persistence** | Local SSD; always available | Remote storage (S3, GCS) required; adds latency |
| **Model artifact access** | Direct local file access | Artifacts must be uploaded/downloaded from storage |
| **Internet dependency** | Required only for yfinance fetch | Always required |
| **Laptop dependency** | Must be powered on at scheduled time | Independent of laptop state |
| **Reliability** | Moderate; laptop must be on and awake | High; cloud runs regardless of user state |
| **Latency** | ~8-20 min pipeline on local hardware | Similar or faster on cloud VM |
| **Data privacy** | Data stays local | Data uploaded to cloud |
| **Terms of Service risk** | yfinance ToS: personal use | yfinance ToS: uploading to cloud may raise ToS questions |

### Decision: Local Windows Task Scheduler for Initial Deployment

**Rationale:**
- Keeps data local (no ToS risk for personal academic use).
- No cloud infrastructure cost.
- Sufficient reliability for an academic project (not a commercial system).
- Simple to set up and maintain.
- Data and model artifacts are immediately accessible to the Streamlit dashboard.

**Cloud option is documented as a future extension.** If the user requires 24/7 availability or remote access to the dashboard, a lightweight cloud deployment (e.g., Streamlit Cloud for the frontend + GitHub Actions for the scheduler) can be layered on top.

---

## 3. Local Scheduler Architecture

### Scheduled Job Configuration

```
Tool:            Windows Task Scheduler
Trigger:         Daily at 17:30 IST (5:30 PM Indian Standard Time)
Rationale:       NSE closes at 15:30 IST. Yahoo Finance typically updates
                 Indian stock data within 1-2 hours of market close.
                 A 2-hour buffer (17:30) provides adequate time for data
                 to be available. If data is still unavailable, the pipeline
                 implements fallback behavior.

Entry point:     scripts/daily_refresh.bat
Action:          Start program → daily_refresh.bat
Start in:        C:\path\to\liquidity-risk-intelligence\
Run on missed:   YES — "Run task as soon as possible after a scheduled
                 start is missed" must be enabled.
Power condition: Uncheck "Start only if on AC power" (laptop may be on battery)
```

### Batch Script: scripts/daily_refresh.bat

```batch
@echo off
REM ============================================================
REM  LiqRisk-India Daily Refresh Pipeline
REM  Triggered by Windows Task Scheduler at 17:30 IST
REM ============================================================

REM Navigate to project root (absolute path required for Task Scheduler)
cd /d C:\path\to\liquidity-risk-intelligence\

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Run the Python orchestrator
python scripts/daily_pipeline_runner.py

REM Deactivate environment
deactivate
```

### Python Orchestrator: scripts/daily_pipeline_runner.py

Calls `src/pipeline/daily_pipeline.py` with the following steps:

1. **Health check:** Verify model artifacts exist; verify configs are readable.
2. **Determine target date:** Identify the most recent trading day for which data is not yet in the raw Parquet file.
3. **Fetch data:** Download only the missing date range (incremental). If today is not yet available, fetch yesterday's data (fallback).
4. **Validate:** Run quality checks on new rows only.
5. **Append to clean dataset:** Idempotent upsert — skip if date already exists.
6. **Feature engineering:** Compute features for new rows (requires sufficient history from existing clean dataset).
7. **LRS computation:** Compute Composite LRS for new rows.
8. **Score with saved model:** Load model artifact; generate HRE_prob and anomaly score.
9. **Write predictions:** Append new scored rows to `data/predictions/scored_YYYYMMDD.parquet`.
10. **Write manifest:** Record run timestamp, success/failure status, failed tickers, quality metrics.
11. **Log:** Write detailed log to `logs/pipeline_YYYYMMDD.log`.

---

## 4. Persistent Storage Design

### Data Storage Schema

All data is stored locally on the laptop SSD. The `data/` directory is the single source of truth.

```
data/
├── raw/
│   └── ohlcv_raw.parquet           -- Cumulative raw OHLCV for all tickers + dates
│                                      Append-only; never overwrite historical rows
├── interim/
│   ├── stocks/
│   │   └── ohlcv_clean.parquet     -- Validated, deduplicated clean stock dataset
│   └── market/                     -- Cleaned market indices (Nifty 50, Bank Nifty, India VIX)
├── processed/
│   └── features_full.parquet       -- Full feature matrix; updated incrementally
├── predictions/
│   └── scored_full.parquet         -- All scored rows; updated incrementally
│                                      Key: (date, ticker) — unique, idempotent
└── manifests/
    ├── manifest_20241001.json
    ├── manifest_20241002.json
    └── ...
```

### Idempotent Update Rule

The primary key for all data files is **(date, ticker)**. On each daily run:

1. New rows with a (date, ticker) combination not already present are appended.
2. Existing (date, ticker) rows are NEVER overwritten automatically.
3. If a re-download is forced (e.g., data quality issue discovered), the affected rows are explicitly flagged and updated in a separate "correction" step, not silently overwritten.

This design ensures:
- A crash mid-pipeline does not corrupt existing data.
- Running the pipeline twice on the same day does not create duplicates.
- Historical data is preserved even if a ticker is later excluded from the universe.

### Atomic Write Protocol

1. All Parquet writes go to a temporary file first: `data/raw/ohlcv_raw.parquet.tmp`.
2. On successful completion, the temp file is renamed to the target path (atomic rename on Windows SSD).
3. If the pipeline crashes during write, the `.tmp` file is detected on next run and cleaned up, leaving the original file intact.

---

## 5. Failure Recovery

### Failure Scenarios and Responses

| Failure Type | Detection | Response |
|---|---|---|
| **Ticker returns empty DataFrame** | Empty df check in fetcher.py | Log failed ticker; continue pipeline; record in manifest |
| **HTTP 429 (rate limit)** | HTTP error code | Retry with exponential backoff (1s, 2s, 4s, 8s, max 5 retries); if all fail, skip ticker and log |
| **yfinance API completely down** | All tickers fail | Abort pipeline; write manifest with FULL_FAILURE status; display warning on dashboard |
| **Market data not yet updated** (data is N-1 days old) | Most recent date in downloaded data < expected date | Log warning; use N-1 data; set `data_lag_days=1` in manifest |
| **Model artifact missing** | File existence check in health_check.py | Abort scoring step; compute LRS only; write partial predictions; alert user |
| **Corrupt Parquet file** | Read exception on startup | Restore from last-known-good backup (daily backup of clean Parquet recommended) |
| **Disk space exhaustion** | df.info() check before write | Alert user via log; halt pipeline |
| **Missing dates (exchange holiday)** | Date not in expected trading calendar | Skip fetch for that date; no action required |

### Graceful Degradation Principle

The pipeline is designed to produce SOME useful output even under partial failure:
- If 20% of tickers fail, the remaining 80% are scored and predictions are written.
- If the model scoring step fails (missing artifact), LRS is still computed and written.
- If feature engineering fails for one stock, that stock is skipped and logged; others continue.

**The pipeline must NEVER abort silently or leave data in a corrupted state.**

---

## 6. Freshness Monitoring

### In the Dashboard

`app/pages/5_Data_Quality.py` will display:

```
Last Successful Update: 2025-10-22 17:42:13 IST
Data Coverage: 287 / 300 tickers updated today
Failed Tickers: YESBANK.NS, VAKRANGEE.NS (logged in manifest)
Data Lag: 0 days (current)

⚠️ WARNING: Data is 2 days old. Last update was 2025-10-20.
   Check pipeline logs for details.
```

**Staleness thresholds:**
- 0-1 trading days: GREEN — normal.
- 2 trading days: YELLOW — warn user; may be weekend/holiday.
- 3+ trading days: RED — pipeline likely failed; user must investigate.

### Data Lag Definition

"Data lag" is defined as the number of trading days between today and the most recent date in the predictions file. This is distinct from calendar days and accounts for weekends and market holidays.

---

## 7. Fallback Behavior

### When Today's Data Is Not Yet Available

Yahoo Finance may not update Indian stock data until several hours after NSE closes (15:30 IST). If the pipeline runs at 17:30 IST and today's data is not yet available:

1. **Check most recent date in yfinance response** for any 3 pilot tickers.
2. If most recent date < today: set `fetch_mode = 'use_yesterday'`; fetch up to yesterday.
3. Log warning: "Today's data not yet available; predictions based on data through YYYY-MM-DD."
4. Dashboard displays: "⚠️ Predictions as of: [yesterday's date]. Today's data not yet available."

### When the Previous Day's Data Is Also Missing

This indicates a market holiday or a prolonged yfinance outage:

1. Check whether the missing date is a known NSE holiday (holidays list in `configs/`).
2. If holiday: skip silently; log "No data expected (holiday): YYYY-MM-DD."
3. If not holiday and data still missing after 24 hours: escalate to RED status in dashboard.

---

## 8. Cloud Deployment (Future Extension)

The following cloud option is documented for future use but is NOT part of the initial implementation:

### Option A: Streamlit Cloud (Frontend) + GitHub Actions (Scheduler)

```
GitHub Actions Schedule:
  - cron: '0 12 * * 1-5'  # 12:00 UTC = 17:30 IST, weekdays only
  Steps:
    - checkout repo
    - install dependencies
    - run daily_pipeline_runner.py
    - commit updated predictions Parquet to repo or push to cloud storage
  
Streamlit Cloud:
  - Connects to GitHub repo
  - Reads Parquet files (from repo or cloud storage bucket)
  - Provides public URL for dashboard access
```

**Risk:** GitHub Actions free tier limits (2,000 minutes/month); yfinance ToS applies to cloud environments; storing Parquet files in a public repo violates Yahoo Finance ToS.

**Recommendation:** Only pursue cloud deployment after academic submission. For the project, local scheduling is sufficient.

---

## 9. Schedule: What the Scheduler Does NOT Do

- **Does NOT guarantee intraday real-time data.** Yahoo Finance provides daily OHLCV; all predictions are based on end-of-day prices. There is a minimum 2-hour lag after market close.
- **Does NOT retrain models daily.** Model retraining is an offline operation run manually every few months or when performance degrades.
- **Does NOT update the stock universe automatically.** Universe changes require manual review and version increment.
- **Does NOT push data to any external server.** All data stays on the local machine.

---

## 10. Operational Testing Checklist

Before considering the daily refresh system operational:

- [ ] Task Scheduler successfully runs `daily_refresh.bat` without user interaction.
- [ ] Pipeline completes for at least 5 consecutive trading days without failure.
- [ ] Manifest files are created daily and contain expected fields.
- [ ] Duplicate rows are NOT created when pipeline is run twice on the same day.
- [ ] Failed ticker simulation: injecting an invalid ticker causes a log entry, not a crash.
- [ ] Network disconnect simulation: disconnecting internet mid-fetch causes graceful abort with log.
- [ ] Dashboard shows correct "last updated" time matching the manifest.
- [ ] Staleness warning appears correctly when predictions are > 2 trading days old.
- [ ] Atomic write: killing the process mid-write does not corrupt existing Parquet files.
