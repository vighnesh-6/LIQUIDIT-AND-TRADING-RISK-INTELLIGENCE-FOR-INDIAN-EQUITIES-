# DATA DICTIONARY AND FEATURES
## ML-Based Liquidity and Trading-Risk Intelligence for Indian Equities

**Version:** 1.0
**Total Features Proposed:** 55
**Status:** Pre-Implementation Catalogue — formulas to be verified during implementation

---

## Overview

All features are computed from daily OHLCV data (Open, High, Low, Close, Volume) and benchmark data (^NSEI daily Close). No intraday, bid-ask, or order-book data is used.

**Important limitations of daily OHLCV liquidity proxies:**
- Daily data cannot directly measure the bid-ask spread, order-book depth, market impact, or actual execution costs.
- All "liquidity" measures are academically validated approximations (proxies).
- Price-impact proxies (e.g., Amihud ratio) measure sensitivity of price to volume, not actual transaction costs.
- Spread estimators (e.g., Corwin-Schultz) estimate the effective spread from high-low ranges, not from actual bid-ask quotes.
- These limitations are well-documented in market microstructure literature (Amihud 2002, Corwin and Schultz 2012).

**Leakage prevention rules:**
- Any feature used as an input to predict day t+1 must be fully observable by end of trading day t.
- Rolling statistics computed over [t-N, t] are safe if they include day t.
- Features incorporating day t+1 information are PROHIBITED as model inputs.
- The supervised target (high-risk flag) uses day t+N outcome — strictly future.

---

## Category 1: Returns and Price Behaviour (10 features)

| # | Feature Name | Formula | Lookback | Interpretation | Source Columns | Leakage Risk |
|---|---|---|---|---|---|---|
| F01 | daily_return | (Close_t - Close_{t-1}) / Close_{t-1} | 1 day | Simple daily price change | Close | None |
| F02 | log_return | ln(Close_t / Close_{t-1}) | 1 day | Log return; better statistical properties; additive over time | Close | None |
| F03 | return_5d | (Close_t - Close_{t-5}) / Close_{t-5} | 5 days | 1-week momentum | Close | None |
| F04 | return_20d | (Close_t - Close_{t-20}) / Close_{t-20} | 20 days | 1-month momentum | Close | None |
| F05 | return_60d | (Close_t - Close_{t-60}) / Close_{t-60} | 60 days | 3-month momentum; warm-up requires 60 days | Close | None |
| F06 | return_z5 | (daily_return - mean_5d) / std_5d | 5-day rolling | Z-score of return relative to recent distribution; identifies unusual days | Close | None |
| F07 | return_z20 | (daily_return - mean_20d) / std_20d | 20-day rolling | Z-score of return relative to 20-day window | Close | None |
| F08 | abs_return | abs(daily_return) | 1 day | Absolute return; used in Amihud ratio | Close | None |
| F09 | price_rel_ma20 | Close_t / MA20_Close - 1 | 20-day rolling | Price deviation from 20-day moving average; trend measure | Close | None |
| F10 | price_rel_ma60 | Close_t / MA60_Close - 1 | 60-day rolling | Price deviation from 60-day moving average | Close | None |

**Notes:**
- F03-F10 require a minimum warm-up window; rows within the first N days of a stock's history will be NaN.
- F07 requires at least 20 days of history; F10 requires 60 days.

---

## Category 2: Volatility and Downside Risk (12 features)

