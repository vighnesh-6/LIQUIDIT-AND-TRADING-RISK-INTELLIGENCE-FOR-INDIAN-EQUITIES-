# MARKET EVENT CALENDAR SPECIFICATION
## ML-Based Liquidity and Trading-Risk Intelligence for Indian Equities

**Version:** 1.0  
**Status:** Pre-Implementation Specification & Design Document  
**Target Path:** `data/events/market_events_template.csv`  
**Analysis Module:** `notebooks/09_event_analysis.ipynb`

---

## 1. Overview & Objectives

In financial market microstructure, liquidity risk does not manifest uniformly across time; rather, it clusters violently around systemic market-wide shocks. To rigorously analyze how liquidity evaporates and how trading risk propagates across the Indian equity spectrum (Large, Mid, and Small caps), this project incorporates a **manually curated calendar of major market-wide events**.

### Primary Objectives:
1. Provide an authoritative, timestamped chronological benchmark of systemic shocks.
2. Enable quantitative **event study analysis** in `notebooks/09_event_analysis.ipynb` to evaluate liquidity dislocations across the `[-5, +5]` trading day window.
3. Compare how large-cap anchors withstand liquidity drains compared to mid-cap and small-cap segments.
4. Investigate the predictive and co-movement properties of the supplementary India VIX during systemic stress periods.

---

## 2. Explicit Exclusions (Out-of-Scope Data)

To maintain methodological focus, data hygiene, and avoid uncontrolled noise, the following categories are **strictly excluded**:

- ❌ **Individual stock news:** Corporate press releases, management changes, product launches, contracts won/lost.
- ❌ **Company earnings & financial results:** Quarterly earnings announcements, guidance releases, earnings call transcripts.
- ❌ **Analyst commentary & broker ratings:** Target price revisions, broker reports, institutional rebalancing estimates.
- ❌ **Financial NLP / Sentiment analysis:** Twitter/X sentiment, news article scraping, headline NLP.
- ❌ **Intraday micro-events:** Flash crashes lasting under 30 minutes, rumors refuted within the same trading session.

**Rationale:** Stock-level news and earnings introduce severe selection bias, high dimensional noise, and scraping liabilities. Systemic liquidity risk is driven primarily by macro, regulatory, and market-wide uncertainty.

---

## 3. Data Schema

The calendar is stored as a version-controlled CSV at `data/events/market_events_template.csv` using the following standardized schema:

| Column | Type | Description | Permitted Values / Constraints |
|---|---|---|---|
| `event_id` | String | Unique identifier for the event | Format: `EVT_YYYY_NNN` (e.g., `EVT_2020_001`) |
| `event_date` | Date (YYYY-MM-DD) | Effective trading day when the market reacted | Must align with an active NSE trading date |
| `event_name` | String | Concise title of the event | Max 60 characters |
| `event_category` | Category | Classification of shock mechanism | `MACROECONOMIC`, `GEOPOLITICAL`, `POLITICAL_ELECTORAL`, `REGULATORY_EXCHANGE`, `SYSTEMIC_CREDIT` |
| `event_description` | String | Factual summary of the shock and market context | Max 250 words |
| `source_url` | String | Authoritative public reference link | Official gazette, RBI, ECI, PIB, or recognized international record |
| `date_confidence` | Category | Precision level of the assigned trading date | `HIGH` (exact session verified), `MEDIUM` (occurred post-market / weekend), `LOW` (multi-day policy lag) |
| `notes` | String | Additional context, market halt details, circuit breakers | Optional qualitative notes |

---

## 4. Event Categories & Definitions

### 4.1 MACROECONOMIC
- Union Budget presentation dates (when policy announcements trigger severe market repricing).
- Unscheduled emergency monetary policy actions by the Reserve Bank of India (RBI).
- Global macroeconomic shocks (e.g., US Federal Reserve emergency rate hikes, major currency crises).

### 4.2 GEOPOLITICAL
- Military conflicts directly affecting international trade, energy prices, or foreign portfolio flows (e.g., Russia-Ukraine war onset Feb 2022, Middle East escalations).
- Severe border confrontations impacting national defense and sovereign sentiment.

### 4.3 POLITICAL & ELECTORAL
- Indian General Election (Lok Sabha) result declaration days (e.g., May 23, 2019; June 4, 2024).
- Key state election outcomes causing nationwide market turbulence.

### 4.4 REGULATORY & EXCHANGE DISRUPTIONS
- Exchange-wide circuit breaker halts triggered on the National Stock Exchange (NSE).
- Nationwide COVID-19 pandemic lockdowns (March 2020).
- Major SEBI regulatory structural interventions (e.g., Peak Margin rules implementation, T+1 settlement transitions).
- NSE technical outages or mid-session trading halts.

