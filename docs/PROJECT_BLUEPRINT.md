# PROJECT BLUEPRINT
## ML-Based Liquidity and Trading-Risk Intelligence for Indian Equities

**Version:** 1.1
**Date:** October 2026
**Status:** Implementation Active (Phase 4.2 Complete)

---

## 1. Project Identity

| Field | Value |
|---|---|
| **Project Title** | ML-Based Liquidity and Trading-Risk Intelligence for Indian Equities |
| **Short Name** | LiqRisk-India |
| **Domain** | Quantitative Finance / Applied Machine Learning |
| **Context** | Academic ML Project (ADS / Quant Finance) |
| **Environment** | Python 3.11+, Windows Workstation / Standard Operating Environment |
| **Primary Stack** | Python 3.11+, Pandas, NumPy, Scikit-learn, Parquet, Streamlit |

---

## 2. Problem Statement

Indian equity markets contain thousands of listed stocks spanning a wide spectrum of liquidity — from highly liquid large-cap stocks (e.g., Reliance, TCS) to extremely thin small-cap and micro-cap counters. Retail investors, portfolio managers, and risk analysts frequently lack accessible, quantitative tools to:

1. **Assess how liquid a stock is** on a given day or over a rolling window.
2. **Identify abnormal trading conditions** (unusual volume spikes, illiquidity dry-ups, price gaps) that may signal elevated trading risk.
3. **Generate a forward-looking risk score** indicating whether a stock is entering a high-risk liquidity/trading regime.
4. **Monitor risk across a portfolio** of Indian equities on a near-daily basis without access to expensive real-time data feeds.

This project addresses these needs using freely available daily OHLCV data from Yahoo Finance (via `yfinance`), classical machine learning, and a Streamlit dashboard — designed for lightweight, reproducible execution without specialized infrastructure.

---

## 3. Stakeholders

| Stakeholder | Interest | Primary Deliverable |
|---|---|---|
| **Retail investors** | Understand which stocks are risky to enter/exit | Dashboard liquidity score and risk flag |
| **Portfolio managers** | Monitor portfolio-level liquidity concentration | Portfolio risk aggregation view |
| **Risk analysts** | Quantify trading-risk exposure across sectors | Risk score time series and anomaly log |
| **Quant researchers** | Study liquidity patterns in Indian mid/small caps | Feature dataset and model outputs |
| **Academic evaluators** | Assess ML methodology and data science rigor | Report, notebooks, methodology document |
| **Recruiters / Resume** | Evaluate end-to-end ML project capability | GitHub repo, dashboard demo, documented pipeline |

---

## 4. Objectives

### Primary Objectives

1. Build a reproducible data pipeline that downloads, validates, and stores daily OHLCV data for approximately 300 Indian equities spanning at least 5 years.
2. Engineer a catalogue of at least 45 meaningful liquidity and trading-risk proxy features from daily OHLCV data.
3. Design and compute a **composite Liquidity-Risk Score (LRS)** for each stock-day observation using a rule-based composite method backed by academic proxies (Amihud, normalized range, volume z-score, etc.).
4. Define a **binary forward-looking target** (High-Risk Event) and train supervised ML classifiers (Logistic Regression, Random Forest, HistGradientBoosting) to predict it.
5. Apply **unsupervised anomaly detection** (Isolation Forest) to detect historically unusual stock-day observations, independent of the supervised target.
6. Validate all models using strict **chronological walk-forward splits** to prevent temporal data leakage.
7. Deploy a **Streamlit dashboard** with stock-level risk scores, feature trends, and portfolio-level aggregation.
8. Automate daily data refresh and risk-score generation using **Windows Task Scheduler**.

### Secondary Objectives

- Document survivorship bias exposure and mitigation strategy.
- Produce a complete, auditable data provenance trail (manifests, logs, changelogs).
- Demonstrate feature importance and model interpretability to support stakeholder understanding.
- Achieve a row count exceeding 200,000 valid stock-day observations after cleaning.

---

## 5. Scope

### In Scope

- Daily OHLCV data from `yfinance` (NSE tickers, `.NS` suffix) for a curated universe of approximately 300 stocks.
- Historical period: approximately 5-7 years (2018-2025), subject to data availability.
- Benchmark data: Nifty 50 (`^NSEI`) for market-relative features.
- Feature engineering from daily data only (no intraday, no order book).
- Binary supervised classification (High-Risk vs Normal), single-step horizon (next trading day or N-day forward).
- Unsupervised anomaly scoring (Isolation Forest) as a complementary, interpretable signal.
- Composite Liquidity-Risk Score derived from academic proxies.
- Streamlit dashboard for visualization and monitoring.
- Automated daily refresh designed for local Windows deployment.
- Documentation of all methodology, architecture, and design decisions.

### Out of Scope

