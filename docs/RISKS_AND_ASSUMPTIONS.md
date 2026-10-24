# RISKS AND ASSUMPTIONS
## ML-Based Liquidity and Trading-Risk Intelligence for Indian Equities

**Version:** 1.0
**Status:** Pre-Implementation Risk Register

---

## Risk Severity Scale

| Level | Description |
|---|---|
| CRITICAL | May invalidate results or make project infeasible |
| HIGH | Significant impact on quality or scope; requires active mitigation |
| MEDIUM | Manageable impact; mitigation recommended |
| LOW | Minor impact; acceptable with documentation |

---

## 1. Data Risks

### R-D1: Survivorship Bias
**Severity:** HIGH
**Description:** Using current NSE index constituent lists means the universe consists only of stocks that have survived long enough to currently be listed. Stocks delisted due to business failure, fraud, or regulatory action are excluded. This systematically omits the most extreme historical liquidity failures.
**Impact:** Model trained on survivors may underestimate tail risk. Risk scores may be systematically optimistic for struggling stocks. Academic validity is reduced.
**Mitigation:**
- Explicitly acknowledge survivorship bias in all model documentation, reports, and dashboard.
- Include a disclaimer on all prediction outputs.
- Add a note in the dashboard: "This model was trained exclusively on surviving stocks and may not capture pre-delisting risk patterns."
- Cite academic literature on survivorship bias in finance ML (e.g., Brown, Goetzmann, Ross 1992).
- Document as a known limitation that cannot be corrected with free data sources.

### R-D2: yfinance Unreliability
**Severity:** HIGH
**Description:** yfinance relies on undocumented Yahoo Finance endpoints that can change, break, or return incorrect data without warning. It is not an official data API.
**Impact:** Historical download may fail partially or completely. Daily refresh may silently fetch incorrect adjusted prices. Ticker changes may cause historical discontinuities.
**Mitigation:**
- Pin yfinance to a specific tested version.
- Implement validation checks on downloaded data (reasonable price ranges, expected date coverage, no sudden adjustment spikes).
- Cross-validate a sample of tickers against a secondary free source (e.g., manually check 5 large-caps against NSE website) during Phase 1.
- Store raw Parquet immediately after download; re-process can recover from corrupt clean datasets.

### R-D3: Corporate Action Adjustment Errors
**Severity:** MEDIUM**
**Description:** Yahoo Finance's adjustment for splits, bonus issues, and dividends can be incorrect or lagged, particularly for Indian equities where bonus issues are common. This can create artificial price gaps in the adjusted series.
**Impact:** Features derived from price returns (F01-F10) may contain spurious signals around ex-dates. The Corwin-Schultz estimator is particularly sensitive to artificial gaps.
**Mitigation:**
- Apply an extreme-move filter: flag any single-day return beyond ±50% as a potential data error.
- During EDA, visually inspect price series around major corporate actions for selected tickers.
- Document that corporate action errors are a known data quality risk for yfinance.

### R-D4: Zero-Volume and Stale-Price Rows
**Severity:** MEDIUM**
**Description:** Some tickers show zero trading volume on days when circuit breakers, exchange suspensions, or data provider issues prevent trading. The price column may remain unchanged for multiple days.
**Impact:** Zero-volume rows cause division-by-zero errors in the Amihud ratio. Stale prices create false "zero volatility" signals.
**Mitigation:**
- Identify zero-volume rows explicitly; exclude from Amihud computation; flag with `zero_vol_flag` (Feature F35).
- Identify stale-price streaks (same close for 3+ days); mark with `stale_price_flag` and exclude from rolling calculations.
- Log the count of zero-volume and stale-price rows per ticker.

### R-D5: Missing Historical Membership Data
**Severity:** MEDIUM**
**Description:** NSE Indices provides current constituent lists only. Historical membership (which stocks were in Nifty 100 in 2018) requires a paid subscription.
**Impact:** A stock currently in Nifty 100 may have been in Nifty Midcap 150 in 2018. The `cap_segment` label applied to historical data is the current segment, not the historical one.
**Mitigation:**
- Accept this as a known limitation.
- Treat `cap_segment` as a current-date label used for subgroup analysis, not as a historical classification.
- Document clearly: "Cap segment labels reflect current index membership as of [universe download date] and may not reflect historical membership."

