# PHASE-WISE ROADMAP
## ML-Based Liquidity and Trading-Risk Intelligence for Indian Equities

**Version:** 1.1  
**Status:** Active Roadmap — Phases 1 to 4.2 Completed  

---

## Phase Overview

| Phase | Name | Status | Dependencies |
|---|---|---|---|
| 1 | Feasibility and Pilot Data Verification | ✅ Completed | None |
| 2 | Repository and Environment Setup | ✅ Completed | Phase 1 |
| 3 | Stock Universe Definition and Data Acquisition | ✅ Completed | Phase 2 |
| 4 | Cleaning, Quality Checks, and Integration | ✅ Completed (Phases 4.1 & 4.2) | Phase 3 |
| 5 | Feature Engineering | 🟡 Next Active Phase | Phase 4 |
| 6 | EDA and Hypothesis Formulation | ⏳ Planned | Phase 5 |
| 7 | Risk-Score and Target Design | ⏳ Planned | Phases 5-6 |
| 8 | Baselines and ML Modelling | ⏳ Planned | Phase 7 |
| 9 | Chronological Validation and Robustness Testing | ⏳ Planned | Phase 8 |
| 10 | Production Pipeline and Prediction Generation | ⏳ Planned | Phase 9 |
| 11 | Streamlit Dashboard | ⏳ Planned | Phase 10 |
| 12 | Automated Daily Updates and Deployment | ⏳ Planned | Phase 11 |
| 13 | Final Audit, Report, and Presentation | ⏳ Planned | All phases |

---

## Phase 1: Feasibility and Pilot Data Verification

**Objective:** Verify that yfinance can reliably download historical data for a small sample of tickers before committing to the full pipeline. Catch data format issues early.

**Inputs:** 5-10 manually selected NSE tickers across large/mid/small-cap (e.g., RELIANCE.NS, TATAMOTORS.NS, HDFCBANK.NS, MARICO.NS, one small-cap).

**Outputs:**
- `notebooks/01_pilot_data_check.ipynb` — pilot download and inspection.
- Confirmed: yfinance ticker format, column names, date range, data types.
- Confirmed: `^NSEI` benchmark data availability.
- Measured: actual row counts, percentage of missing days, corporate action adjustment behavior.
- Measured: download time for 10 tickers.

**Acceptance Criteria:**
- All 5-10 pilot tickers download successfully with 5+ years of data.
- `^NSEI` returns clean data for the target date range.
- No unexpected NaN columns or format issues in returned DataFrames.
- yfinance version pinned and noted.

**Major Risks:**
- Pilot tickers fail or return sparse data → investigate alternative ticker formats or yfinance version.
- `^NSEI` data has large gaps → investigate alternative benchmark.
- Yahoo Finance rate-limiting during pilot → increase delay between requests.

---

## Phase 2: Repository and Environment Setup

**Objective:** Establish the project repository, Python environment, and folder structure.

**Inputs:** Project blueprint (this document set).

**Outputs:**
- Git repository initialized with the folder structure defined in `ARCHITECTURE.md`.
- `requirements.txt` and `pyproject.toml` created with pinned dependencies.
- `.gitignore` configured to exclude `data/`, `models/`, `logs/`, `.env`.
- Virtual environment (`.venv`) created and activated.
- `configs/` populated with template configuration files.
- `README.md` drafted.

**Key Dependencies (requirements.txt):**

```
yfinance==<pinned>
pandas==<pinned>
numpy==<pinned>
scikit-learn==<pinned>
pyarrow==<pinned>
streamlit==<pinned>
plotly==<pinned>
pyyaml==<pinned>
pytest==<pinned>
joblib==<pinned>
```

**Acceptance Criteria:**
- All team members (or the single developer) can clone the repo and recreate the environment in under 5 minutes.
- Running `pytest tests/` produces no import errors (tests are empty stubs initially).
- Folder structure matches ARCHITECTURE.md exactly.

---

## Phase 3: Stock Universe Definition and Data Acquisition

**Objective:** Define the final 300-stock universe and download all historical OHLCV data.

**Inputs:** NSE Indices constituent lists (manually downloaded from niftyindices.com).

