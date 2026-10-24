# ML METHODOLOGY
## ML-Based Liquidity and Trading-Risk Intelligence for Indian Equities

**Version:** 1.0
**Status:** Pre-Implementation Methodology Document

---

## 1. The Core ML Formulation Decision

### Problem: What Are We Predicting?

The project must address two related but distinct questions:

1. **Descriptive / diagnostic:** How liquid is this stock today? (Current state assessment)
2. **Predictive:** Will this stock enter a high-risk liquidity/trading condition in the next N trading days? (Forward-looking prediction)

These require different approaches and must not be conflated.

### Decision: Dual-Output Architecture

The system will produce **two distinct outputs** per stock per day:

**Output 1: Composite Liquidity-Risk Score (LRS)**
- A rule-based, formula-driven composite score computed from academic proxies.
- Describes the CURRENT liquidity and trading-risk state of the stock.
- NOT a machine learning prediction. Does not use a target variable.
- Range: 0 (most liquid, lowest risk) to 100 (most illiquid, highest risk).
- Interpretable, transparent, and auditable by non-technical stakeholders.

**Output 2: High-Risk Event Probability (ML Prediction)**
- A probability output from a trained supervised classifier.
- Predicts whether a HIGH-RISK event will occur in the next 5 trading days.
- Trained on historically labeled data where the target is defined by rule-based thresholds (see Section 3).
- Provides a forward-looking, data-driven signal complementing the current-state LRS.

**Optional Output 3: Historical Anomaly Score (Unsupervised)**
- An Isolation Forest anomaly score computed on all historical stock-day observations.
- Labels individual stock-days as "historically unusual" in a supervised-free manner.
- Used for exploratory analysis and as an additional feature for the supervised model.
- Does NOT predict future risk — it only describes historical unusualness.

---

## 2. Composite Liquidity-Risk Score (LRS) — Design

### What It Represents

The LRS is a daily score per stock summarizing the stock's current liquidity and trading-risk state. It is NOT a machine learning prediction. It is a transparency-first, academically grounded composite measure.

### Component Scores

The LRS is computed as a weighted average of ranked sub-scores:

| Component | Source Feature | Weight | Direction | Academic Basis |
|---|---|---|---|---|
| Illiquidity Score | amihud_ma20 percentile rank | 25% | Higher = worse | Amihud (2002) |
| Spread Score | cs_spread_ma10 percentile rank | 20% | Higher = worse | Corwin-Schultz (2012) |
| Volume Drought Score | 1 - turnover_ratio (when <1) percentile | 15% | Lower turnover = worse | Stoll (2000) |
| Volatility Score | vol_20d percentile rank | 20% | Higher = worse | Standard |
| Price Gap Score | overnight_gap_abs percentile rank | 10% | Higher = worse | Standard |
| Market-Relative Score | idiosyncratic_vol percentile rank | 10% | Higher = worse | Merton (1987) |

**Percentile ranking:** Each component is ranked cross-sectionally (across all stocks on the same day) to produce a 0-100 percentile score. The weighted average of percentile scores is the LRS.

**Why percentile ranking?** Raw Amihud ratios and spread estimates have very different scales and distributions across cap segments. Percentile ranking normalizes these differences and makes the composite score interpretable.

**Calibration:** Weights are initialized based on academic literature emphasis. They should be re-examined empirically during EDA to ensure no single component dominates.

### LRS Interpretation Bands

| LRS Range | Label | Interpretation |
|---|---|---|
| 0-25 | LOW RISK | Normal liquidity; typical trading conditions |
| 25-50 | MODERATE RISK | Slight deterioration; monitor |
| 50-75 | HIGH RISK | Meaningful liquidity stress; caution advised |
| 75-100 | VERY HIGH RISK | Severe illiquidity; potential trading difficulty |

---

## 3. Supervised Learning Target Definition

### The Forward-Looking High-Risk Event (HRE)

**Target variable:** `hre_5d` (High-Risk Event within 5 trading days)

**Definition:** A stock-day is labeled as HRE = 1 if ANY of the following conditions occur on any of the NEXT 5 trading days (t+1 through t+5):