- Real-time or intraday data (tick, minute, or hourly data).
- Actual bid-ask spread data or order-book depth.
- Fundamental data (P/E, balance sheet, earnings).
- Sentiment analysis or news data.
- Options or derivatives data.
- Portfolio optimization or trade execution.
- Deep learning models (LSTM, Transformer, etc.).
- Cloud infrastructure (AWS, GCP, Azure) in the initial version.
- Micro-cap stocks (market cap below Nifty Smallcap 250 threshold) in the initial universe.
- Legal or regulatory compliance analysis.

---

## 6. Research Hypotheses

| ID | Hypothesis | Expected Direction |
|---|---|---|
| H1 | Amihud illiquidity ratio is positively correlated with future high-risk events | Positive |
| H2 | Abnormally low volume (relative to 20-day average) precedes increased price gap frequency | Positive |
| H3 | Small-cap stocks exhibit systematically higher Amihud ratios than large-caps | Positive |
| H4 | Market-stress periods (high benchmark volatility) amplify individual stock liquidity risk | Positive |
| H5 | Rolling return z-scores can differentiate high-risk from normal stock-day regimes | Positive |
| H6 | Isolation Forest anomaly scores correlate with periods later labeled as High-Risk Events | Positive |
| H7 | Random Forest outperforms Logistic Regression on precision for the minority High-Risk class | Positive |

---

## 7. Success Criteria

### Data Quality
- >= 200,000 valid stock-day rows after all cleaning and warm-up-period removal.
- <= 5% missing values per feature column across the final feature dataset.
- All tickers verified against NSE trade-able list; failed tickers logged and excluded.
- Benchmark data (^NSEI) available for the full historical window.

### Model Performance
- Baseline Logistic Regression achieves ROC-AUC >= 0.55 on chronological hold-out.
- Best supervised model achieves ROC-AUC >= 0.65 on walk-forward validation.
- Precision-Recall AUC reported alongside ROC-AUC (due to class imbalance).
- No evidence of temporal data leakage (validated by strict chronological splits).
- Feature importances are interpretable and directionally consistent with domain knowledge.

### Engineering
- Full pipeline runs end-to-end on target hardware in under 30 minutes.
- Daily refresh script completes successfully on first run after implementation.
- Streamlit dashboard loads within 10 seconds on local machine.
- All data stored as Parquet; no CSVs committed to Git.

### Documentation
- All 12 audit documents produced and internally consistent.
- At least 45 features catalogued with formulas, lookback periods, and leakage notes.
- Data dictionary accurately reflects the final feature dataset schema.

---

## 8. Limitations (Acknowledged at Outset)

| Limitation | Explanation |
|---|---|
| **Proxy-only liquidity** | Daily OHLCV cannot directly measure bid-ask spreads, order-book depth, or actual execution costs. All "liquidity" measures are academically validated proxies. |
| **Survivorship bias** | yfinance only provides data for currently listed or recently delisted stocks. Stocks delisted due to failure are likely missing. This will be documented but cannot be fully corrected without a paid database. |
| **No intraday resolution** | Risk scores are daily granularity only. Intraday liquidity crises within a single trading day are invisible. |
| **Yahoo Finance reliability** | yfinance depends on undocumented Yahoo Finance endpoints. Data may be unavailable for extended periods, and ticker symbol changes may break historical continuity. |
| **Target label subjectivity** | The "High-Risk Event" target is defined by rule-based thresholds (e.g., Amihud > 90th percentile), not independently observed ground-truth risk events. |
| **GPU not essential** | Classical ML on tabular data does not require GPU acceleration. |
| **Indian market specifics** | Circuit breakers, exchange-level halts, and dividend/bonus adjustment errors in Yahoo Finance data can create spurious signals. |
| **No redistribution** | Yahoo Finance data is subject to terms of service. Raw data files must not be redistributed in any public repository. |

---

## 9. Deliverables Summary

| Deliverable | Format | Audience |
|---|---|---|
| 12 Audit Documents | Markdown in docs/ | Academic evaluators, developer |
| Feature Dataset | Parquet in data/processed/ | Developer, modelling phase |
| Trained Models | Joblib in models/ | Pipeline, dashboard |
| Prediction Archive | Parquet in data/predictions/ | Dashboard, monitoring |
| Streamlit Dashboard | Python app in app/ | All stakeholders |
| Final Report | PDF/Markdown in reports/ | Academic evaluators |
| GitHub Repository | Public or private repo | Recruiters, evaluators |
| Slide Deck | PPTX/PDF in reports/ | Presentation |

---

## 10. Academic and Professional Value

**Academic value:**
- Demonstrates end-to-end applied ML: data engineering, feature engineering, supervised and unsupervised ML, evaluation, deployment.
- Uses academically cited liquidity proxies (Amihud 2002, Corwin-Schultz 2012).
- Applies rigorous time-series validation (walk-forward, no data leakage).
- Produces interpretable models appropriate for financial decision support.

**Resume / professional value:**
- Full-stack quant ML project: pipeline, modelling, dashboard, and automation.
- Domain specificity: Indian equity market, liquidity risk, market microstructure proxies.
- Demonstrates familiarity with financial data challenges (survivorship bias, corporate actions, data quality).
- Deployable Streamlit application with automated daily refresh.