**Tasks:**
1. Download constituent lists for Nifty 100, Nifty Midcap 150, Nifty Smallcap 250.
2. Map company names to NSE `.NS` tickers.
3. Select top 50 small-caps by available market cap or turnover data.
4. Run yfinance validation for all 300 tickers (check coverage ≥ 200 days over 7 years).
5. Build `configs/universe.json` with final ticker list.
6. Download full historical data (2018-01-01 to present) for all 300 tickers + `^NSEI`.
7. Save raw data to `data/raw/ohlcv_YYYYMMDD.parquet` and `data/raw/benchmark_YYYYMMDD.parquet`.

**Responsible Files/Modules:**
- `scripts/build_universe.py` — universe construction and validation.
- `scripts/backfill_history.py` — full historical download.
- `src/data/fetcher.py` — download implementation.
- `src/data/storage.py` — Parquet write.

**Tests:**
- `test_fetcher.py`: verify that fetcher handles empty responses, HTTP 429, and ticker-not-found without crashing.
- Verify: manifest records the number of successfully downloaded tickers.

**Acceptance Criteria:**
- ≥ 270 of 300 tickers successfully downloaded (90% success rate).
- Raw data size within expected bounds (5-20 MB Parquet).
- All downloaded data covers at least 2018-01-01 to current date.
- No duplicate (date, ticker) rows in raw Parquet.

**Major Risks:**
- Many small-cap tickers fail → expand to Nifty Midcap 150 or accept <300 stocks.
- Download takes >4 hours due to rate limiting → implement overnight batch download with delays.
- Ticker format ambiguity for stocks with special characters → manual mapping required.

---

## Phase 4: Cleaning, Quality Checks, and Integration

**Objective:** Apply quality filters to raw data; produce a clean, integrated dataset.

**Inputs:** `data/raw/ohlcv_YYYYMMDD.parquet`, `data/raw/benchmark_YYYYMMDD.parquet`.

**Tasks:**
1. Filter zero-volume rows (mark, do not silently delete — log counts).
2. Filter stale prices (same close for 3+ consecutive days on a given stock).
3. Remove rows with negative prices or clearly erroneous values (>300% single-day move).
4. Merge benchmark (`^NSEI`) close and return onto stock rows by date.
5. Validate row count per ticker; exclude tickers falling below minimum threshold.
6. Write clean integrated dataset to `data/interim/stocks/ohlcv_clean.parquet` and cleaned market datasets to `data/interim/market/`.

**Responsible Files/Modules:** `src/data/validator.py`, `src/data/storage.py`.

**Tests:** `test_validator.py` with synthetic DataFrames containing known quality issues.

**Acceptance Criteria:**
- Clean dataset contains ≥ 200,000 valid stock-day rows.
- No duplicate (date, ticker) pairs.
- Missing value rate per column ≤ 2% (after expected gaps).
- At least 250 tickers survive quality filtering.

---

## Phase 5: Feature Engineering

**Objective:** Compute all 55 features (F01-F55) for every valid stock-day observation.

**Inputs:** `data/interim/stocks/ohlcv_clean.parquet`, `data/interim/market/*.parquet`.

**Tasks:**
1. Implement each feature module (`returns.py`, `volatility.py`, `liquidity.py`, `gaps.py`, `market_relative.py`, `market_stress.py`).
2. Process one stock at a time; concatenate results.
3. Apply warm-up window flag (`is_warmup=True` for first 80 rows per stock).
4. Downcast all feature columns to `float32`.
5. Write to `data/processed/features_YYYYMMDD.parquet`.

**Tests:** `test_features.py` — verify F27 (Amihud), F43 (CS spread), F48 (beta) against manually computed reference values on small synthetic DataFrames.

**Acceptance Criteria:**
- All 55 features present in output Parquet.
- NaN rate per feature matches expected warm-up impact.
- Feature ranges are sensible (Amihud > 0, RSI in [0,100], correlations in [-1,1]).
- Feature Parquet file size within estimates.

**Major Risks:**
- Corwin-Schultz estimator returns many negative values for illiquid small-caps → cap at 0, document.
- Rolling windows create NaN cascades for short-history tickers → verify minimum history requirement.

---

## Phase 6: EDA and Hypothesis Formulation

**Objective:** Understand the data distribution, validate hypotheses, identify anomalies, and finalize feature selection.

**Inputs:** `data/processed/features_YYYYMMDD.parquet`.

**Tasks:**
1. Descriptive statistics by cap segment.
2. Test H1-H7 (correlation, distributional tests).
3. Plot Amihud ratio distributions by segment.
4. Analyze target label class balance under different threshold settings.
5. Correlation matrix; identify highly correlated feature pairs.
6. Visualize feature time series for known market stress events (COVID-19 March 2020, SEBI circuit breaker events).

