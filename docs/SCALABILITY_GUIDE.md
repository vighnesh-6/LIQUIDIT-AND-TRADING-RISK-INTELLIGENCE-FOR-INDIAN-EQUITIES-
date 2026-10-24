# SOFTWARE SCALABILITY AND PERFORMANCE GUIDE
## ML-Based Liquidity and Trading-Risk Intelligence for Indian Equities

**Version:** 1.1  
**Status:** Active Reference Guide  

---

## 1. System Scalability Principles

The liquidity and trading-risk intelligence pipeline is engineered for high throughput, memory safety, and reproducibility on standard workstation environments. The system processes extensive multi-year panel datasets of Indian equities without requiring distributed clusters or specialized infrastructure.

### Core Design Principles

1. **Strict Memory Budgeting:** Process data per stock and cast arrays to minimal sufficient precision (`float32`), ensuring the working memory footprint remains bounded even as the universe grows.
2. **Columnar Parquet Storage:** Leverage Apache Parquet with Snappy compression for fast selective I/O, compact disk footprints, and rapid filtering by date or ticker.
3. **Atomic and Idempotent Operations:** Prevent data corruption by writing to intermediate temporary files (`.tmp.parquet`) before atomic renaming, ensuring idempotent execution across runs.
4. **Vectorized Computation:** Execute all rolling metrics (returns, volatility, Amihud illiquidity, price impact) using vectorized NumPy and Pandas routines rather than slow Python iteration.
5. **Decoupled Architecture:** Maintain clean separation between data acquisition, validation, feature engineering, model inference, and presentation layers.

---

## 2. Dataset Size Projections

### Trading Days Baseline
The National Stock Exchange of India (NSE) trades approximately 247 days per calendar year after accounting for standard exchange holidays and weekends.

### Raw OHLCV Ingestion Projections

| Universe | 5-Year Horizon | 7-Year Horizon |
|---|---|---|
| **300 stocks (Current Baseline)** | ~370,500 rows | ~518,700 rows |
| **500 stocks** | ~617,500 rows | ~864,500 rows |
| **700 stocks** | ~864,500 rows | ~1,210,300 rows |
| **1,000 stocks** | ~1,235,000 rows | ~1,729,000 rows |

*Actual verified baseline for current 300-stock universe (2018–2026): 565,190 raw stock rows across 300 tickers.*

### Post-Cleaning Production Rows
After applying automated hygiene gates (zero-volume flags, non-positive price checks, and stale price filtering), the clean interim dataset yields:

| Universe | Horizon | Retained Clean Rows | Minimum Target (200k) |
|---|---|---|---|
| **300 stocks** | ~7+ years | **564,439 clean rows** | **Exceeded (282%)** |
| **500 stocks** | 7 years | ~735,000 rows | Exceeded |
| **1,000 stocks** | 7 years | ~1,470,000 rows | Exceeded |

---

## 3. Memory Optimization Strategy

### Memory Footprint Formula
Working memory for tabular datasets is calculated as:
$$\text{Memory} = \text{Rows} \times \text{Columns} \times \text{Bytes per Element} \times (1 + \text{Overhead})$$

- Standard `float64`: 8 bytes per value
- Optimized `float32`: 4 bytes per value (50% reduction)
- Categorical `category`: 1–2 bytes per code
- Pandas DataFrame internal indexing overhead: approximately 10%–20%

### Memory Consumption by Pipeline Stage

#### A. Raw OHLCV Panel (7 columns: date, ticker, open, high, low, close, volume)

| Universe Size | Row Count | Standard (`float64`) | Optimized (`float32` + category) |
|---|---|---|---|
| 300 stocks | ~565,000 | ~32 MB | ~16 MB |
| 500 stocks | ~865,000 | ~49 MB | ~24 MB |
| 1,000 stocks | ~1,730,000 | ~98 MB | ~48 MB |

*Raw OHLCV data presents negligible memory load across all realistic universe sizes.*

#### B. Feature Matrix (55 engineered features + 5 metadata columns = 60 columns)

| Universe Size | Row Count | Standard (`float64`) | Optimized (`float32`) | Scalability Status |
|---|---|---|---|---|
| 300 stocks | ~565,000 | ~271 MB | ~135 MB | Fully In-Memory |
| 500 stocks | ~865,000 | ~415 MB | ~208 MB | Fully In-Memory |
| 700 stocks | ~1,210,000 | ~581 MB | ~290 MB | Fully In-Memory |
| 1,000 stocks | ~1,730,000 | ~830 MB | ~415 MB | In-Memory with Chunking |

#### C. Model Training Memory Profile (Expanding-Window Walk-Forward Validation)