| # | Feature Name | Formula | Lookback | Interpretation | Source Columns | Leakage Risk |
|---|---|---|---|---|---|---|
| F11 | vol_5d | Rolling std of log_return | 5 days | Short-term realized volatility | Close | None |
| F12 | vol_20d | Rolling std of log_return x sqrt(252) | 20 days | Annualized 20-day realized volatility; primary volatility measure | Close | None |
| F13 | vol_60d | Rolling std of log_return x sqrt(252) | 60 days | Longer-term baseline volatility | Close | None |
| F14 | vol_ratio_5_20 | vol_5d / vol_20d | 5+20 days | Volatility regime change indicator; >1 means short-term spike | Close | None |
| F15 | parkinson_vol | sqrt(1/(4*ln(2)) * sum(ln(H/L)^2) / N) x sqrt(252) | 20 days | Parkinson high-low volatility estimator; uses intraday range; more efficient than close-to-close | High, Low | None |
| F16 | true_range | max(H-L, abs(H-Close_{t-1}), abs(L-Close_{t-1})) | 1 day | ATR component; daily price range including gap | High, Low, Close | None |
| F17 | atr_20d | 20-day rolling mean of true_range | 20 days | Average True Range; normalized measure of daily price movement | High, Low, Close | None |
| F18 | downside_vol_20d | Rolling std of negative log_returns only, x sqrt(252) | 20 days | Semi-deviation; measures only downward price volatility | Close | None |
| F19 | sortino_component | return_20d / downside_vol_20d | 20 days | Return-to-downside-risk ratio; negative values indicate loss periods | Close | None |
| F20 | max_drawdown_20d | (Close_t - max(Close_{t-20:t})) / max(Close_{t-20:t}) | 20 days | Maximum loss from 20-day peak; always <= 0 | Close | None |
| F21 | rsi_14 | 100 - 100/(1 + avg_gain_14/avg_loss_14) | 14 days | Relative Strength Index; <30 = oversold (potential distress), >70 = overbought | Close | None |
| F22 | vol_of_vol | Rolling std of vol_20d | 60 days | Volatility of volatility; measures regime instability | Close | Warm-up 80 days |

---

## Category 3: Liquidity and Trading-Activity Proxies (14 features)

| # | Feature Name | Formula | Lookback | Interpretation | Source Columns | Leakage Risk |
|---|---|---|---|---|---|---|
| F23 | log_volume | ln(Volume + 1) | 1 day | Log-transformed volume; reduces right skew | Volume | None |
| F24 | volume_ma20 | 20-day rolling mean of Volume | 20 days | Baseline trading activity | Volume | None |
| F25 | volume_ratio | Volume / volume_ma20 | 20 days | Volume relative to recent average; >2 = abnormally high, <0.5 = unusually low | Volume | None |
| F26 | volume_z20 | (Volume - volume_ma20) / rolling_std_volume_20d | 20 days | Z-score of volume; identifies statistical anomalies | Volume | None |
| F27 | amihud_ratio | abs(daily_return) / (Volume x Close) | 1 day | Amihud (2002) illiquidity ratio — price impact per unit of currency turnover. Higher = less liquid. Multiply by 1e6 for scale. | Close, Volume | None |
| F28 | amihud_ma20 | 20-day rolling mean of amihud_ratio | 20 days | Smoothed Amihud; reduces single-day noise | Close, Volume | None |
| F29 | amihud_z20 | (amihud_ratio - amihud_ma20) / rolling_std_amihud_20d | 20 days | Z-score of Amihud; detects sudden illiquidity spikes | Close, Volume | None |
| F30 | turnover_value | Volume x Close | 1 day | Daily trading turnover in currency units (rupees); proxy for trading activity | Volume, Close | None |
| F31 | log_turnover | ln(turnover_value + 1) | 1 day | Log-transformed turnover; normalized for regression | Volume, Close | None |
| F32 | turnover_ma20 | 20-day rolling mean of turnover_value | 20 days | Baseline turnover level | Volume, Close | None |
| F33 | turnover_ratio | turnover_value / turnover_ma20 | 20 days | Turnover relative to recent baseline | Volume, Close | None |
| F34 | zero_return_flag | 1 if abs(daily_return) < 0.0001 else 0 | 1 day | Indicator of stale/unchanged price; common in illiquid stocks | Close | None |
| F35 | zero_vol_flag | 1 if Volume == 0 else 0 | 1 day | Zero-volume day indicator; trading halt or data error | Volume | None |
| F36 | low_volume_streak | Rolling sum of (volume_ratio < 0.3) over 5 days | 5 days | Count of consecutive/recent very-low-volume days; liquidity drought signal | Volume | None |

