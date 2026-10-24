# FEASIBILITY AUDIT
## ML-Based Liquidity and Trading-Risk Intelligence for Indian Equities

**Version:** 1.1
**Status:** Active Feasibility Reference (Phase 4.2 Complete)
**Label convention:** [VERIFIED] = confirmed from documentation/research. [ESTIMATE] = calculated from known parameters. [UNRESOLVED] = requires verification during implementation.

---

## 1. Resource & Environment Profile

| Component | Standard Specification | Relevance |
|---|---|---|
| Runtime Environment | Python 3.11+ | Standard virtual environment |
| Data Processing | Pandas, NumPy, PyArrow | Vectorized single-node computation |
| ML Frameworks | Scikit-learn (CPU-first) | Standard tree ensembles and linear models |
| Storage Format | Parquet (Snappy compression) | Columnar storage; highly space-efficient |
| Automation | Task Scheduler / CLI scripts | Scheduled daily execution |
| Visualization | Streamlit & Plotly | Lightweight browser-based dashboard |

**Memory Budget & Efficiency Principles:**
The pipeline is designed to operate comfortably within standard workstation memory boundaries by processing stocks sequentially, casting numerical features to `float32`, and writing intermediate files atomically.

---

## 2. Row-Count Feasibility

### Trading Days per Year
Indian stock markets trade approximately 245-250 days per year (after excluding NSE holidays and weekends). [VERIFIED — NSE publishes annual holiday calendars; ~247 days is a safe estimate.]

### Formula
```
Expected rows = N_stocks × N_years × N_trading_days_per_year
```

### Baseline Estimates (Before Cleaning)

| Universe | Years | Trading Days/Yr | Raw Rows |
|---|---|---|---|
| 300 stocks | 5 | 247 | 370,500 |
| 300 stocks | 7 | 247 | 518,700 |
| 500 stocks | 5 | 247 | 617,500 |
| 500 stocks | 7 | 247 | 864,500 |
| 1,000 stocks | 5 | 247 | 1,235,000 |
| 1,000 stocks | 7 | 247 | 1,729,000 |

**All above figures are [ESTIMATE]. Actual counts depend on data availability per ticker.**

### Deductions to Apply

| Deduction | Estimated Impact |
|---|---|
| Failed/missing tickers (yfinance) | -5% to -15% of stocks |
| Warm-up period (e.g., 60 trading days for 60-day rolling features) | -60 rows per stock |
| Corporate action data gaps | -1% to -3% of rows per stock |
| Data quality filter (zero volume days, stale prices) | -0.5% to -2% of rows |
| IPO date gaps (stocks listed after 2018) | Varies; mid/small caps more affected |

### Post-Cleaning Row Estimates (Conservative)

| Universe | Years | Estimated Clean Rows | Target Met? |
|---|---|---|---|
| 300 stocks | 5 | ~310,000-340,000 | YES (>200k) |
| 300 stocks | 7 | ~430,000-470,000 | YES |
| 500 stocks | 5 | ~520,000-560,000 | YES |
| 1,000 stocks | 7 | ~1,400,000-1,600,000 | YES |

**Conclusion:** Even with a 300-stock universe over 5 years, the 200,000-row target is comfortably achievable. The 100,000-row minimum is met even at 200 stocks over 3 years.

**[ESTIMATE — requires verification against actual yfinance download results during Phase 1.]**

---

## 3. RAM Usage Estimates

### Raw OHLCV Data (7 columns per stock-day)

| Universe | Rows | Estimated RAM (float64) | Optimized (float32 + category) |
|---|---|---|---|
| 300 stocks, 5yr | ~340,000 | ~19 MB | ~10 MB |
| 300 stocks, 7yr | ~470,000 | ~26 MB | ~13 MB |
| 500 stocks, 7yr | ~800,000 | ~45 MB | ~23 MB |
| 1,000 stocks, 7yr | ~1,600,000 | ~90 MB | ~45 MB |

Raw OHLCV alone presents no memory concerns in standard environments.

### Feature-Engineered Dataset (55 columns per stock-day)

| Universe | Rows | Estimated RAM (float64) | Optimized (float32 + category) |
|---|---|---|---|
| 300 stocks, 5yr | ~310,000 | ~136 MB | ~68 MB |
| 300 stocks, 7yr | ~430,000 | ~189 MB | ~95 MB |
| 500 stocks, 7yr | ~730,000 | ~321 MB | ~161 MB |
| 1,000 stocks, 7yr | ~1,450,000 | ~638 MB | ~319 MB |

**[ESTIMATE based on: rows x 55 columns x 8 bytes (float64) or 4 bytes (float32), plus Pandas overhead ~20%.]**

### Critical RAM Constraint Analysis

At 300 stocks (7yr), feature dataset RAM usage is approximately 190 MB (float64) or 95 MB (float32). This is comfortably within standard runtime memory budgets. Even at 1,000 stocks (7yr), float32 usage is approximately 320 MB, remaining manageable when chunked processing is used during feature engineering.

**RAM becomes a concern only if:**
- Loading the entire feature matrix into memory simultaneously without downcasting (e.g., for model training on 1M+ rows with 55 unoptimized features)
- Using float64 for the 1,000-stock universe at 7 years (~640 MB for features alone, plus model overhead)

**Recommended mitigation:** Use float32 for all feature columns, use `category` dtype for ticker/sector columns, and use chunked feature engineering (process one stock at a time, concatenate at the end).

---

## 4. Disk Usage Estimates

### Parquet (Snappy compression, float32 + category dtypes)

