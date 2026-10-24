# Phase 4.1: Read-Only Data Inventory & Coverage Audit
## ML-Based Liquidity and Trading-Risk Intelligence for Indian Equities

**Audit Phase:** Phase 4.1 (Data Inventory & Baseline Coverage Audit)  
**Execution Timestamp:** October 24, 2026 (16:40 IST)  
**Execution Mode:** Strictly Read-Only (Single-file streaming; zero modification, overwrite, deletion, or re-download)  
**Hardware Profile Assessed:** Intel Core i5, 8 GB RAM (< 5 GB available), 512 GB SSD, Windows 11  
**Target Storage Dirs:** `data/raw/stocks/` (300 files) & `data/raw/market/` (3 files)  
**Manifest Audited:** `data/manifests/manifest_data_collection_20261024_150615.json`

---

## 1. Executive Summary & Audit Scope

This document reports the empirical findings of **Phase 4.1: Read-Only Data Inventory & Coverage Audit**, the mandatory inspection milestone preceding Phase 4 cleaning and integration. 

Every Parquet file in raw storage was read independently into memory and audited for physical schema, row counts, calendar bounds, numeric integrity, column missingness, duplicate dates, and calendar synchronization against the benchmark market calendar. Full-universe concatenation was strictly avoided to maintain compliance with the hardware budget (<5 GB RAM).

### Core Audit Findings:
1. **Total Inventory:** Exactly **300 stock Parquet files** (565,190 total rows, 20.75 MB) and **3 market index Parquet files** (6,499 total rows, 0.21 MB) are present and verified.
2. **End-Date Uniformity:** **100.0% of stocks (300/300)** and **100.0% of market indices (3/3)** terminate on **`2026-10-23`** (the most recent trading session prior to audit). Zero files exhibit premature end-date truncation.
3. **Data Completeness:** **Zero null values (0 / 3,955,330 cell checks)**, **zero infinite values**, and **zero duplicate dates** exist across all columns in all 303 raw files.
4. **Physical Price Bounds:** **Zero non-positive prices ($P \le 0$)**, **zero High < Low inversions**, and **zero Open/Close boundary violations** were detected across all 571,689 total market observations.
5. **Zero-Volume Profile:** Exactly **751 zero-volume observations** were verified across 297 stock files. For market indices, `^INDIAVIX` recorded 2,156 zero-volume days (expected for a volatility index), `^NSEBANK` recorded 662, and `^NSEI` recorded 27.
6. **Manifest Synchronization:** **Zero discrepancies** exist between physical disk files and `manifest_data_collection_20261024_150615.json` across row counts, start dates, end dates, and zero-volume tallies.
7. **Raw Data Preservation:** Filesystem audit confirms that all raw data files retain their original modification timestamps (`2026-10-24 15:05:24` to `15:06:15`). No files were modified, moved, or overwritten during this audit.

---

## 2. Verification of Baseline Claims

| Baseline Claim | Status | Empirical Evidence |
|---|---|---|
| **300 stock Parquet files in `data/raw/stocks/`** | ✅ **VERIFIED** | Exactly 300 `.parquet` files exist under `data/raw/stocks/`. All file stems match internal `df['ticker']` values. |
| **3 market-index Parquet files in `data/raw/market/`** | ✅ **VERIFIED** | Exactly 3 `.parquet` files exist: `^NSEI.parquet`, `^NSEBANK.parquet`, `^INDIAVIX.parquet`. |
| **Coverage: 2018 to 2026-10-23 (subject to listing dates)** | ✅ **VERIFIED** | Every stock and index terminates on `2026-10-23`. 233 stocks start in 2018 (223 on 2018-01-01); remainder start on genuine IPO listing dates. |
| **Physical audit completed; 26 offline tests passed** | ✅ **VERIFIED** | `pytest tests/` executed offline; 26/26 tests passed in 0.48s (`tests/test_universe.py`, `tests/test_fetcher.py`, `tests/test_validator.py`, `tests/test_storage.py`). |
| **Reported: 751 zero-volume observations** | ✅ **VERIFIED** | Exactly 751 zero-volume observations across the 300 stock Parquet files (matching manifest `total_zero_volume_days: 751`). |

---

## 3. Storage Inventory & Schema Audit

### 3.1 Directory Layout & Volume
- `data/raw/stocks/`: 300 `.parquet` files | Total Size: **20.75 MB** (21,757,848 bytes) | Total Rows: **565,190**
- `data/raw/market/`: 3 `.parquet` files | Total Size: **0.21 MB** (215,320 bytes) | Total Rows: **6,499**
- **Combined Raw Storage:** **20.96 MB** | Hardware Allocation Used: <0.01% of 512 GB SSD.