**Responsible Files/Modules:** `notebooks/02_eda.ipynb`, `notebooks/03_feature_exploration.ipynb`.

**Acceptance Criteria:**
- At least 5 hypotheses confirmed, rejected, or partially supported with statistical tests.
- Feature correlation matrix produced; pairs with |r| > 0.95 flagged for possible removal.
- Target class balance confirmed to be in workable range (5-30% positive).
- No unexpected data anomalies that invalidate the feature design.

---

## Phase 7: Risk-Score and Target Design

**Objective:** Finalize the LRS composite score weights and HRE target thresholds based on EDA findings.

**Inputs:** EDA findings from Phase 6.

**Tasks:**
1. Compute LRS for all historical observations.
2. Validate LRS distribution: all values in [0,100], meaningful variation across cap segments.
3. Construct HRE_5d target; measure class balance.
4. Adjust thresholds if class balance is outside workable range (5-30% positive).
5. Cross-validate: verify that LRS > 75 correlates with HRE_5d = 1.
6. Write labeled dataset (features + LRS + HRE_5d) to `data/processed/features_labeled.parquet`.

**Responsible Files/Modules:** `src/labels/lrs.py`, `src/labels/targets.py`, `notebooks/04_label_analysis.ipynb`.

**Acceptance Criteria:**
- LRS values span full [0,100] range; large-caps cluster near 0-30, small-caps near 40-80.
- HRE_5d positive class rate is between 5% and 30%.
- LRS > 75 has at least 2x the HRE positive rate vs. LRS < 25 (basic validity check).

---

## Phase 8: Baselines and ML Modelling

**Objective:** Train and evaluate all ML models; select the best model for production.

**Inputs:** `data/processed/features_labeled.parquet` (excluding warm-up rows and most recent 1-year holdout).

**Tasks:**
1. Implement walk-forward validation framework (10 folds).
2. Train Logistic Regression baseline; record per-fold metrics.
3. Train Random Forest; tune max_depth and n_estimators.
4. Train HistGradientBoosting; tune regularization.
5. Train Isolation Forest (unsupervised; separate from supervised pipeline).
6. Compare models: ROC-AUC, PR-AUC, Precision/Recall for HRE=1.
7. Select best model; generate feature importance and permutation importance report.
8. Save all model artifacts to `models/`.

**Responsible Files/Modules:** `src/modeling/trainer.py`, `src/modeling/evaluation.py`, `notebooks/05-08_model_*.ipynb`.

**Acceptance Criteria:**
- All three supervised models evaluated; walk-forward metrics tabulated.
- Best model achieves ROC-AUC ≥ 0.65 on validation folds.
- Logistic Regression baseline established and outperformed by ensemble model.
- Feature importance consistent with domain knowledge.
- No data leakage detected (permutation test, temporal stability check).

---

## Phase 9: Chronological Validation and Robustness Testing

**Objective:** Final rigorous out-of-sample evaluation; robustness checks against model gaming.

**Inputs:** Best model artifact from Phase 8; reserved 1-year holdout data.

**Tasks:**
1. Apply best model to 1-year holdout (never-seen data).
2. Compute holdout ROC-AUC and PR-AUC; compare to validation estimates.
3. Run permutation test on training data (confirm AUC drops to ~0.50).
4. Evaluate model separately on large/mid/small-cap subgroups.
5. Evaluate during high-volatility market periods vs. normal periods.
6. Test label sensitivity (re-run with 90th vs. 95th percentile Amihud threshold).
7. Document all robustness check results in `reports/validation_report.md`.

**Acceptance Criteria:**
- Holdout ROC-AUC within 0.05 of validation estimate (no major generalization gap).
- Permutation test AUC ≈ 0.50 (confirms model is not random).
- Model performs reasonably (AUC ≥ 0.60) for all cap-segment subgroups.
- Label sensitivity analysis shows stable ranking of models.

---

## Phase 10: Production Pipeline and Prediction Generation

**Objective:** Convert experimental notebooks into the production pipeline; run end-to-end.

**Inputs:** All `src/` modules; model artifacts from Phase 8.

**Tasks:**
1. Finalize `src/pipeline/daily_pipeline.py` orchestrator.
2. Implement `src/pipeline/health_check.py` (model artifact existence, data freshness).
3. Create `scripts/daily_refresh.bat` for Windows Task Scheduler.
4. Run full historical backfill: compute LRS, HRE_prob, anomaly_score for all historical data.
5. Store predictions in `data/predictions/scored_YYYYMMDD.parquet` (one file per run date).
6. Write `data/manifests/manifest_YYYYMMDD.json` with run metadata.
7. Verify end-to-end runtime on target hardware.