### R-D6: Data Redistribution Risk
**Severity:** HIGH (Legal)
**Description:** Yahoo Finance's Terms of Service prohibit commercial redistribution of data. Uploading raw data to a public GitHub repository or cloud storage may violate ToS.
**Impact:** Legal/compliance issue; academic project could be called into question.
**Mitigation:**
- `data/` directory is in `.gitignore`; never commit data files to Git.
- If project is submitted as a public repository, ensure no data files are included.
- Include a clear disclaimer in README: "Data sourced from Yahoo Finance via yfinance for personal academic use. Raw data not redistributed."

---

## 2. Methodology Risks

### R-M1: Target Label Subjectivity
**Severity:** HIGH
**Description:** The High-Risk Event (HRE_5d) target is defined by rule-based thresholds applied to the stock's own features (e.g., Amihud > 95th percentile). There is no independent ground-truth label for "high trading risk."
**Impact:** If the thresholds are poorly calibrated, the trained model may effectively learn to predict its own proxy metrics rather than actual risk. Threshold choice is subjective.
**Mitigation:**
- Justify all thresholds in `ML_METHODOLOGY.md` with reference to academic literature.
- Perform sensitivity analysis: vary thresholds and check model stability.
- Cross-validate: ensure HRE events correlate with observable market stress events (known circuit-breaker days, market crashes).
- Report threshold sensitivity as part of robustness testing (Phase 9).

### R-M2: Temporal Data Leakage
**Severity:** CRITICAL**
**Description:** Using any future information (t+1 and beyond) in model inputs is temporal data leakage. This is the most common and dangerous mistake in financial ML.
**Impact:** Leakage produces artificially high performance metrics that collapse in production.
**Mitigation:**
- Strictly enforce the rule: all feature inputs use data through and including day t only.
- All rolling windows are backward-looking (computed on [t-N, t]).
- StandardScaler and LRS percentile ranks are fit on training data only within each fold.
- The HRE_5d target uses t+1 to t+5 data — this is by design and is the prediction target, NOT an input.
- Perform the permutation test (shuffle labels; performance should drop to ~0.50) as a leakage sanity check.
- Perform temporal validation (earlier training folds should not perform significantly worse than later ones due to leakage).

### R-M3: Overfitting / Spurious Correlations
**Severity:** HIGH
**Description:** With 55 features, the model may fit noise, particularly for tree-based methods on small datasets.
**Impact:** High training performance but poor out-of-sample performance; misleading results.
**Mitigation:**
- Limit `max_depth` for Random Forest; use regularization for HGBT.
- Reserve 1-year holdout; evaluate only at the end.
- Check feature importances for stability across walk-forward folds.
- Prefer parsimony: if HistGradientBoosting with 20 features achieves the same PR-AUC as Random Forest with 55, prefer the simpler model.

### R-M4: Class Imbalance
**Severity:** MEDIUM**
**Description:** HRE events may be rare (5-15% positive class), leading classifiers to default to predicting all zeros.
**Impact:** Misleadingly high accuracy; zero recall for the minority class.
**Mitigation:**
- Use `class_weight='balanced'` for all classifiers.
- Report PR-AUC and Recall for HRE=1, not overall accuracy.
- If positive class < 5%, revisit threshold definition to produce a more balanced target.

### R-M5: Proxy Validity Limitations
**Severity:** MEDIUM**
**Description:** All liquidity measures are OHLCV-derived proxies. They do not directly measure bid-ask spread, order-book depth, or actual execution impact.
**Impact:** Model may not generalize to actual trading difficulty. Claims about "liquidity" must be carefully hedged.
**Mitigation:**
- Always refer to measures as "liquidity proxies" in all documents and the dashboard.
- Include the disclaimer: "Features measure statistical proxies for liquidity and trading activity from daily closing data. They do not directly measure bid-ask spreads, order-book depth, or actual execution costs."
- Cite academic papers that validate these proxies against observed microstructure data.

### R-M6: Market Regime Change
**Severity:** MEDIUM**
**Description:** A model trained on 2018-2022 data may not generalize to 2023-2025 market conditions if the market structure changes (e.g., new regulations, new types of participants, COVID-era anomalies).
**Impact:** Model performance may degrade over time without retraining.
**Mitigation:**
- Monitor rolling validation performance across walk-forward folds.
- Flag if the most recent fold's performance drops significantly below earlier folds.
- Plan periodic manual model retraining (every 3-6 months).
- Dashboard displays the training-data cutoff date for transparency.