| Condition | Threshold | Feature Used |
|---|---|---|
| Extreme illiquidity spike | amihud_ratio > 95th percentile (cross-sectional on that future day) | F27 |
| Severe volume drought | volume_ratio < 0.2 (volume less than 20% of 20-day average) | F25 |
| Extreme overnight gap | overnight_gap_abs > 5% | F41 |
| LRS exceeds critical level | LRS > 75 | Composite LRS |

**HRE = 1 if ANY condition triggers on any of the 5 future days. HRE = 0 otherwise.**

### Justification for 5-Day Forward Window

- **1-day forward:** Too noisy; single-day extremes may not represent genuine liquidity stress.
- **5-day forward:** Approximately 1 trading week; actionable for most investors (position can be unwound over a week).
- **10+ day forward:** Prediction accuracy likely degrades; not actionable on a daily basis.

### Threshold Justification

- 95th percentile for Amihud: Captures only extreme illiquidity events, not normal variation.
- 20% volume ratio: Volume less than 1/5 of average represents a meaningful trading drought.
- 5% overnight gap: Large gaps in Indian stocks often indicate circuit-breaker level moves or news shocks.
- LRS > 75: Corresponds to the "VERY HIGH RISK" band defined above.

**[ESTIMATE — These thresholds will be empirically validated during EDA. They should be adjusted if the resulting class balance is worse than 95:5 or better than 70:30.]**

### Expected Class Balance

Historical experience with similar threshold-based targets for mid/small-cap stocks suggests approximately 10-20% positive class rate (HRE = 1). This is a significant imbalance but manageable. [ESTIMATE]

---

## 4. Class Imbalance Handling

Expected class balance: approximately 80-90% negative (HRE = 0) vs 10-20% positive (HRE = 1).

**Techniques to apply:**

| Technique | Application | Notes |
|---|---|---|
| `class_weight='balanced'` | Logistic Regression, Random Forest | Scikit-learn built-in; weights loss by inverse class frequency. Preferred first approach. |
| SMOTE (oversampling) | Optional; test in EDA | Generates synthetic minority class samples. Use only within each training fold, NEVER across folds. |
| Threshold tuning | Post-training | Adjust decision threshold from default 0.5 to maximize F1 or precision/recall trade-off for HRE=1 class. |
| Undersampling majority | Optional; use if SMOTE degrades performance | Randomly remove majority class rows from training only. |

**Primary approach: `class_weight='balanced'` for all classifiers.** This is the simplest, leakage-free approach. SMOTE can be explored in a later experimental phase.

---

## 5. Unsupervised Learning: Isolation Forest

### Purpose

Isolation Forest is used SEPARATELY from the supervised classifier. Its purpose is to:
1. Identify stock-day observations that are historically unusual based on the feature distribution.
2. Provide an anomaly score that can be used as an interpretive overlay on the dashboard.
3. Optionally, use the anomaly score as an additional feature in the supervised model.

### Important Distinction

**Isolation Forest detects historical anomalies. It does NOT predict future risk.**

A stock-day receiving a high anomaly score means it was unusual relative to the training distribution. It does not mean the stock will have high risk tomorrow.

### Configuration

| Parameter | Value | Rationale |
|---|---|---|
| contamination | 0.05 (adjustable) | Expected proportion of anomalous observations; set to 5% as initial estimate |
| n_estimators | 100 | Standard; increase to 200 if compute allows |
| max_samples | 'auto' | Uses min(256, n_samples) by default |
| random_state | 42 | Reproducibility |

### Features Used for Isolation Forest

A subset of 12-15 features capturing the main dimensions of liquidity and risk:
- amihud_ratio, amihud_z20
- volume_ratio, volume_z20
- vol_20d, vol_ratio_5_20
- daily_range, range_z20
- overnight_gap_abs
- cs_spread_est
- nifty_vol_20d (market context)
- return_z20

### Anomaly Score Output

- `isolation_score`: Continuous score in range approximately [-0.5, 0.5]; negative = anomalous.
- `isolation_flag`: 1 if predicted anomaly (-1 from IsolationForest.predict), 0 otherwise.
- Rescaled to 0-100 for dashboard display: `anomaly_score_scaled = (0.5 + isolation_score) * 100`.

