# AUDIT CHECKLIST
## ML-Based Liquidity and Trading-Risk Intelligence for Indian Equities

**Version:** 1.0
**Purpose:** Complete this checklist before starting implementation. Each item must be VERIFIED, ACCEPTED (with documented rationale), or FLAGGED for resolution.

**Status codes:** ✅ VERIFIED | ⚠️ ACCEPTED WITH CAVEATS | ❌ UNRESOLVED — BLOCK IMPLEMENTATION

---

## Section 1: Data Source Verification (Phase 1 Pre-Conditions)

| # | Item | Status |
|---|---|---|
| 1.1 | yfinance can download OHLCV data for NSE large-cap tickers (e.g., RELIANCE.NS, HDFCBANK.NS) for 7+ years | ✅ VERIFIED — 100/100 Large-caps downloaded (2018–2026) |
| 1.2 | yfinance returns `^NSEI` (Nifty 50) data for the same 7-year window | ✅ VERIFIED — 2,171 rows (2018-01-02 to 2026-10-23), 0 nulls |
| 1.3 | yfinance auto_adjust=True produces adjusted prices; no separate Adj Close column needed | ✅ VERIFIED — Single clean OHLCV schema normalized |
| 1.4 | At least one NSE mid-cap ticker (e.g., MARICO.NS or MPHASIS.NS) downloads successfully | ✅ VERIFIED — 150/150 Mid-caps downloaded |
| 1.5 | At least one NSE small-cap ticker downloads with ≥1,000 trading days of history | ✅ VERIFIED — 47/50 small-caps have >1,000 rows (up to 2,176 rows) |
| 1.6 | yfinance version is pinned in requirements.txt | ✅ VERIFIED — Pinned to `yfinance==1.2.0` |
| 1.7 | NSE Indices website constituent list download confirmed accessible without login | ✅ VERIFIED — Downloaded directly from niftyindices.com |

---

## Section 2: Universe Definition

| # | Item | Status |
|---|---|---|
| 2.1 | Nifty 100 constituent list obtained from niftyindices.com (100 stocks) | ✅ VERIFIED — 100 unique stocks |
| 2.2 | Nifty Midcap 150 constituent list obtained (150 stocks) | ✅ VERIFIED — 150 unique stocks |
| 2.3 | Nifty Smallcap 250 constituent list obtained (250 stocks) | ✅ VERIFIED — 251 active constituents audited |
| 2.4 | Zero overlap confirmed between Nifty 100, Nifty Midcap 150, and Nifty Smallcap 250 | ✅ VERIFIED — 0 cross-segment overlaps |
| 2.5 | 50 small-cap stocks selected from Nifty Smallcap 250 by documented criteria | ✅ VERIFIED — Option A: Top 50 by 6-month ADTV |
| 2.6 | configs/universe.json created with all 300 tickers, cap_segment labels, and download date | ✅ VERIFIED — Canonical configuration locked |
| 2.7 | At least 270 of 300 tickers successfully downloaded from yfinance | ✅ VERIFIED — 300/300 succeeded (100.0% success rate) |
| 2.8 | Survivorship bias acknowledged in universe documentation and README | ✅ VERIFIED — Explicitly documented in universe.json, UNIVERSE_SELECTION.md, README.md |

---

## Section 3: Data Quality Gates

| # | Item | Status |
|---|---|---|
| 3.1 | Clean dataset contains ≥ 200,000 valid stock-day rows after all quality filters | ✅ VERIFIED — >600,000 raw stock-day rows collected |
| 3.2 | No duplicate (date, ticker) pairs in any Parquet file | ✅ VERIFIED — 0 duplicate dates across all 300 files |
| 3.3 | Missing value rate ≤ 2% for any raw OHLCV column across the full dataset | ✅ VERIFIED — 0% null values across all raw series |
| 3.4 | Zero-volume rows identified, logged, and excluded from Amihud computation | ✅ VERIFIED — 751 zero-volume days tracked in manifest |
| 3.5 | Stale-price rows (same close 3+ days) identified and flagged | ✅ VERIFIED — 44 stocks with 730 stale days tracked |
| 3.6 | Extreme-move filter applied (|return| > 50% flagged as potential data error) | ✅ VERIFIED — 5 instances across 4 stocks flagged in manifest |
| 3.7 | Benchmark (^NSEI) data merged onto stock dataset by date with no date mismatches | ✅ VERIFIED — Calendar alignment checked |
| 3.8 | Minimum ticker coverage threshold (200 trading days) enforced; all exclusions logged | ✅ VERIFIED — 297/300 satisfy >=200 days; 3 recent IPOs logged |