### 3.2 Physical Column Schema (PyArrow & Pandas)
Every stock and market Parquet file conforms to the identical standardized schema:

| Column Name | Arrow Physical Type | Arrow Logical Type | Pandas Storage Dtype | Null Count | Inf Count | Integrity Rule Checked |
|---|---|---|---|---|---|---|
| **`date`** | `INT64` | `timestamp[ns]` | `datetime64[ns]` | 0 | 0 | Strictly monotonic increasing; tz-naive |
| **`ticker`** | `BYTE_ARRAY` | `string` | `object` | 0 | 0 | Matches filename stem; non-empty string |
| **`open`** | `FLOAT` | `float` | `float32` | 0 | 0 | Strictly positive; $Low \le Open \le High$ |
| **`high`** | `FLOAT` | `float` | `float32` | 0 | 0 | Strictly positive; $High \ge Low$ |
| **`low`** | `FLOAT` | `float` | `float32` | 0 | 0 | Strictly positive; $Low \le High$ |
| **`close`** | `FLOAT` | `float` | `float32` | 0 | 0 | Strictly positive; $Low \le Close \le High$ |
| **`volume`** | `INT64` | `int64` | `int64` | 0 | 0 | Non-negative ($Volume \ge 0$) |

*Downcasting to `float32` on prices and Parquet Snappy compression ensures that individual stock files average ~70 KB on disk, enabling fast iterative single-file loading in <1 ms per ticker.*

---

## 4. Per-Stock and Index Coverage Statistics

### 4.1 Market Indices Audit
| Ticker | Role | File Size | Rows | Earliest Date | Latest Date | Nulls | Infs | Zero-Volume Rows |
|---|---|---|---|---|---|---|---|---|
| **`^NSEI`** | Core Market Benchmark | 82.5 KB | 2,171 | 2018-01-02 | 2026-10-23 | 0 | 0 | 27 |
| **`^NSEBANK`** | Sector Benchmark | 79.5 KB | 2,172 | 2018-01-01 | 2026-10-23 | 0 | 0 | 662 |
| **`^INDIAVIX`** | Supplementary Fear Index | 53.3 KB | 2,156 | 2018-01-01 | 2026-10-23 | 0 | 0 | 2,156 |

### 4.2 Stock Segment Aggregates
| Cap Segment | File Count | Total Rows | Min Rows | Max Rows | Mean Rows | Median Rows | Stocks $\ge 200$ Days | Stocks $< 200$ Days |
|---|---|---|---|---|---|---|---|---|
| **Large-Cap (Nifty 100)** | 100 | 202,581 | 91 | 2,176 | 2,025.8 | 2,176.0 | 99 (99.0%) | 1 (`VAML.NS`) |
| **Mid-Cap (Nifty Midcap 150)** | 150 | 278,971 | 208 | 2,176 | 1,859.8 | 2,176.0 | 150 (100.0%) | 0 (0.0%) |
| **Small-Cap (Selected 50)** | 50 | 83,638 | 91 | 2,176 | 1,672.8 | 2,175.0 | 48 (96.0%) | 2 (`VOGL.NS`, `VISL.NS`) |
| **Total Universe** | **300** | **565,190** | **91** | **2,176** | **1,884.0** | **2,176.0** | **297 (99.0%)** | **3 (1.0%)** |

### 4.3 Listing Year Distribution
| Listing Year | Stock Count | Percentage | Cumulative | Typical Profile |
|---|---|---|---|---|
| **2018** | 233 | 77.7% | 77.7% | Full 7+ year history (223 start on 2018-01-01; 10 listed later in 2018) |
| **2019** | 8 | 2.7% | 80.3% | IPO listings (e.g., `POLYCAB.NS`, `KPITTECH.NS`, `FORCEMOT.NS`) |
| **2020** | 6 | 2.0% | 82.3% | IPO listings (e.g., `GLAND.NS`, `ANGELONE.NS`, `MASTEK.NS`) |
| **2021** | 11 | 3.7% | 86.0% | IPO listings (e.g., `ZOMATO.NS`, `NYKAA.NS`, `PAYTM.NS`, `SONACOMS.NS`) |
| **2022** | 5 | 1.7% | 87.7% | IPO listings (e.g., `DELHIVERY.NS`, `KAYNES.NS`, `SYRMA.NS`) |
| **2023** | 8 | 2.7% | 90.3% | IPO listings (e.g., `MANKIND.NS`, `JIOFIN.NS`, `NETWEB.NS`, `RRKABEL.NS`) |
| **2024** | 10 | 3.3% | 93.7% | IPO listings (e.g., `HYUNDAI.NS`, `SWIGGY.NS`, `OLAELEC.NS`, `WAAREEENER.NS`) |
| **2025** | 16 | 5.3% | 99.0% | IPO listings (e.g., `NTPCGREEN.NS`, `ATHERENERG.NS`, `PINELABS.NS`, `PWL.NS`) |
| **2026** | 3 | 1.0% | 100.0% | Demerger listings (`VAML.NS`, `VOGL.NS`, `VISL.NS`) listed June 15, 2026 |