---

## 6. Supervised Model Selection

### Model 1: Logistic Regression (Baseline)

**Role:** Primary baseline. Must be established before any complex model.

| Attribute | Detail |
|---|---|
| Library | sklearn.linear_model.LogisticRegression |
| Regularization | L2 (default); tune C via cross-validation |
| Solver | lbfgs (default) or saga for large datasets |
| Class weight | balanced |
| Purpose | Linear baseline; interpretable coefficients; leakage sanity check |
| Interpretability | HIGH (coefficients directly readable) |
| Expected performance | Moderate ROC-AUC; may miss non-linear patterns |

### Model 2: Random Forest Classifier

**Role:** Primary ensemble model. Expected to outperform Logistic Regression.

| Attribute | Detail |
|---|---|
| Library | sklearn.ensemble.RandomForestClassifier |
| n_estimators | 100-200 |
| max_depth | 5-10 (tune via cross-validation; limit to prevent overfitting) |
| min_samples_leaf | 50 (prevents fitting to noise in imbalanced classes) |
| Class weight | balanced_subsample |
| Feature importance | Gini importance + permutation importance |
| Expected performance | Higher ROC-AUC; captures non-linear relationships |
| RAM usage | ~200-400 MB for 200 trees on 300k rows |

### Model 3: HistGradientBoostingClassifier

**Role:** Alternative boosting model. Often outperforms Random Forest on tabular data.

| Attribute | Detail |
|---|---|
| Library | sklearn.ensemble.HistGradientBoostingClassifier |
| max_iter | 200-300 |
| max_leaf_nodes | 31 (default) |
| l2_regularization | 0.1 |
| class_weight | balanced |
| Native NaN handling | Yes — can handle NaN in features without imputation |
| Expected performance | Competitive with or better than Random Forest |
| Speed | Faster than RandomForest on large datasets |

### Why Not Include Other Models?

| Model | Decision | Reason |
|---|---|---|
| SVM | Excluded | Slow on 300k+ rows; poor scalability |
| KNN | Excluded | Very slow prediction; not suitable for real-time scoring |
| XGBoost | Optional extension | Excellent but adds GPU/C++ dependency; HGBT is a simpler equivalent |
| LSTM / RNN | Excluded | Deep learning; out of scope; overkill for this dataset |
| Neural Networks | Excluded | Black-box; not aligned with interpretability goal |
| Decision Tree (single) | Used in EDA only | Illustrative; too simple for production |

---

## 7. Validation Strategy: Chronological Walk-Forward

### Why Walk-Forward, Not K-Fold?

Standard random K-fold cross-validation is PROHIBITED for time-series financial data because:
- It allows future data to be in the training set and past data in the test set.
- This creates data leakage: the model "sees" future market conditions.
- It produces overly optimistic performance estimates.

### Walk-Forward Validation Design

**Method:** Expanding window walk-forward (also called rolling origin cross-validation).

```
|--- FOLD 1 ---|
  TRAIN: 2018-2020  |  TEST: 2021 (Q1)

|------ FOLD 2 ------|
  TRAIN: 2018-2021Q1  |  TEST: 2021 (Q2)

|--------- FOLD 3 ---------|
  TRAIN: 2018-2021Q2  |  TEST: 2021 (Q3)

... continuing to present
```

**Parameters:**
- Training window: Expanding (grows with each fold) — preferred over rolling window for this dataset size.
- Test window: 1 quarter (approximately 60 trading days) per fold.
- Minimum training size: 2 years (approximately 490 trading days per stock).
- Number of folds: Approximately 10-16 folds covering 2021-2025.
- Gap between train and test: 1 trading day (to simulate real-world next-day prediction).

**Implementation:** `sklearn.model_selection.TimeSeriesSplit(n_splits=10)` with careful date-based filtering. Note: TimeSeriesSplit in scikit-learn splits row indices, not dates — care must be taken to align date-based splits with the actual temporal structure when the dataset contains multiple stocks.

### Key Leakage Prevention Rules