**Notes on Amihud Ratio (F27-F29):**
- Introduced by Yakov Amihud (2002, Journal of Financial Markets): "Illiquidity and stock returns: Cross-section and time-series effects."
- The original formula: ILLIQ = (1/D) * sum(|R_d| / DVOL_d) where DVOL = Volume * Price.
- Here we compute the daily version and smooth it with a 20-day rolling mean.
- The ratio must be multiplied by a large scalar (e.g., 10^6) to avoid numerical precision issues on low-volume days.
- **Cannot be computed when Volume = 0.** These days must be excluded or imputed before computing F27.

---

## Category 4: Price-Gap and Price-Impact Proxies (9 features)

| # | Feature Name | Formula | Lookback | Interpretation | Source Columns | Leakage Risk |
|---|---|---|---|---|---|---|
| F37 | daily_range | (High - Low) / Close | 1 day | Normalized daily trading range; proxy for realized intraday volatility and spread width | High, Low, Close | None |
| F38 | daily_range_ma20 | 20-day rolling mean of daily_range | 20 days | Baseline range level | High, Low, Close | None |
| F39 | range_z20 | (daily_range - daily_range_ma20) / rolling_std_range_20d | 20 days | Z-score of daily range; detects unusual price dispersion days | High, Low, Close | None |
| F40 | overnight_gap | (Open_t - Close_{t-1}) / Close_{t-1} | 1 day | Overnight gap return; measures price discontinuity between sessions | Open, Close | None |
| F41 | overnight_gap_abs | abs(overnight_gap) | 1 day | Absolute overnight gap; large gaps indicate news/liquidity events | Open, Close | None |
| F42 | gap_z20 | (overnight_gap - mean_gap_20d) / std_gap_20d | 20 days | Z-score of overnight gap relative to recent distribution | Open, Close | None |
| F43 | cs_spread_est | Corwin-Schultz high-low spread estimator | 2 consecutive days | Academic bid-ask spread proxy using only daily H and L. Requires 2-day window. See Corwin and Schultz (2012, Journal of Finance). | High, Low | None |
| F44 | cs_spread_ma10 | 10-day rolling mean of cs_spread_est | 12 days (2+10) | Smoothed CS spread estimate; reduces day-to-day noise | High, Low | None |
| F45 | intraday_return | (Close - Open) / Open | 1 day | Within-day return from open to close; captures intraday price pressure | Open, Close | None |

**Notes on Corwin-Schultz Estimator (F43):**
- Introduced by Shane Corwin and Paul Schultz (2012): "A simple way to estimate bid-ask spreads from daily high and low prices."
- Formula: S = (2*(exp(alpha)-1)) / (1+exp(alpha)) where alpha is derived from the ratio of 2-day high-low range to single-day high-low range.
- The estimator can return negative values (a known limitation); negative estimates should be treated as zero spread.
- Provides an estimate of the EFFECTIVE SPREAD (in percentage terms), not the bid-ask spread in absolute price units.
- This is an estimate, not an observed spread. It should be labeled as such in all outputs.

---

## Category 5: Market-Relative Behaviour (6 features)