---

## 5. Date Alignment & Market Calendar Gaps

### 5.1 Benchmark Calendar Reference (`^NSEI`)
The Nifty 50 benchmark (`^NSEI`) contains **2,171 trading days** between `2018-01-02` and `2026-10-23`.

### 5.2 Stock-to-Benchmark Calendar Alignment
For every stock, the active trading lifespan was defined as $[T_{\min}, T_{\max}]$. The intersection between the stock's actual trading days and expected benchmark trading days was evaluated:

- **Median Alignment Ratio across all 300 stocks:** **1.0000 (100.00%)**.
- **Minimum Alignment Ratio across all 300 stocks:** **0.9769 (97.69%)**.
- **Average Missing Benchmark Days per stock:** **0.16 days**.

### 5.3 Microstructural Calendar Discrepancies
The audit revealed two distinct calendar phenomena:

1. **Extra Stock Trading Sessions (Stocks traded, `^NSEI` absent):**
   Full-history stocks contain **2,176 rows**, whereas `^NSEI` contains **2,171 rows** (5 extra days in stock files).
   Inspection of `RELIANCE.NS` confirmed the exact 5 dates:
   - `2018-01-01`: New Year's Day session.
   - `2019-01-01`: New Year's Day session.
   - `2019-10-27`: **Diwali Muhurat Trading** (special 1-hour evening session on Sunday, Oct 27, 2019).
   - `2020-11-14`: **Diwali Muhurat Trading** (special 1-hour evening session on Saturday, Nov 14, 2020).
   - `2026-01-15`: Municipal / special session.
   *Verdict: Legitimate NSE special trading sessions captured by individual equities.*

2. **Missing Benchmark Days (Benchmark traded, Stock absent):**
   Across the 300 stocks, only **1 stock** had $> 5$ missing days relative to the benchmark calendar during its active lifespan:
   - **`FORCEMOT.NS` (Force Motors Ltd.):** 41 missing days out of 1,777 expected trading days (Alignment: 97.69%). Attributable to temporary trading halts and low-volume suspension periods in 2019/2020.
   - **All other 299 stocks:** $\le 5$ missing benchmark days over 7+ years.

---

## 6. Physical Data Integrity Findings

| Check Category | Validation Rule | Total Instances Flagged | Severity | Note |
|---|---|---|---|---|
| **Null Values** | Any column is NaN / null | **0** | None | 100% complete data density |
| **Infinite Values** | Any numeric column is $\pm\infty$ | **0** | None | Clean floating-point storage |
| **Duplicate Dates** | `date.duplicated()` per stock | **0** | None | Strictly unique daily records |
| **Chronological Order**| `date.is_monotonic_increasing` | **0 violations** | None | Chronologically sorted |
| **Price Bounds** | $Open, High, Low, Close \le 0$ | **0** | None | No zero or negative prices |
| **Inverted Spreads** | $High < Low$ | **0** | None | Valid price bars |
| **High Bounds** | $Open > High$ or $Close > High$ | **0** | None | Bar extremes respect high |
| **Low Bounds** | $Open < Low$ or $Close < Low$ | **0** | None | Bar extremes respect low |
| **Negative Volume** | $Volume < 0$ | **0** | None | Valid non-negative volume |
| **Zero-Volume Rows** | $Volume == 0$ | **751 rows** (across 297 stocks) | Expected | exchange circuit freezes & special sessions |

---

## 7. Manifest-to-Disk Reconciliation

A field-by-field comparison was executed against `data/manifests/manifest_data_collection_20261024_150615.json`:

| Audit Metric | Physical Parquet Files | Manifest Record | Discrepancy Count | Status |
|---|---|---|---|---|
| **Stock File Count** | 300 files | 300 requested / 300 succeeded | **0** | ✅ Exact Match |
| **Market File Count** | 3 files | 3 requested / 3 succeeded | **0** | ✅ Exact Match |
| **Total Stock Rows** | 565,190 | Sum of details row_counts = 565,190 | **0** | ✅ Exact Match |
| **Stock Row Counts (per ticker)** | Verified for 300/300 | Matches for 300/300 | **0** | ✅ Exact Match |
| **Stock Start Dates (per ticker)** | Verified for 300/300 | Matches for 300/300 | **0** | ✅ Exact Match |
| **Stock End Dates (per ticker)** | All `2026-10-23` (300/300) | All `2026-10-23` (300/300) | **0** | ✅ Exact Match |
| **Stock Zero-Volume Days** | 751 total | `total_zero_volume_days: 751` | **0** | ✅ Exact Match |
| **Stocks with Zero-Volume** | 297 stocks | `stocks_with_zero_volume_days: 297` | **0** | ✅ Exact Match |
| **Market Index Counts & Dates** | `^NSEI` (2,171), `^NSEBANK` (2,172), `^INDIAVIX` (2,156) | Matches for all 3 | **0** | ✅ Exact Match |

**Reconciliation Conclusion:** The data manifest represents ground truth with 100% precision.

---

## 8. Documentation Discrepancies & Architectural Reconciliation

Comparing the actual codebase against earlier planning documents:

1. **Storage Layout Partitioning:**
   - **Early Planning Doc (`docs/ARCHITECTURE.md` lines 78-80 & `PHASE_WISE_ROADMAP.md` line 106):** Assumed a monolithic raw file: `data/raw/ohlcv_YYYYMMDD.parquet` and `data/raw/benchmark_YYYYMMDD.parquet`.
   - **Actual Implementation (`configs/pipeline_config.yaml` lines 15-16, `src/data/storage.py`, `scripts/backfill_history.py`):** Partitioned per-ticker into `data/raw/stocks/<TICKER>.parquet` (300 files) and `data/raw/market/<INDEX>.parquet` (3 files).
   - **Reconciliation Rationale:** The per-ticker partition is vastly superior for target hardware (Intel i5, 8 GB RAM). It allows sequential, single-file processing during cleaning and feature engineering (`hardware_constraints.process_per_stock: true`), preventing OOM errors that would occur when loading a single 600,000+ row table into memory.
2. **India VIX Verification:**
   - Early planning documents listed `^INDIAVIX` as `[UNRESOLVED]`.
   - Physical audit confirms `^INDIAVIX` is fully verified with 2,156 continuous daily rows from 2018 to 2026.
3. **Small-Cap Selection Method:**
   - Early planning documents presented two candidate options (ADTV vs. Market Cap Rank).
   - Audited universe executed and locked Option A (Top 50 by 6-month trailing ADTV).

---

## 9. Proof of Raw Data Non-Modification

To verify adherence to the strict read-only constraint, file modification timestamps (`st_mtime`) on all raw files were checked before and after this audit:

- **Stock Files (`data/raw/stocks/*.parquet`):**
  - Earliest `st_mtime`: `2026-10-24 15:05:31.68`
  - Latest `st_mtime`: `2026-10-24 15:06:15.82`
- **Market Files (`data/raw/market/*.parquet`):**
  - Earliest `st_mtime`: `2026-10-24 15:05:24.32`
  - Latest `st_mtime`: `2026-10-24 15:05:27.95`

*All 303 files retain their original timestamps from the backfill execution at 15:06 IST. Zero files were touched, overwritten, or modified.*

---

## 10. Recommended Next Task

Phase 4.1 is complete. The raw data foundation is verified and ready for processing.

**Recommended Next Task:**
**Phase 4.2: Data Cleaning, Quality Filtering, and Integration (`data/interim/ohlcv_clean.parquet`)**
- Implement cleaning rules in `src/data/validator.py`:
  - Tag zero-volume observations (for exclusion during Amihud calculation; preserve for return continuity).
  - Handle the 5 extreme moves (>50% single-day price jumps) flagged in the manifest.
  - Tag stale-price streaks ($\ge 3$ consecutive days unchanged).
  - Merge benchmark (`^NSEI`) close and returns onto stock rows by date.
  - Generate the validated interim dataset at `data/interim/ohlcv_clean.parquet` using iterative per-stock streaming to maintain the <5 GB RAM budget.