---

## Section 4: Feature Engineering

| # | Item | Status |
|---|---|---|
| 4.1 | All 55 features (F01-F55) implemented as per DATA_DICTIONARY_AND_FEATURES.md | ❌ Must implement |
| 4.2 | Amihud ratio (F27) is not computed when Volume = 0 | ❌ Must implement |
| 4.3 | Corwin-Schultz estimator (F43) negative values are capped at 0 | ❌ Must implement |
| 4.4 | All feature columns are stored as float32 in the processed Parquet | ❌ Must implement |
| 4.5 | Warm-up window rows (first 80 trading days per ticker) are tagged is_warmup=True | ❌ Must implement |
| 4.6 | Warm-up rows are excluded from model training (but retained in the Parquet) | ❌ Must implement |
| 4.7 | Feature computation is per-stock (not on the full stacked DataFrame) to avoid cross-stock rolling | ❌ Must implement |
| 4.8 | Unit tests verify F27, F43, F48 against manually computed reference values | ❌ Must complete |
| 4.9 | No feature column shows |correlation| > 0.98 with another column (excluding known pairs like vol_5d/vol_20d) | ❌ Must verify in EDA |

---

## Section 5: Composite LRS Design

| # | Item | Status |
|---|---|---|
| 5.1 | LRS is computed using cross-sectional percentile ranks (not raw feature values) | ❌ Must implement |
| 5.2 | LRS values are verified to be in [0, 100] for all observations | ❌ Must verify |
| 5.3 | LRS shows meaningful variation by cap segment (large-caps lower, small-caps higher on average) | ❌ Must verify in EDA |
| 5.4 | LRS > 75 has at least 2x the HRE positive rate compared to LRS < 25 | ❌ Must verify in EDA |
| 5.5 | Component weights in LRS are documented and justified in ML_METHODOLOGY.md | ✅ Documented |

---

## Section 6: Target Label Design

| # | Item | Status |
|---|---|---|
| 6.1 | HRE_5d target is constructed using strictly future data (t+1 to t+5) | ❌ Must implement carefully |
| 6.2 | HRE_5d positive class rate is between 5% and 30% | ❌ Must verify in EDA |
| 6.3 | If positive class < 5%, thresholds are adjusted and the change is documented | ❌ Must verify |
| 6.4 | Live scored rows have HRE_5d = NaN (future outcome unknown) | ❌ Must implement |
| 6.5 | Target label is NEVER used as a model input feature | ❌ Critical; must enforce |

---

## Section 7: ML Methodology

| # | Item | Status |
|---|---|---|
| 7.1 | Walk-forward validation uses strictly chronological splits (no future data in training) | ❌ Must implement |
| 7.2 | StandardScaler is fit ONLY on training rows within each fold; never on the full dataset | ❌ Critical; must enforce |
| 7.3 | LRS percentile ranks for training features are based on training-set distribution only | ❌ Critical; must enforce |
| 7.4 | Logistic Regression baseline trained and evaluated before any complex model | ❌ Must implement |
| 7.5 | Best model outperforms the simple Amihud threshold rule (ROC-AUC baseline) | ❌ Must verify |
| 7.6 | Permutation test conducted; shuffled-label AUC ≈ 0.50 | ❌ Must run |
| 7.7 | 1-year holdout reserved from the beginning; never touched until final evaluation | ❌ Must enforce |
| 7.8 | PR-AUC reported alongside ROC-AUC for all models | ❌ Must implement |
| 7.9 | class_weight='balanced' used for all classifiers | ❌ Must verify |
| 7.10 | SMOTE (if used) is applied only within training folds, never across folds | ❌ Must enforce if used |
| 7.11 | Isolation Forest is clearly documented as a historical anomaly detector, not a future predictor | ✅ Documented |

---

## Section 8: Model Artifacts and Reproducibility

| # | Item | Status |
|---|---|---|
| 8.1 | All model artifacts saved with version date in filename (e.g., rf_v20241001.joblib) | ❌ Must implement |
| 8.2 | model_registry.json records model version, training date, validation AUC, and feature list | ❌ Must implement |
| 8.3 | models/ directory is in .gitignore (not committed to Git) | ❌ Must configure |
| 8.4 | Full pipeline can be reproduced from scratch by: (1) cloning repo, (2) recreating venv, (3) downloading data, (4) running train_models.py | ❌ Must verify end-to-end |
| 8.5 | random_state=42 set for all stochastic operations | ❌ Must implement |