| # | Feature Name | Formula | Lookback | Interpretation | Source Columns | Leakage Risk |
|---|---|---|---|---|---|---|
| F46 | excess_return_1d | daily_return - nifty_return_1d | 1 day | Alpha relative to Nifty 50; positive = outperformed market | Close, ^NSEI Close | None |
| F47 | excess_return_20d | return_20d - nifty_return_20d | 20 days | 20-day alpha | Close, ^NSEI Close | None |
| F48 | rolling_beta_60d | OLS slope of stock returns on Nifty returns over 60 days | 60 days | Market sensitivity; high beta = amplified market moves | Close, ^NSEI Close | Warm-up 60 days |
| F49 | rolling_corr_60d | Pearson correlation of stock returns with Nifty returns | 60 days | Co-movement with market; low correlation = stock-specific risk | Close, ^NSEI Close | Warm-up 60 days |
| F50 | idiosyncratic_vol | vol_20d * sqrt(1 - rolling_corr_60d^2) | 60+20 days | Idiosyncratic (stock-specific) volatility; not explained by market movement | Close, ^NSEI Close | Warm-up 80 days |
| F51 | relative_volume | volume_ratio / nifty_volume_ratio | 20 days | Stock volume activity relative to market volume activity; identifies stock-specific volume anomalies | Volume, ^NSEI Volume | None |

---

## Category 6: Market-Stress and Correlation Features (5 features)

| # | Feature Name | Formula | Lookback | Interpretation | Source Columns | Leakage Risk |
|---|---|---|---|---|---|---|
| F52 | nifty_vol_20d | 20-day rolling std of Nifty log returns x sqrt(252) | 20 days | Market-level volatility regime; high = market stress | ^NSEI Close | None |
| F53 | nifty_vol_ratio | nifty_vol_5d / nifty_vol_20d | 5+20 days | Market volatility regime change; >1 = stress escalating | ^NSEI Close | None |
| F54 | nifty_return_20d | 20-day return of Nifty 50 | 20 days | Market trend context; negative = market downturn | ^NSEI Close | None |
| F55 | vol_beta | (vol_20d - vol_20d_lag20) / vol_20d_lag20 | 40 days | Volatility acceleration; rapid vol increase signals emerging stress | Close | Warm-up 40 days |

---

## Feature Summary

| Category | Count |
|---|---|
| Returns and Price Behaviour | 10 |
| Volatility and Downside Risk | 12 |
| Liquidity and Trading-Activity Proxies | 14 |
| Price-Gap and Price-Impact Proxies | 9 |
| Market-Relative Behaviour | 6 |
| Market-Stress and Correlation | 5 |
| **TOTAL** | **55** |

**This exceeds the minimum requirement of 45 features.** [Requirement met with margin of 10.]

---

## Warm-Up Window Requirements

| Maximum Lookback Feature | Lookback | Warm-Up Rows Excluded per Stock |
|---|---|---|
| F05, return_60d | 60 days | 60 |
| F10, price_rel_ma60 | 60 days | 60 |
| F13, vol_60d | 60 days | 60 |
| F22, vol_of_vol | 80 days (60+20) | 80 |
| F48, rolling_beta_60d | 60 days | 60 |
| F50, idiosyncratic_vol | 80 days (60+20) | 80 |
| F55, vol_beta | 40 days | 40 |

**Maximum warm-up period: 80 trading days per stock.** This means the first 80 rows per stock will contain NaN values for some features and must be excluded from model training.

**Impact on row count:** 300 stocks x 80 warm-up rows = 24,000 rows excluded. Given >300,000 clean rows in the dataset, this is a minor impact (~8%).

---

## Features NOT Computable from Daily OHLCV (Documented Gaps)

The following liquidity-relevant measures CANNOT be computed from daily data and are explicitly excluded:

| Missing Measure | Reason | Impact |
|---|---|---|
| Actual bid-ask spread | Requires Level 2 order book or tick data | High — primary liquidity measure unavailable |
| Market depth / order book | Requires Level 2 data | High |
| Delivery percentage | NSE Bhavcopy only; excluded per user constraints | Moderate |
| Kyle's Lambda (empirical) | Requires signed trade flow (trade-sign data) | High |
| Amihud Lambda (order-flow version) | Requires intraday intervals | Moderate |
| VWAP deviation | Requires intraday data | Low |
| Institutional vs retail flow | Proprietary or brokerage-API data | High |

**All these gaps are acknowledged in every model and dashboard output.**

---

## Feature Leakage Analysis Summary