| Artifact | Estimated Size |
|---|---|
| Raw OHLCV, 300 stocks, 7yr | ~5-10 MB |
| Feature dataset, 300 stocks, 7yr | ~20-40 MB |
| Feature dataset, 500 stocks, 7yr | ~35-65 MB |
| Feature dataset, 1,000 stocks, 7yr | ~70-130 MB |
| Predictions archive (3 years daily) | ~5-15 MB |
| Model artifacts (Joblib) | ~10-50 MB total |
| Logs | ~1-5 MB/year |
| Notebooks | ~50-200 MB |

**Total project disk usage: [ESTIMATE] 500 MB to 2 GB.** Highly space-efficient with negligible storage footprint.

### Raw data must not be committed to Git. Use `.gitignore` to exclude `data/` and `models/`.

---

## 5. Compute Time Estimates

### Data Download (yfinance)

| Task | Estimate | Notes |
|---|---|---|
| Download 300 tickers, 7yr history | 15-40 minutes | Rate limiting; batched downloads |
| Download 500 tickers, 7yr history | 25-70 minutes | Requires retry logic |
| Daily refresh (300 tickers, 1 day) | 3-10 minutes | Incremental fetch |

**[ESTIMATE — highly variable depending on Yahoo Finance rate-limiting behavior.]**

### Feature Engineering

| Task | Estimate | Notes |
|---|---|---|
| Engineer 55 features, 300 stocks, 5yr | 2-5 minutes | Sequential per-stock processing |
| Engineer 55 features, 500 stocks, 7yr | 5-12 minutes | With chunked Pandas operations |
| Engineer 55 features, 1,000 stocks, 7yr | 10-25 minutes | May need chunked I/O |

### Model Training (Scikit-learn, CPU)

| Model | Dataset Size | Estimate |
|---|---|---|
| Logistic Regression | 300k rows, 55 features | < 30 seconds |
| Random Forest (100 trees) | 300k rows, 55 features | 2-5 minutes |
| HistGradientBoosting | 300k rows, 55 features | 3-8 minutes |
| Isolation Forest | 300k rows, 55 features | 1-3 minutes |
| Walk-forward (5 folds) | As above x5 | 10-40 minutes total |

**[ESTIMATE — scikit-learn benchmarks on similar hardware and dataset sizes.]**

### Streamlit Dashboard Load

| Task | Estimate |
|---|---|
| Initial load (read Parquet, render charts) | 3-10 seconds |
| Stock filter / date range update | < 2 seconds |
| Portfolio view recalculation | < 5 seconds |

---

## 6. Scalability Limits

| Universe Size | RAM Status | Compute Status | Feasibility |
|---|---|---|---|
| 300 stocks, 5yr | COMFORTABLE | COMFORTABLE | FULLY FEASIBLE |
| 300 stocks, 7yr | COMFORTABLE | COMFORTABLE | FULLY FEASIBLE |
| 500 stocks, 7yr | COMFORTABLE | MANAGEABLE | FEASIBLE |
| 700 stocks, 7yr | MANAGEABLE | MANAGEABLE | FEASIBLE with float32 |
| 1,000 stocks, 7yr | CAUTION | SLOW | FEASIBLE with chunked processing and float32 |
| 1,500+ stocks, 7yr | RAM RISK | SLOW | NOT recommended without chunked I/O and batched training |

**Recommended initial target: 300 stocks, 5-7 years.** This provides ample data volume for ML while remaining comfortably within standard memory and runtime limits.

---

## 7. Acceleration & Framework Choice

The pipeline prioritizes CPU-based scikit-learn implementations as the primary baseline:
- Pandas feature engineering is CPU-bound and fully vectorized.
- Scikit-learn models (Logistic Regression, HistGradientBoosting, Random Forest, Isolation Forest) execute efficiently on modern multi-core processors.
- Streamlit dashboard operations perform read-only queries against Parquet files.

Optional GPU acceleration (e.g., XGBoost with GPU histograms or RAPIDS cuML) is not required for the 300–500 stock universe scale and is documented strictly as a potential future scaling path.

---

## 8. Key Feasibility Risks

| Risk | Severity | Mitigation |
|---|---|---|
| yfinance rate limiting | HIGH | Throttle requests, add delay between tickers, retry logic |
| RAM exhaustion during feature engineering | MEDIUM | Use float32, process per-stock, avoid holding all data in memory simultaneously |
| Insufficient clean rows after filtering | LOW | 300 stocks over 5 years yields ~310k+ rows; large safety margin |
| Slow model training (1,000 stocks) | MEDIUM | Subsample for initial experiments; use HistGradientBoosting over RandomForest |
| Data corruption on crash | LOW | Write to temp files, rename on success; append-safe Parquet design |
| Windows Task Scheduler not running | MEDIUM | Test scheduler in Phase 1; document fallback manual run |
| yfinance API breaking change | HIGH | Pin yfinance version; monitor PyPI; maintain raw data locally |

---

## 9. Conclusion

The project is **fully feasible on standard workstation environments** at the recommended 300-stock initial universe over 5-7 years. The row count target (>200,000) is met with significant margin (564,439 clean rows achieved in Phase 4.2). Memory and disk usage are well within constraints when float32 dtypes and Parquet storage are used. Compute times are acceptable. The project can scale to 500-700 stocks without fundamental changes. Scaling to 1,000 stocks requires chunked processing but remains viable.

**[UNRESOLVED items for Phase 1 verification:]**
1. Actual number of Nifty 100 / Midcap 150 / Smallcap 250 tickers successfully downloaded from yfinance.
2. Average row count per ticker after quality filtering.
3. Rate-limiting behavior of Yahoo Finance for 300 simultaneous tickers.
4. Actual disk size of first full download.