### 4.5 SYSTEMIC CREDIT & FINANCIAL CONTAGION
- Defaults or credit freezes at large non-banking financial corporations (NBFCs) triggering systemic liquidity crunches (e.g., IL&FS default September 2018).
- High-profile institutional moratoria or bank reconstructions (e.g., Yes Bank moratorium March 2020).
- Widespread corporate governance or investigative shocks with market-wide contagion (e.g., Adani Group Hindenburg report January 2023).

---

## 5. Event Study Methodology (Phase 9 Implementation)

In `notebooks/09_event_analysis.ipynb`, each recorded event $k$ on date $T_k$ is analyzed using standard econometric event-study frameworks:

```
[--- Baseline Normal Window ---]       [-- Pre-Event --]  [Event]  [-- Post-Event --]
        T_k - 20 to T_k - 6             T_k - 5 to T_k - 1   T_k    T_k + 1 to T_k + 5
```

### Metrics Evaluated in the Event Window:
1. **LRS Shock Trajectory:** Cross-sectional mean and 90th percentile LRS across Large, Mid, and Small caps.
2. **Amihud Illiquidity Spike:** Ratio of event-window Amihud to the baseline 20-day average:
   $$\text{Amihud Multiple} = \frac{\text{amihud\_ratio}_{T_k}}{\text{amihud\_ma20}_{T_k - 6}}$$
3. **Effective Spread Widening:** Change in Corwin-Schultz spread (`cs_spread_est`) across market cap tiers.
4. **Volume Drying vs. Liquidation Surge:** Identification of liquidity dry-ups (`volume_ratio < 0.2`) versus panic liquidation turnover spikes.
5. **VIX Interaction:** India VIX level and single-day percentage change relative to realized stock return drawdowns.

---

## 6. Curated Initial Candidate Events (2018–2025)

The table below illustrates the verified historical candidate events to be populated in `data/events/market_events_template.csv`:

| Event ID | Date | Event Name | Category | Date Conf. | Public Source / Context |
|---|---|---|---|---|---|
| `EVT_2018_001` | 2018-09-21 | IL&FS Credit Default Crisis | `SYSTEMIC_CREDIT` | HIGH | RBI / NSE public disclosures; sparked NBFC liquidity crisis |
| `EVT_2019_001` | 2019-02-26 | Balakot Airstrike & Market Reaction | `GEOPOLITICAL` | HIGH | Public defense communique; immediate intraday volatility spike |
| `EVT_2019_002` | 2019-05-23 | Lok Sabha 2019 Election Results | `POLITICAL_ELECTORAL` | HIGH | Election Commission of India (ECI) official results |
| `EVT_2019_003` | 2019-09-20 | Corporate Tax Cut Announcement | `MACROECONOMIC` | HIGH | Ministry of Finance; massive positive price shock & turnover |
| `EVT_2020_001` | 2020-03-06 | Yes Bank Moratorium | `SYSTEMIC_CREDIT` | HIGH | RBI notification; severe banking liquidity uncertainty |
| `EVT_2020_002` | 2020-03-13 | COVID Crash Lower Circuit Halt | `REGULATORY_EXCHANGE` | HIGH | NSE circular; trading halted for 45 minutes on 10% lower circuit |
| `EVT_2020_003` | 2020-03-23 | Nationwide Lockdown Lower Circuit | `REGULATORY_EXCHANGE` | HIGH | NSE circular; second 10% lower circuit halt of the crisis |
| `EVT_2021_001` | 2021-02-24 | NSE Telecom Glitch Trading Halt | `REGULATORY_EXCHANGE` | HIGH | NSE official press release; trading halted across cash & derivatives |
| `EVT_2022_001` | 2022-02-24 | Russia-Ukraine War Outbreak | `GEOPOLITICAL` | HIGH | International news; global equity selloff and crude oil surge |
| `EVT_2022_002` | 2022-05-04 | RBI Off-Cycle 40 bps Repo Rate Hike | `MACROECONOMIC` | HIGH | RBI Monetary Policy Committee emergency statement |
| `EVT_2023_001` | 2023-01-25 | Hindenburg Report on Adani Group | `SYSTEMIC_CREDIT` | HIGH | Public release; systemic contagion across infrastructure/banks |
| `EVT_2024_001` | 2024-06-04 | Lok Sabha 2024 Election Results Day | `POLITICAL_ELECTORAL` | HIGH | ECI official counting; Nifty 50 single-day plunge of ~6% |

---

## 7. Storage and Maintenance Protocol

- The calendar CSV is tracked in Git under `data/events/`.
- Updates must include a credible, verifiable `source_url`.
- Any addition or date revision requires updating `docs/PROJECT_STATUS.md` and logging the rationale in `manifests/`.