---

## 3. Operational Risks

### R-O1: Laptop Must Be On and Awake
**Severity:** MEDIUM**
**Description:** Windows Task Scheduler requires the laptop to be powered on and not sleeping at the scheduled time (17:30 IST).
**Impact:** Missed refreshes if the laptop is off or hibernating.
**Mitigation:**
- Enable "Run task as soon as possible after a scheduled start is missed" in Task Scheduler.
- This ensures the pipeline runs as soon as the laptop is turned on after a missed schedule.
- Document: "Daily refresh requires the laptop to be on at some point each trading day."

### R-O2: yfinance Rate Limiting Worsens Over Time
**Severity:** MEDIUM**
**Description:** Yahoo Finance may increase anti-bot protection, making bulk downloads increasingly difficult.
**Impact:** Pipeline may fail consistently; project becomes unsustainable.
**Mitigation:**
- Keep raw historical data locally; only fetch incremental (new) rows daily.
- Implement aggressive rate limiting (1-2 second delay between tickers).
- Fallback: manually download data via yfinance download_multiprocessing=False for troublesome tickers.
- Document alternative sources (Stooq, investing.com CSV exports) as fallbacks.

### R-O3: yfinance API Version Breaking Change
**Severity:** HIGH
**Description:** The yfinance library occasionally introduces breaking changes (column name changes, parameter renames) between versions.
**Impact:** Pipeline breaks on update; historical data may be reformatted incorrectly.
**Mitigation:**
- Pin exact yfinance version in requirements.txt.
- Monitor yfinance GitHub releases before updating.
- Add a version compatibility test in `tests/test_fetcher.py`.

### R-O4: Disk Space Exhaustion (Low probability)
**Severity:** LOW
**Description:** Long-running daily appends may eventually consume significant disk space.
**Impact:** Pipeline fails on write; predictions not updated.
**Mitigation:**
- Current estimates show <500 MB total even after 3 years of daily predictions.
- Parquet compression ensures disk space poses no realistic constraint on modern drives.
- Add a disk space check in health_check.py (warn if < 5 GB free).

---

## 4. Presentation and Academic Risks

### R-A1: Evaluator Questions Proxy Validity
**Severity:** MEDIUM**
**Description:** Academic evaluators may question whether OHLCV proxies are valid substitutes for actual liquidity measures.
**Impact:** Reduced academic score if proxy limitations are not proactively disclosed.
**Mitigation:**
- Pre-empt by citing Amihud (2002) and Corwin-Schultz (2012) directly.
- Use the exact disclaimer language from this document in the final report.
- Acknowledge the limitation in the project presentation before being asked.

### R-A2: Dashboard Appears "Too Simple" Without Real-Time Data
**Severity:** LOW**
**Description:** End-of-day predictions may seem underwhelming compared to real-time trading platforms.
**Impact:** Stakeholder expectation mismatch.
**Mitigation:**
- Clearly frame the project as a daily risk-intelligence tool, not a trading platform.
- Emphasize the academic and methodological rigor over real-time capability.
- Compare favorably to paid analytics tools by highlighting free data and interpretable ML.

---

## 5. Key Assumptions (Documented)

| # | Assumption | Basis | If Wrong |
|---|---|---|---|
| A1 | NSE trades ~247 days/year | Historical NSE holiday records | Row-count estimates shift by <3% |
| A2 | ≥90% of 300 tickers download successfully from yfinance | Research on yfinance India coverage | Reduce universe; accept fewer stocks |
| A3 | Most Nifty 500 stocks have 7yr history on Yahoo Finance | Observed for large/mid caps; unverified for small-caps | Reduce to 5yr window |
| A4 | HRE positive class rate will be 5-20% | Domain knowledge + threshold design | Recalibrate thresholds in EDA |
| A5 | Random Forest achieves ROC-AUC ≥ 0.65 | Literature benchmarks on similar tasks | Document lower performance; focus on PR-AUC |
| A6 | Laptop will be powered on at 17:30 IST at least 4 days/week | User behavior | Configure "run on missed schedule" |
| A7 | Yahoo Finance data is free for personal academic use | ToS interpretation; widespread practice | Consult ToS; restrict to offline use |
| A8 | Float32 precision is adequate for all features | Standard practice in financial ML | Switch to float64 at RAM cost |