**Acceptance Criteria:**
- Pipeline runs from raw download to prediction file in under 30 minutes for 300 stocks.
- Manifest correctly records: run timestamp, ticker count, failed tickers, data quality flags.
- Predictions file contains all expected columns for all tickers.
- Pipeline handles 5 injected failure cases (empty ticker response, network timeout, missing date) without crashing.

---

## Phase 11: Streamlit Dashboard

**Objective:** Build the production dashboard for stakeholder visualization.

**Inputs:** `data/predictions/`, `data/processed/features_*.parquet`, `data/manifests/`.

**Pages to implement:**
1. **Overview:** Today's top high-risk stocks (sorted by HRE_prob). LRS distribution histogram. Last-updated timestamp.
2. **Stock Detail:** Select any ticker; view LRS and HRE_prob time series. Feature trend charts. Anomaly score overlay.
3. **Portfolio Risk:** Enter a list of tickers; view aggregate risk summary. Weighted average LRS. High-risk count.
4. **Anomaly Log:** Browse historical anomaly events (anomaly_flag=1 days). Filter by ticker, date, cap segment.
5. **Data Quality:** Pipeline health panel. Show manifest details. Warn if last update > 2 trading days old.

**Responsible Files/Modules:** `app/` directory.

**Acceptance Criteria:**
- Dashboard loads in under 10 seconds on local machine.
- All 5 pages render without error on the full 300-stock dataset.
- "Data staleness" warning appears if most recent predictions are > 2 trading days old.
- Feature trend charts display correctly for at least 3 different tickers.

---

## Phase 12: Automated Daily Updates and Deployment

**Objective:** Configure Windows Task Scheduler for automated daily pipeline execution.

**Inputs:** `scripts/daily_refresh.bat`.

**Tasks:**
1. Configure Task Scheduler trigger: daily at 17:30 IST (post-NSE close at 15:30 IST; allows 2 hours for Yahoo Finance to update).
2. Configure "Run task as soon as possible after a scheduled start is missed."
3. Test: manually run task; verify successful execution from Task Scheduler.
4. Test: simulate failure (disconnect internet during fetch); verify graceful error handling and log.
5. Run for 5 consecutive trading days; verify predictions are updated daily.

**Acceptance Criteria:**
- Task Scheduler runs successfully for 5 consecutive trading days without manual intervention.
- Failed ticker count each day is logged and does not trigger full pipeline abort.
- Streamlit dashboard shows the current day's data (or warns if not yet available).
- No duplicate rows appear in prediction files after 5 days of incremental updates.

---

## Phase 13: Final Audit, Report, and Presentation

**Objective:** Produce all final deliverables; audit the complete project for consistency and correctness.

**Tasks:**
1. Final consistency check: all 12 doc files internally consistent.
2. Write `reports/final_report.md` (methodology, results, limitations, conclusions).
3. Produce performance visualization charts for the report.
4. Write the slide deck (`reports/presentation.pptx`).
5. Clean and annotate all notebooks.
6. Final GitHub repository cleanup.
7. Record a 2-3 minute dashboard demo video.

**Final Deliverables:**
- All 12 `docs/*.md` audit documents.
- Trained model artifacts in `models/`.
- Streamlit dashboard running locally.
- Final report (PDF/Markdown).
- Slide presentation.
- Annotated Jupyter notebooks.
- Public or private GitHub repository with clean commit history.
- Dashboard demo recording.

---

## Milestones

| Milestone | Target After Start | Condition |
|---|---|---|
| M1: Pilot Verified | Week 1 | Phase 1 complete; yfinance confirmed |
| M2: Universe Downloaded | Week 2 | ≥270 tickers with 5yr history |
| M3: Features Computed | Week 3 | 55 features, ≥200k clean rows |
| M4: Models Trained | Week 5 | Best model AUC ≥ 0.65 on validation |
| M5: Pipeline Running | Week 6 | End-to-end daily pipeline verified |
| M6: Dashboard Live | Week 7 | All 5 pages rendering |
| M7: Auto-refresh Live | Week 7 | Task Scheduler running 5+ days |
| M8: Final Submission | Week 8 | Report, slides, and repo delivered |
