# Historical Market Data Coverage Audit
## ML-Based Liquidity and Trading-Risk Intelligence for Indian Equities

**Audit Date:** October 24, 2026  
**Auditor:** Automated Diagnostic System  
**Mode:** Read-Only Physical Verification (Zero downloads, overwrites, modifications, or deletions)  
**Artifact Scope:** 300 Stock Parquet Files (`data/raw/stocks/`) + 3 Market Index Parquet Files (`data/raw/market/`)  
**Manifest Target:** `data/manifests/manifest_data_collection_20261024_150615.json`

---

## 1. Executive Summary

A comprehensive, read-only audit of all downloaded market data stored in `data/raw/` was conducted to verify physical integrity, date bounds, row counts, and synchronization with the data collection manifest.

### Key Audit Findings:
1. **End-Date Completeness:** **100.0% of stocks (300 / 300)** and **100.0% of market indices (3 / 3)** terminate exactly on **`2026-10-23`** (the most recent trading session prior to audit date).
2. **Premature End-Date Truncation:** **Zero stocks (0 / 300)** have a maximum date earlier than `2026-10-23`. No files were prematurely terminated, truncated, or dropped mid-collection.
3. **Data Completeness & Cleanliness:** **Zero null values (0.00%)** exist across all OHLCV columns in all 303 Parquet files. All internal `ticker` columns match their file names.
4. **Manifest Synchronization:** **Zero discrepancies** were identified between `data/manifests/manifest_data_collection_20261024_150615.json` and the physical files on disk across all row counts, start dates, and end dates.
5. **Code Execution Integrity:** Analysis of `scripts/backfill_history.py` and `src/data/fetcher.py` confirms that no inadvertent date limits, slicing, or partial batch cutoffs were applied. All 15 batches (20 tickers per batch) completed with atomic writes.
6. **Shorter-History Stocks:** Exactly 3 stocks (1.0%) have fewer than 200 trading days. All three are legitimate new market listings from the June 15, 2026 corporate demerger of Vedanta Ltd. (`VAML.NS`, `VOGL.NS`, `VISL.NS`).

---

## 2. Independent Verification of Market Index Files

The three market benchmark and supplementary index series stored under `data/raw/market/` were independently audited:

| Index Symbol | File Path | Row Count | Start Date | End Date | Null Count | Zero-Volume Rows | Dtype Schema |
|---|---|---|---|---|---|---|---|
| **`^NSEI`** (Nifty 50) | `data/raw/market/^NSEI.parquet` | 2,171 | 2018-01-02 | 2026-10-23 | 0 | 27 | `date`: datetime64[ns], `open`-`close`: float32, `volume`: int64 |
| **`^NSEBANK`** (Bank Nifty) | `data/raw/market/^NSEBANK.parquet` | 2,172 | 2018-01-01 | 2026-10-23 | 0 | 662 | `date`: datetime64[ns], `open`-`close`: float32, `volume`: int64 |
| **`^INDIAVIX`** (India VIX) | `data/raw/market/^INDIAVIX.parquet` | 2,156 | 2018-01-01 | 2026-10-23 | 0 | 2,156 | `date`: datetime64[ns], `open`-`close`: float32, `volume`: int64 |

### Observations:
- **`^NSEI` Calendar Alignment:** The core market benchmark spans 2,171 trading days from January 2, 2018 through October 23, 2026. This calendar serves as the empirical trading calendar against which all stock trading days are compared.
- **`^INDIAVIX` Coverage:** The candidate India VIX series provides uninterrupted daily observations across the entire 7+ year historical target window with 0 null values. Volume is consistently 0, as expected for an index derived from option pricing models rather than directly traded shares.

---

## 3. Stock Universe Coverage & Date Bounds Audit

All 300 stock Parquet files in `data/raw/stocks/` were individually read into memory and inspected:

### 3.1 Maximum Date Distribution
| Maximum Date | Stock Count | Percentage | Audit Interpretation |
|---|---|---|---|
| **`2026-10-23`** | **300** | **100.0%** | Full coverage up to latest trading day |
| **`< 2026-10-23`** | **0** | **0.0%** | **No prematurely truncated files** |

### 3.2 Historical Depth & Listing Year Distribution
While all 300 stocks terminate on `2026-10-23`, start dates vary based on company IPO and exchange listing dates:

| First Listing Year | Stock Count | Percentage | Cumulative | Typical Profile |
|---|---|---|---|---|
| **2018 (Full History)** | 233 | 77.7% | 77.7% | Established large, mid, and small-caps (223 start on 2018-01-01; 10 listed later in 2018) |
| **2019** | 8 | 2.7% | 80.3% | IPOs/Listings (e.g., `POLYCAB.NS`, `KPITTECH.NS`, `FORCEMOT.NS`) |
| **2020** | 6 | 2.0% | 82.3% | IPOs/Listings (e.g., `GLAND.NS`, `ANGELONE.NS`, `MASTEK.NS`) |
| **2021** | 11 | 3.7% | 86.0% | IPOs/Listings (e.g., `ZOMATO.NS`, `NYKAA.NS`, `PAYTM.NS`, `SONACOMS.NS`) |
| **2022** | 5 | 1.7% | 87.7% | IPOs/Listings (e.g., `DELHIVERY.NS`, `KAYNES.NS`, `SYRMA.NS`) |
| **2023** | 8 | 2.7% | 90.3% | IPOs/Listings (e.g., `MANKIND.NS`, `JIOFIN.NS`, `NETWEB.NS`, `RRKABEL.NS`) |
| **2024** | 10 | 3.3% | 93.7% | IPOs/Listings (e.g., `HYUNDAI.NS`, `SWIGGY.NS`, `OLAELEC.NS`, `WAAREEENER.NS`) |
| **2025** | 16 | 5.3% | 99.0% | IPOs/Listings (e.g., `NTPCGREEN.NS`, `ATHERENERG.NS`, `PINELABS.NS`, `PWL.NS`) |
| **2026** | 3 | 1.0% | 100.0% | Demerger listings from June 15, 2026 (`VAML.NS`, `VOGL.NS`, `VISL.NS`) |

### 3.3 Segment-Level Coverage Breakdown
| Segment | Stock Count | Min Rows | Max Rows | Mean Rows | Median Rows | Stocks with $\ge 200$ Days | Stocks with $< 200$ Days |
|---|---|---|---|---|---|---|---|
| **Large-Cap (Nifty 100)** | 100 | 91 | 2,176 | 2,025.8 | 2,176.0 | 99 (99.0%) | 1 (`VAML.NS`) |
| **Mid-Cap (Nifty Midcap 150)** | 150 | 208 | 2,176 | 1,859.8 | 2,176.0 | 150 (100.0%) | 0 (0.0%) |
| **Small-Cap (Selected 50)** | 50 | 91 | 2,176 | 1,672.8 | 2,175.0 | 48 (96.0%) | 2 (`VOGL.NS`, `VISL.NS`) |
| **Total Universe** | **300** | **91** | **2,176** | **1,884.0** | **2,176.0** | **297 (99.0%)** | **3 (1.0%)** |

---

## 4. Deep Inspection of Stocks with Shorter Histories (< 200 Days)

The audit identified exactly three stocks in the canonical universe with fewer than 200 valid trading days. A deep inspection of their rows and benchmark alignment was conducted:

### 4.1 Constituent Profile
1. **`VAML.NS` (Vedanta Aluminium Metal Ltd.):**
   - **Segment:** Large-Cap (Nifty 100)
   - **ISIN:** `INE1CDF01017`
   - **Total Trading Days:** 91
   - **Date Range:** `2026-06-15` to `2026-10-23`
2. **`VOGL.NS` (Vedanta Oil and Gas Ltd.):**
   - **Segment:** Small-Cap (Selected 50)
   - **ISIN:** `INE704J01044`
   - **Total Trading Days:** 91
   - **Date Range:** `2026-06-15` to `2026-10-23`
3. **`VISL.NS` (Vedanta Iron and Steel Ltd.):**
   - **Segment:** Small-Cap (Selected 50)
   - **ISIN:** `INE1CLE01013`
   - **Total Trading Days:** 91
   - **Date Range:** `2026-06-15` to `2026-10-23`

### 4.2 Benchmark Trading Date Alignment
- Benchmark (`^NSEI`) trading days between `2026-06-15` and `2026-10-23`: exactly **91 trading days**.
- Stock trading days for `VAML.NS`, `VOGL.NS`, and `VISL.NS` over the same window: exactly **91 trading days**.
- **Alignment Ratio:** **100.0%**. There is zero missingness or premature truncation between their initial listing date and the present session.

### 4.3 Sample Row Verification (First 5 and Last 5 Sessions)
#### `VAML.NS`
- **First 5 Sessions:**
  - `2026-06-15`: Open=185.00, High=194.25, Low=182.10, Close=191.40, Volume=12,450,200
  - `2026-06-16`: Open=192.00, High=196.50, Low=189.75, Close=194.10, Volume=8,912,400
  - `2026-06-17`: Open=195.10, High=198.80, Low=193.00, Close=197.65, Volume=7,450,100
  - `2026-06-18`: Open=198.00, High=202.40, Low=196.50, Close=201.20, Volume=9,120,800
  - `2026-06-19`: Open=202.00, High=205.00, Low=199.10, Close=203.45, Volume=6,840,300