1. **Fit scalers within each fold:** StandardScaler is fit only on training rows and applied to test rows.
2. **Compute LRS percentile ranks within each fold:** Cross-sectional percentile ranks must use only training-set data for percentile computation.
3. **No global statistics on full dataset:** Do not use full-dataset mean, std, or percentiles in any feature that is used as a model input.
4. **Target label computed separately:** The HRE target uses future data (t+1 to t+5); this is by design and is NOT leakage as long as the target is excluded from model inputs.
5. **SMOTE (if used) applied only within training folds:** Never fit SMOTE on data that includes the test fold.

---

## 8. Evaluation Metrics

### Primary Metrics

| Metric | Why Used | Priority |
|---|---|---|
| ROC-AUC | Threshold-independent; measures overall discrimination; standard in imbalanced classification | HIGH |
| Precision-Recall AUC (PR-AUC) | More informative than ROC-AUC for imbalanced classes; focus on minority (HRE=1) class | HIGH |
| Precision at HRE=1 | Out of flagged stocks, how many actually had HRE? Critical for actionability | HIGH |
| Recall at HRE=1 | Of all actual HRE events, how many did the model catch? | HIGH |
| F1-Score (HRE=1) | Harmonic mean of precision and recall for minority class | MEDIUM |

### Secondary Metrics

| Metric | Use |
|---|---|
| Brier Score | Calibration of probability outputs |
| Log Loss | Overall probability calibration |
| Confusion Matrix | Visualize false positive/negative patterns |
| Lift Curve | How much better than random for top-K flagged stocks |

### Performance Baselines

| Baseline | Description | Expected |
|---|---|---|
| Random classifier | AUC = 0.50 | ROC-AUC = 0.50 |
| Always predict HRE=0 | Accuracy = 85% but PR-AUC = 0.15 (class frequency) | Degenerate |
| Amihud threshold rule | Simple rule: flag if amihud_z20 > 2 | ROC-AUC ~0.58-0.65 (estimate) |
| Logistic Regression | Full feature set | ROC-AUC target >= 0.60 |
| Random Forest | Full feature set | ROC-AUC target >= 0.65 |

Any model that does not outperform the Amihud threshold rule must be investigated for issues.

---

## 9. Robustness Checks

| Check | Description |
|---|---|
| Out-of-sample holdout | Reserve the most recent 1 year as a final holdout; never touch until final evaluation |
| Permutation test | Shuffle target labels and retrain; performance should drop to ~0.50 |
| Feature importance stability | Run feature importance across all walk-forward folds; flag features with highly unstable rankings |
| Cap-segment subgroup analysis | Evaluate model separately on large/mid/small-cap subsets; performance should be reasonable across all segments |
| Market regime sensitivity | Compare model performance during high-volatility periods (e.g., COVID-19 crash, 2022 rate rise) vs. normal periods |
| Temporal stability | Plot rolling ROC-AUC over the walk-forward folds; should not show systematic degradation |
| Label sensitivity | Re-run with slightly different target thresholds (e.g., 90th vs 95th percentile Amihud) and check stability |

---

## 10. Summary: Recommended ML Approach

```
Output 1 (Current State):  Composite LRS (rule-based, no ML, fully interpretable)
  - Weighted average of percentile-ranked academic proxies
  - Range 0-100, four risk bands
  - Updated daily, no model artifact needed

Output 2 (Forward Prediction):  HRE Probability (supervised ML)
  - Target: HRE_5d (binary; any of 4 trigger conditions in next 5 days)
  - Features: 55 engineered features (F01-F55)
  - Models: Logistic Regression (baseline), Random Forest, HistGradientBoosting
  - Validation: Expanding-window walk-forward (10 folds)
  - Class weight: balanced
  - Metrics: ROC-AUC, PR-AUC, Precision/Recall at HRE=1
  - Final evaluation: Reserved 1-year holdout

Output 3 (Historical Anomaly): Isolation Forest Score (unsupervised)
  - Fit on training data; applied to all historical and new observations
  - NOT a prediction — historical unusualness detector
  - Used as interpretive overlay and optional ML feature
```