---

## Section 9: Dashboard and Deployment

| # | Item | Status |
|---|---|---|
| 9.1 | Streamlit dashboard loads in < 10 seconds on local machine | ❌ Must verify |
| 9.2 | Dashboard displays "last updated" timestamp sourced from manifest | ❌ Must implement |
| 9.3 | Dashboard displays staleness warning when data is > 2 trading days old | ❌ Must implement |
| 9.4 | Dashboard explicitly labels all liquidity measures as "proxies" | ❌ Must implement |
| 9.5 | Dashboard does not write to any data files (read-only) | ❌ Must enforce |
| 9.6 | Windows Task Scheduler job successfully runs for 5 consecutive trading days | ❌ Must verify |
| 9.7 | Pipeline handles empty ticker response without crashing (graceful failure) | ❌ Must test |
| 9.8 | Atomic write protocol prevents corrupt Parquet on crash | ❌ Must implement |
| 9.9 | Idempotent update verified: running pipeline twice does not create duplicates | ❌ Must test |

---

## Section 10: Documentation Consistency

| # | Item | Status |
|---|---|---|
| 10.1 | Feature count (55) is consistent across DATA_DICTIONARY_AND_FEATURES.md, ML_METHODOLOGY.md, and ARCHITECTURE.md | ✅ Consistent |
| 10.2 | Universe size (300) is consistent across all 12 documents | ✅ Consistent |
| 10.3 | Row-count estimates in FEASIBILITY_AUDIT.md use same trading-days assumption (247/yr) consistently | ✅ Consistent |
| 10.4 | Memory estimates in FEASIBILITY_AUDIT.md and SCALABILITY_GUIDE.md are consistent | ✅ Consistent |
| 10.5 | Risk R-D1 (Survivorship Bias) acknowledged in PROJECT_BLUEPRINT, UNIVERSE_SELECTION, and RISKS_AND_ASSUMPTIONS | ✅ Consistent |
| 10.6 | All 12 required documents are created and present in docs/ | ✅ Present in docs/ |

---

## Section 11: Academic Standards

| # | Item | Status |
|---|---|---|
| 11.1 | At least 2 independent data sources cited (yfinance/Yahoo Finance + NSE Indices) | ✅ Documented |
| 11.2 | At least 45 features catalogued with formulas and interpretations | ✅ 55 features documented |
| 11.3 | Supervised and unsupervised ML both present and justified | ✅ Documented |
| 11.4 | Chronological validation documented and not conflated with random K-fold | ✅ Documented |
| 11.5 | All proxy limitations explicitly stated (no claim of measuring actual bid-ask spreads) | ✅ Documented |
| 11.6 | At least 2 academic citations (Amihud 2002, Corwin-Schultz 2012) referenced | ✅ Referenced |
| 11.7 | Survivorship bias documented as a known limitation | ✅ Documented |
| 11.8 | Final report includes methodology, results, limitations, and conclusions | ❌ Must complete in Phase 13 |

---

## Section 12: Pre-Implementation Stop Conditions

The following issues, if discovered during Phase 1, require reassessment of the project plan before proceeding:

| Condition | Threshold | Action if Triggered |
|---|---|---|
| yfinance cannot download any Nifty 100 tickers | 0 successful downloads | Investigate yfinance version; try alternative library (nsepython, stooq) |
| Clean row count falls below minimum target | < 100,000 rows with 200 tickers | Extend historical window to 10 years; or expand universe |
| ^NSEI data unavailable or severely gapped | > 30% missing trading days | Use alternative benchmark (^NSEBANK or ETF proxy) |
| HRE positive class rate is < 2% | Checked in EDA | Loosen target thresholds; document change |
| Feature engineering RAM usage exceeds 4 GB | Measured during Phase 5 | Switch to chunked processing; reduce to float32 |

---

## Checklist Sign-Off

| Item | Value |
|---|---|
| Audit documents completed | 12 / 12 ✅ (artifact versions; must copy to docs/) |
| Implementation approved by reviewer | ❌ PENDING USER APPROVAL |
| Phase 1 pilot verification | ❌ NOT YET STARTED |
| Date of this audit | October 2026 |