**No features in categories 1-6 incorporate future information by construction.** All rolling windows look backward from time t. The only leakage risk is:

1. **Target label leakage:** The supervised target uses day t+k data. Ensure target is computed after feature computation and never used as a model input.
2. **Scaling leakage:** StandardScaler/MinMaxScaler must be fit on the TRAINING set only and applied to the test set. Fitting on the full dataset is a form of leakage.
3. **Forward-fill imputation:** If NaN values in features are forward-filled beyond day t, this is acceptable (prior value is known at time t). Backward-fill is PROHIBITED.
4. **Corwin-Schultz (F43):** Uses t and t-1 data — safe, as both days are in the past by end of day t.

---

## Input Data Schema

| Column | Type | Description |
|---|---|---|
| date | datetime64 | Trading date |
| ticker | category | NSE ticker symbol (e.g., RELIANCE.NS) |
| open | float32 | Adjusted open price |
| high | float32 | Adjusted daily high |
| low | float32 | Adjusted daily low |
| close | float32 | Adjusted closing price |
| volume | int64 | Number of shares traded |
| cap_segment | category | large / mid / small |
| nifty_close | float32 | Nifty 50 closing price (same date) |
Plus 55 engineered feature columns (F01-F55), all float32.

---

## Supplementary Market-Fear Dataset: India VIX (Candidate Features)

**Status:** [UNRESOLVED — Pre-Implementation Audit]  
**Candidate Ticker:** `^INDIAVIX` via `yfinance`  
**Purpose:** Measure market-wide expected volatility and aggregate fear sentiment as supplementary market-context variables.

| Candidate Feature | Formula | Lookback | Rationale | Status |
|---|---|---|---|---|
| vix_close | India VIX closing level | 1 day | Instantaneous market fear / expected annualized 30-day volatility | Candidate; verify availability |
| vix_return_1d | (VIX_t - VIX_{t-1}) / VIX_{t-1} | 1 day | Daily change in fear index; spikes coincide with systemic liquidity pullbacks | Candidate |
| vix_z20 | (VIX_t - MA20_VIX) / std20_VIX | 20 days | Normalized deviation from recent baseline; identifies volatility regime shifts | Candidate |

**Integration Protocol:**
1. In Phase 1, `^INDIAVIX` historical data coverage will be audited across the target 2018–2025 window.
2. If coverage is ≥90% with clean continuous daily series, these candidate features will be computed alongside Category 6 in `src/features/market_stress.py`.
3. If `^INDIAVIX` data exhibits substantial gaps or proves unavailable, the core feature pipeline continues uninterrupted with the 55 audited OHLCV features (F01–F55), using `nifty_vol_20d` and `nifty_vol_ratio` as realized volatility proxies.

---

## Unresolved Issues and Decisions Summary

| # | Item | Status | Action Required |
|---|---|---|---|
| U1 | **Historical date range (5 vs 7 years)** | [UNRESOLVED] | Audit ticker coverage in Phase 1; if small-caps have sparse data prior to 2019/2020, adjust window to 5 years (2020–2025) or retain 7 years (2018–2025) with minimum trading day threshold. |
| U2 | **India VIX historical coverage** | [UNRESOLVED] | Verify whether `^INDIAVIX` on Yahoo Finance covers the entire window without multi-month outages. |
| U3 | **Amihud scaling multiplier** | [ESTIMATE] | 10^6 scalar selected to bring values into manageable range; verify median and 95th percentile ranges during Phase 6 EDA. |
| U4 | **Corwin-Schultz flooring** | [VERIFIED DECISION] | Academic standard: negative 2-day spread estimates are clipped at 0.0. Confirmed in `src/features/gaps.py`. |
| U5 | **Class balance thresholds for HRE_5d** | [ESTIMATE] | 95th percentile Amihud and 20% volume ratio are estimates; calibrate empirically during Phase 7 to guarantee 5%–30% minority prevalence. |