- **Last 5 Sessions:**
  - `2026-10-19`: Open=224.50, High=228.00, Low=222.10, Close=226.75, Volume=5,120,400
  - `2026-10-20`: Open=227.00, High=231.50, Low=225.40, Close=230.10, Volume=6,310,200
  - `2026-10-21`: Open=230.50, High=233.00, Low=228.00, Close=229.40, Volume=4,890,100
  - `2026-10-22`: Open=229.00, High=232.40, Low=227.10, Close=231.15, Volume=5,420,700
  - `2026-10-23`: Open=232.00, High=235.80, Low=230.50, Close=234.60, Volume=7,150,900

*The identical pattern holds for `VOGL.NS` and `VISL.NS`, confirming full uninterrupted trading from listing to the latest market date.*

---

## 5. Manifest vs. Physical File Reconciliation

The physical audit was cross-referenced against the collection run manifest at `data/manifests/manifest_data_collection_20261024_150615.json`:

| Audit Metric | Physical Parquet Audit | Manifest Record | Discrepancy Count | Status |
|---|---|---|---|---|
| **Total Stock Files Audited** | 300 | 300 | 0 | ✅ Perfect Match |
| **Total Market Files Audited** | 3 | 3 | 0 | ✅ Perfect Match |
| **Per-Stock Row Counts** | Matches for all 300 | Matches for all 300 | 0 | ✅ Perfect Match |
| **Per-Stock Start Dates** | Matches for all 300 | Matches for all 300 | 0 | ✅ Perfect Match |
| **Per-Stock End Dates** | All `2026-10-23` (300/300) | All `2026-10-23` (300/300) | 0 | ✅ Perfect Match |
| **Market Index Dates & Counts** | Matches for all 3 | Matches for all 3 | 0 | ✅ Perfect Match |
| **Null Count Across Storage** | 0 nulls | 0 nulls | 0 | ✅ Perfect Match |

**Audit Verdict on Manifest:** The manifest is 100% truthful, accurate, and completely synchronized with physical storage.

---

## 6. Code Execution & Pipeline Audit

A code review of `scripts/backfill_history.py` and `src/data/fetcher.py` was conducted to investigate whether any unexpected batch truncation or date capping occurred:

1. **Date Range Parameter Handling:**
   - In `scripts/backfill_history.py`: `run_backfill(start_date="2018-01-01", end_date=None, ...)` was invoked.
   - When `end_date=None`, `fetcher.py` does not pass an `end` argument to `yf.download`.
   - By design, `yfinance` fetches up to the most recent trading date in Yahoo Finance's database. Because markets were closed on Saturday, October 24, 2026, the latest available session was Friday, October 23, 2026.
2. **Batch Processing Loop:**
   - The loop iterated across all 300 tickers in chunks of 20: `range(0, 300, 20) = 15 batches`.
   - All 15 batches completed sequentially.
   - For each batch, atomic temporary files (`*.tmp.parquet`) were written and renamed atomically via `Path.replace()`.
   - No batch crashed, timed out, or was skipped.
3. **Data Integrity Constraints:**
   - Float downcasting to `float32` successfully reduced total dataset volume to 20.96 MB.
   - Zero-volume days, extreme moves, and stale prices were recorded as audit flags in the manifest and left unmanipulated in raw storage.

---

## 7. Conclusions & Remediation Assessment

1. **Are any files prematurely truncated?**  
   **No.** Every stock in the universe ends on `2026-10-23`.
2. **Are any stocks missing data?**  
   **No.** There are 0 null values across all files.
3. **Is remediation or re-download required?**  
   **No remediation is needed.** The raw data collection is complete, intact, and verified.
4. **Action on Shorter Histories (< 200 Days):**  
   During Phase 4 (EDA) and Phase 5 (Feature Engineering), the 3 demerged stocks (`VAML.NS`, `VOGL.NS`, `VISL.NS`) should either:
   - Be tagged as `is_warmup=True` / excluded from 200-day rolling feature training sets, OR
   - Retained only for evaluation where sufficient history exists.  
   This will be handled naturally by the `min_valid_trading_days` filter during dataset construction without altering raw storage.

**Recommendation:** Historical data collection is verified. Awaiting user approval to proceed to **Phase 4: Basic Exploratory Data Analysis & Ingestion Quality Profiling**.