| Model Architecture | 300k Rows, 55 Features | 565k Rows, 55 Features | 1,000k Rows, 55 Features |
|---|---|---|---|
| **Logistic Regression (L2 / ElasticNet)** | < 100 MB | < 150 MB | < 250 MB |
| **HistGradientBoosting (`HistGradientBoostingClassifier`)** | ~250–400 MB | ~400–600 MB | ~800 MB–1.2 GB |
| **Random Forest (`n_estimators=150`, `max_depth=10`)** | ~600 MB–1.1 GB | ~1.0–1.8 GB | ~2.0–3.2 GB |
| **Isolation Forest (`n_estimators=100`)** | ~200–350 MB | ~350–550 MB | ~700 MB–1.0 GB |

**Key Architectural Decision:** `HistGradientBoostingClassifier` utilizes histogram-based discretization of continuous features into 256 bins, yielding 3x to 5x faster training speeds and significantly lower memory requirements compared to exact-split tree ensembles.

---

## 4. Disk Storage & Columnar Compression

### Parquet Format Efficiency (Snappy Compression)

| Dataset Component | 300 Stocks (Current) | 500 Stocks | 1,000 Stocks |
|---|---|---|---|
| Raw OHLCV Parquets | ~18 MB | ~30 MB | ~60 MB |
| Clean Interim Stocks (`stocks/ohlcv_clean.parquet`) | ~44 MB | ~74 MB | ~148 MB |
| Clean Interim Market (`market/*_clean.parquet`) | ~0.5 MB | ~0.5 MB | ~0.5 MB |
| Feature Dataset (`features_*.parquet`, 60 cols) | ~45 MB | ~75 MB | ~150 MB |
| Model Artifacts (`joblib` bundles) | ~25 MB | ~25 MB | ~35 MB |
| Predictions Archive (Daily, multi-year) | ~8 MB | ~14 MB | ~28 MB |
| Audit Manifests & Logs | ~3 MB | ~5 MB | ~10 MB |
| **Total Storage Required** | **~113 MB** | **~173 MB** | **~331 MB** |

The entire multi-year repository requires only a few hundred megabytes of disk space, making it exceptionally portable and suitable for version-controlled codebases and lightweight CI/CD verification.

---

## 5. Execution Runtime & Throughput

### Component Latency Breakdown

| Pipeline Stage | 300 Stocks (Sequential) | 500 Stocks (Estimated) | Optimization Strategy |
|---|---|---|---|
| **Raw Data Acquisition (yfinance)** | ~15–30 min | ~25–50 min | Batching by 20 tickers; exponential backoff |
| **Data Validation & Cleaning** | ~3–5 sec | ~6–10 sec | Vectorized column checks and boolean masks |
| **Feature Engineering (F01–F55)** | ~2–4 min | ~4–7 min | Per-stock sequential calculation; float32 casting |
| **Composite LRS Calibration** | ~10–20 sec | ~20–40 sec | Vectorized cross-sectional percentile ranking |
| **Model Training (10 Walk-Forward Folds)** | ~8–15 min | ~15–28 min | Multi-core CPU parallelization (`n_jobs=-1`) |
| **Model Scoring & Anomaly Inference** | ~15–30 sec | ~30–60 sec | Batch matrix operations |
| **Daily Incremental Refresh** | **~2–5 min** | **~4–8 min** | Processes only newest trading day rows |

---

## 6. Software Scaling Roadmap

### Universe Scaling Paths

```
Current Baseline (300 Stocks, 565k rows)
│   ├── Pure in-memory Pandas + NumPy
│   ├── Sequential per-stock feature generation
│   └── Multi-core scikit-learn models
│
└── Expanded Universe (500 to 1,000 Stocks)
    ├── Streaming chunked writes (batches of 100 tickers)
    ├── HistGradientBoosting as primary supervised model
    ├── Parquet partitioning by date/cap-segment
    └── Shared memory workers for parallel feature extraction
```

### Technical Scalability Best Practices

1. **Avoid Iterative `.apply()` over DataFrames:** Always prefer vectorized operations (`.pct_change()`, `.rolling()`, `.diff()`). When complex rolling aggregations are required, compute on raw NumPy arrays or group by ticker explicitly.
2. **Sequential Stock Processing:** Avoid loading and computing all 300 stocks in a single unpartitioned DataFrame during rolling window calculations. Iterating stock-by-stock ensures constant $O(1)$ memory overhead per ticker during feature construction.
3. **Partitioned I/O:** Store raw stock Parquets individually (`data/raw/stocks/<TICKER>.parquet`) so that incremental fetches and individual stock audits require zero scanning of other tickers.
4. **Reproducible Validation:** Ensure random state reproducibility across all estimators (`random_state=42`) and enforce strictly chronological expanding splits to guarantee that temporal ordering is preserved as data scale expands.
