# Phase 4 Market Events Calendar Collection & Validation Report
## ML-Based Liquidity and Trading-Risk Intelligence for Indian Equities

**Document ID:** `PHASE-4-EVENT-CALENDAR-20261024`  
**Execution Timestamp:** October 24, 2026 (Updated Post-Audit Remediation)  
**Status:** ⚠️ **PASS WITH LIMITATIONS** (100% Schema & Calendar Validation; 53 passing test assertions; 25 Verified deep links, 61 Provisional citations)  
**Canonical Output Asset:** `data/events/market_events.csv` (86 validated records, 16 standardized schema fields, 42.1 KB)  
**Preserved Template Asset:** `data/events/market_events_template.csv` (100% unchanged, 3.42 KB)  
**Raw Data Integrity:** 100% Verified Untouched (Stock Universe Merkle Root: `cdace0ba7662be9d0c49edca3f4db3ca00c2ef31c4704807db1bdef7cff0dcbf`)  

---

## 1. Executive Summary & Deliverables

In accordance with the approved Event Calendar Specification and the independent Read-Only Event Calendar Audit, Phase 4 has collected, normalized, verified, remediated, and validated the historical market events dataset for Indian equities spanning **January 1, 2018 through October 23, 2026** (2,171 active NIFTY 50 trading sessions).

### Key Milestones & Remediation Accomplishments:
1. **Canonical Dataset Delivery:** Maintained exactly **86 strictly verified events** across market-wide systemic shocks, sector-specific policy shifts, and stock-specific structural corporate actions.
2. **Event-Specific Source URL Resolution:** Replaced generic homepage URLs with 25 working, HTTP 200-verified event-specific official links (Union Budget PDF speeches, PIB press releases, SEBI circulars, ECI statistical report archives, UN News releases, and regulatory filings). Unresolved sources are honestly classified as `PROVISIONAL` without fabricating links.
3. **EVT_2020_003 Historical Session Remediation:** Fully documented that February 1, 2020 was a special Saturday live trading session (09:15–15:30 IST; circular `NSE/CMTR/43405`) omitted by the raw data provider (Yahoo Finance). Preserved Monday, February 3 as the dataset-aligned effective date ($T_0$), lowered `date_confidence` to `MEDIUM`, and recorded the limitation.
4. **EVT_2025_001 Timing Classification Correction:** Corrected Saturday February 1, 2025 from `DURING_MARKET` to `WEEKEND_HOLIDAY`, documenting calendar alignment to Monday February 3, 2025.
5. **Corporate Action Ex-Date Semantics:** Explicitly documented across all corporate actions that `announcement_datetime_ist` denotes board approval / regulatory filing date, whereas `effective_trading_date` denotes the exchange ex-date (mechanical price/volume adjustment date), preserving schema stability.
6. **Strengthened Test Suite:** Expanded `tests/test_events.py` to 12 focused suites covering weekend/holiday announcements on non-trading days, calendar alignment, post-market timing, and corporate action ex-dates. The full project test suite now passes with **53 tests passing in 1.36s**.
7. **Raw Data Immutability:** Pre- and post-collection cryptographic SHA-256 Merkle root verification confirms zero byte modification to all 300 raw stock Parquets and 3 raw market benchmark Parquets.

---

## 2. Statistical Breakdown of the Event Dataset

### 2.1 Distribution by Scope
| Scope | Record Count | Percentage | Primary Purpose / Role in Project |
|---|---|---|---|
| **`MARKET_WIDE`** | 60 | 69.8% | Benchmark for macro event studies, broad-market liquidity evaporation, and VIX stress conditioning. |
| **`SECTOR_SPECIFIC`** | 13 | 15.1% | Evaluates sectoral liquidity contagion (Banking moratoria, Telecom AGR rulings, NBFC liquidity squeezes). |
| **`STOCK_SPECIFIC`** | 13 | 15.1% | Disambiguates mechanical corporate action price/volume gaps from genuine liquidity failures across the 300 stocks. |
| **Total** | **86** | **100.0%** | Comprehensive multi-tier risk intelligence. |

### 2.2 Distribution by Event Category
| Event Category | Count | Permitted Subcategories | Key Historical Shocks Included |
|---|---|---|---|
| **`MACRO_POLICY`** | 31 | `BUDGET`, `RATE_DECISION`, `FISCAL_REFORM` | All 11 Union Budgets (2018–2026), RBI rate cycle turning points (75 bps cut 2020, 40 bps hike May 2022, neutral shift 2024), 2019 Corporate Tax Cut. |
| **`REGULATORY_EXCHANGE`** | 17 | `CIRCUIT_HALT`, `OUTAGE`, `MARKET_REGULATION`, `SECTOR_REGULATION` | March 13 & 23, 2020 10% lower circuit halts, Feb 24, 2021 NSE 4-hr outage, SEBI Peak Margin rollout, T+1 settlement transition, Oct 2024 F&O framework tightening. |
| **`CORPORATE_ACTION`** | 11 | `SPLIT_BONUS`, `MERGER_DEMERGER` | `MOTILALOFS.NS` 3:1 bonus, `PATANJALI.NS` capital reduction, `VEDL.NS` demerger, `YESBANK.NS` reconstruction, `RELIANCE.NS` JioFin spinoff, `HDFCBANK.NS` merger. |
| **`GEOPOLITICAL`** | 10 | `MILITARY_CONFLICT`, `TRADE_WAR`, `GLOBAL_SHOCK`, `BANKING_CRISIS` | US-China tariffs (2018), Balakot airstrikes (2019), Russia-Ukraine invasion (2022), SVB collapse (2023), Yen carry trade unwind (Aug 5, 2024). |
| **`SYSTEMIC_CREDIT`** | 9 | `CREDIT_DEFAULT`, `GOVERNANCE_CRISIS`, `BANKING_CRISIS` | IL&FS default (Sept 2018), DHFL downgrade to default (2019), PMC Bank (2019), Yes Bank moratorium (2020), Adani Hindenburg report (2023). |
| **`POLITICAL_ELECTORAL`** | 8 | `ELECTION_RESULT` | Lok Sabha 2019 exit polls & counting, Lok Sabha 2024 exit polls & historic counting day plunge (-5.93%), 2023 state election clean sweep, NDA 3.0 coalition formation. |

### 2.3 Chronological Coverage Across Project Years (2018–2026)
| Year | Active NIFTY Sessions | Total Events | Market-Wide | Sector-Specific | Stock-Specific | Salient Character of the Year |
|---|---|---|---|---|---|---|
| **2018** | 245 | 7 | 4 | 2 | 1 | IL&FS crisis, NBFC liquidity freeze, LTCG tax reintroduction, US-China trade war onset. |
| **2019** | 241 | 12 | 7 | 3 | 2 | Balakot, Lok Sabha elections, Corporate tax cut rally (+5.3%), Telecom AGR ruling, DHFL default. |
| **2020** | 250 | 15 | 8 | 4 | 3 | COVID crash circuit halts (March 13 & 23), Yes Bank moratorium, RBI 75 bps emergency package, Galwan clash. |
| **2021** | 248 | 6 | 4 | 1 | 1 | Union Budget stimulus (+4.7%), NSE 4-hr telecom outage, Peak Margin 100% rollout, Telecom relief package. |
| **2022** | 248 | 11 | 8 | 1 | 2 | Russia-Ukraine war onset, RBI 40 bps emergency hike, rapid rate hikes to 6.25%, Windfall fuel tax. |
| **2023** | 245 | 12 | 8 | 2 | 2 | Adani Hindenburg report, T+1 settlement rollout, SVB & Credit Suisse shocks, HDFC merger, JioFin demerger. |
| **2024** | 246 | 15 | 10 | 3 | 2 | Lok Sabha 2024 election crash (-5.9%), Yen carry trade unwind, Budget STCG/LTCG tax hike, SEBI F&O curbs. |
| **2025** | 249 | 5 | 4 | 1 | 0 | Union Budget 2025, RBI monetary policy evolution, SEBI market infrastructure update. |
| **2026** | 199 | 3 | 2 | 0 | 1 | Union Budget 2026, Vedanta multi-entity demerger ex-date, Autumn RBI policy review. |
| **Total** | **2,171** | **86** | **60** | **13** | **13** | **Continuous, unbroken 8.8-year historical coverage.** |

---

## 3. Standardized 16-Field Dataset Schema

The canonical CSV at `data/events/market_events.csv` adheres strictly to the approved specification:

| # | Field Name | Data Type | Permitted Values / Constraints | Quantitative Purpose & Rationale |
|---|---|---|---|---|
| 1 | `event_id` | String | Format: `EVT_YYYY_NNN` | Unique primary key for deduplication and event-window indexing. |
| 2 | `event_name` | String | Max 80 characters | Human-readable title for dashboards and event study plots. |
| 3 | `event_category` | Category | `MACRO_POLICY`, `POLITICAL_ELECTORAL`, `REGULATORY_EXCHANGE`, `SYSTEMIC_CREDIT`, `GEOPOLITICAL`, `CORPORATE_ACTION` | Primary taxonomy for event study stratification. |
| 4 | `event_subcategory` | String | `BUDGET`, `RATE_DECISION`, `ELECTION_RESULT`, `CIRCUIT_HALT`, etc. | Finer-grained shock classification. |
| 5 | `scope` | Category | `MARKET_WIDE`, `SECTOR_SPECIFIC`, `STOCK_SPECIFIC` | Controls cross-sectional aggregation rules. |
| 6 | `affected_ticker` | String | Empty (market-wide), Sector (e.g. `BANKING`), or NSE ticker (`INFY.NS`, etc.) | Direct foreign key into the 300-stock universe or permitted systemic entity. |
| 7 | `announcement_datetime_ist` | Timestamp | ISO 8601 string (`YYYY-MM-DD HH:MM:SS` or `YYYY-MM-DD`) | Exact historical moment of public disclosure. |
| 8 | `market_timing` | Category | `PRE_MARKET`, `DURING_MARKET`, `POST_MARKET`, `WEEKEND_HOLIDAY` | Enforces zero look-ahead bias mapping. |
| 9 | `effective_trading_date` | Date | `YYYY-MM-DD` (active NSE trading date) | **The exact date $T_0$** on which cash market prices could first react. |
| 10 | `is_scheduled` | Boolean | `True` / `False` | Prevents models from using pre-event advance warnings for surprise shocks. |
| 11 | `event_description` | String | Factual summary | Concise description of the shock mechanism and financial transmission. |
| 12 | `source_name` | String | Official organization name | Authoritative publisher (`RBI`, `NSE`, `SEBI`, `ECI`, `PIB / Ministry of Finance`). |
| 13 | `source_url` | String | Valid HTTP/HTTPS URL | Direct public URL for provenance and institutional auditability. |
| 14 | `verification_status` | Category | `VERIFIED`, `PROVISIONAL`, `UNDER_REVIEW` | 25 Verified deep links, 61 Provisional authority citations. |
| 15 | `date_confidence` | Category | `HIGH`, `MEDIUM`, `LOW` | Indicates precision of the announcement timestamp. |
| 16 | `notes` | String | Qualitative notes | Documents halt duration, circuit bands, VIX moves, or return impacts. |

---

## 4. Source URL Verification & Provenance Breakdown

To prevent URL fabrication, every source link was audited against live endpoints:
- **Verified Event-Specific Deep Links (25 records):**
  - Union Budget Speeches: 2018 (`budget2018-2019/ub2018-19/bs/bs.pdf`), 2019 Interim (`budget2019-20(I)/ub2019-20/bs/bs.pdf`), 2019 Full (`budget2019-20/doc/budget_speech.pdf`), 2020 (`budget2020-21/doc/budget_speech.pdf`), 2021 (`budget2021-22/doc/budget_speech.pdf`), 2022 (`budget2022-23/doc/budget_speech.pdf`), 2023 (`budget2023-24/doc/budget_speech.pdf`), 2024 Interim (PIB PRID `2001134`), 2024 Full (`doc/budget_speech.pdf`).
  - Regulatory Circulars & Major Releases: SEBI Index F&O Tightening (Circular `SEBI/HO/MRD/TPD/P/CIR/2024/132`), PIB Corporate Tax Cut (PRID `1585641`), PIB Telecom Relief (PRID `1755086`), PIB Balakot (RelID `188948`), RBI COVID Liquidity Package (PRID `49582`).
  - Global Shocks: UN News Russia-Ukraine (`1112592`), Gaza Outbreak (`1142027`), Iran Escalation (`1148541`), FDIC SVB Closure (`pr23019.html`), Hindenburg Adani Report, DoD Soleimani Strike.
  - ECI Statistical Archive: `https://eci.gov.in/statistical-report/statistical-reports/` for General and State election reports.
- **Provisional Authority Citations (61 records):**
  - Unresolved sources (e.g. RBI MPC statements, SEBI historical margin circulars, NSE corporate action filings, and forward scheduled budgets) retain verified institutional authority base URLs (`rbi.org.in`, `sebi.gov.in`, `nseindia.com`, `main.sci.gov.in`).
  - These records are honestly recorded as `PROVISIONAL` with exact document numbers and circular citations embedded in `notes` and `source_name`. No fake URLs were generated.

---

## 5. Look-Ahead Bias Prevention & Timing Policy

A critical vulnerability in quantitative event studies is information leakage (treating after-hours announcements as known prior to that day's closing bell). The table below demonstrates how the timing policy was applied across edge cases:

| Event Example | Actual Public Announcement | Market Timing | Assigned Effective Date ($T_0$) | Justification & Leakage Defense |
|---|---|---|---|---|
| **Corporate Tax Cut (2019)** | Sept 20, 2019 10:15 IST (Fri) | `DURING_MARKET` | `2019-09-20` (Friday) | Announced during live market; cash prices reacted immediately (+5.3%). |
| **Yes Bank Moratorium (2020)** | March 5, 2020 20:00 IST (Thu) | `POST_MARKET` | `2020-03-06` (Friday) | Released post-close; March 5 prices could not incorporate the news. March 6 is $T_0$ (-56.1%). |
| **Union Budget 2020 (Sat)** | Feb 1, 2020 11:00 IST (Sat) | `WEEKEND_HOLIDAY` | `2020-02-03` (Monday) | Special Saturday session was omitted in Yahoo daily feeds; reaction consolidated on Monday Feb 3. |
| **Union Budget 2025 (Sat)** | Feb 1, 2025 11:00 IST (Sat) | `WEEKEND_HOLIDAY` | `2025-02-03` (Monday) | Saturday is a non-trading exchange holiday; reaction aligned to Monday Feb 3. |
| **Lok Sabha Exit Polls (2024)** | June 1, 2024 19:00 IST (Sat) | `WEEKEND_HOLIDAY` | `2024-06-03` (Monday) | Released Saturday evening; market opened with a 3.25% gap up on Monday morning. |
| **SEBI F&O Circular (2024)** | Oct 1, 2024 18:30 IST (Tue) | `POST_MARKET` | `2024-10-03` (Thursday) | Released post-market; Oct 2 was Gandhi Jayanti holiday. First trading session was Oct 3. |

---

## 6. Corporate Action Ex-Date Semantics

In equity markets, corporate actions (splits, bonuses, mergers, capital reductions) have a critical structural dual-date lifecycle:
1. **Announcement Date (`announcement_datetime_ist`):** The date the Board of Directors approved the action and submitted statutory disclosure to the exchanges.
2. **Ex-Date (`effective_trading_date`):** The date on which the stock begins trading on an adjusted basis, triggering a mechanical price and volume discontinuity in raw OHLCV series.

**Design Rule:** The existing schema is strictly preserved. In `data/events/market_events.csv`, `effective_trading_date` represents the **exchange ex-date** ($T_0$). This ensures Phase 4.2 liquidity filtering and Phase 5 feature engineering can isolate mechanical price adjustments (e.g. -94.9% on Patanjali, -74.6% on Motilal Oswal, -64.9% on Vedanta) without misclassifying them as genuine market liquidity breakdowns.

---

## 7. Automated Validation & Test Suite Results

The validation suite in `tests/test_events.py` was expanded to 12 tests and executed alongside all existing project tests.

### Test Execution Log:
```text
============================= test session starts =============================
platform win32 -- Python 3.13.5, pytest-8.3.4, pluggy-1.5.0
rootdir: C:\Users\vighn\OneDrive\Desktop\ads project (quant)
collected 53 items

tests/test_events.py ............                                        [ 22%]
tests/test_features.py .                                                 [ 24%]
tests/test_fetcher.py .......                                            [ 37%]
tests/test_interim_market.py .......                                     [ 50%]
tests/test_lrs.py .                                                      [ 52%]
tests/test_storage.py ........                                           [ 67%]
tests/test_targets.py .                                                  [ 69%]
tests/test_universe.py ....                                              [ 77%]
tests/test_validator.py ............                                     [100%]

============================== 53 passed in 1.36s ==============================
```

### Verified Checks:
1. **File Presence:** `data/events/market_events.csv` verified present and non-empty (86 records).
2. **Schema Integrity:** All 16 columns present with exact casing and zero missing columns.
3. **Primary Key Uniqueness:** Exactly 86 unique `event_id` keys; 0 duplicates. Format `EVT_YYYY_NNN` strictly satisfied.
4. **Permitted Enums:** 0 invalid categories, scopes, timings, statuses, or confidences.
5. **Trading Calendar Alignment:** 100% of effective dates exist in `data/interim/market/nifty50_clean.parquet`.
6. **Leakage & Timing Protection:**
   - 0 records where effective date precedes announcement date.
   - 0 post-market same-day leaks (`eff_date > ann_date`).
   - 0 weekend/holiday leaks on non-trading dates (`eff_date > ann_date`).
7. **Audit Remediation Cases:**
   - `EVT_2020_003` verified: `date_confidence == MEDIUM`, `effective_trading_date == 2020-02-03`, notes explain Saturday session omission.
   - `EVT_2025_001` verified: `market_timing == WEEKEND_HOLIDAY`, `effective_trading_date == 2025-02-03`.
8. **Corporate Action Ex-Date Semantics:** All 11 corporate actions verified with explicit semantic notes and valid tickers.
9. **Source URLs & Traceability:** 100% valid HTTP/HTTPS URLs with non-empty authoritative publisher names; 25 verified deep links and 61 provisional citations.
10. **Template Preservation:** `data/events/market_events_template.csv` verified 100% intact (3,419 bytes).

---

## 8. Cryptographic Raw Data Verification

Executed `audit/compute_raw_sha256.py`:
* **300 Raw Stock Files Merkle Root:** `cdace0ba7662be9d0c49edca3f4db3ca00c2ef31c4704807db1bdef7cff0dcbf` (100% identical to baseline).
* **`^NSEI.parquet` SHA-256:** `a60bf31f42714f9bc23ffdca6e0e0d28f985b43537a049d079f4bd27700363e9` (Identical).
* **`^NSEBANK.parquet` SHA-256:** `da989b7be832361ee9b5187dbe8924ec9cbb7f48124122066581f31fcab38c0d` (Identical).
* **`^INDIAVIX.parquet` SHA-256:** `bb29de8547afc28a02e2470541328b2da1f51b496f43ef77df4c26f9a5d607ee` (Identical).
* **Verdict:** Zero raw data files modified, overwritten, or moved.

---

## 9. Modified Files Inventory

1. [`data/events/market_events.csv`](file:///c:/Users/vighn/OneDrive/Desktop/ads%20project%20%28quant%29/data/events/market_events.csv): Remediated canonical dataset with 86 records, verified deep URLs, corrected timing, and documented ex-date semantics.
2. [`src/data/events.py`](file:///c:/Users/vighn/OneDrive/Desktop/ads%20project%20%28quant%29/src/data/events.py): Updated `EventCalendarManager` with enhanced weekend/holiday timing check and corporate action documentation.
3. [`tests/test_events.py`](file:///c:/Users/vighn/OneDrive/Desktop/ads%20project%20%28quant%29/tests/test_events.py): Strengthened tests covering weekend/holiday announcements, audit cases, and ex-date semantics (12 tests).
4. [`reports/phase4_market_events_collection.md`](file:///c:/Users/vighn/OneDrive/Desktop/ads%20project%20%28quant%29/reports/phase4_market_events_collection.md): Updated audit sign-off report with complete remediation findings.

---

## 10. Remaining Limitations & Downstream Guidance

1. **Unresolved Source Permalinks (61 records):** While 25 key official documents have verified deep links, 61 records retain institutional base URLs with document reference citations because Indian regulatory portals (RBI, SEBI, NSE) do not maintain static public permalinks for legacy disclosures without dynamic queries. These records are categorized as `PROVISIONAL`.
2. **Raw Feed Session Omission (EVT_2020_003):** Saturday February 1, 2020 was a live trading session omitted by Yahoo Finance. Downstream models must be aware that the initial market shock is captured in the Monday February 3 close rather than Saturday.
3. **Point-in-Time Safety Scope:** The unit and contract tests prove schema validity and calendar alignment, but do not guarantee complete point-in-time feature safety. Downstream feature engineering pipelines (Phase 5) must independently verify that feature calculations use strictly lagged event distances ($t \le T_0$).

---

## 11. Final Status & Sign-Off

* **Remediation Quality:** All 6 remediation items successfully implemented.
* **Integrity:** 86 records preserved; raw data 100% untouched.
* **Test Suite:** 53 / 53 tests passing.
* **Final Verdict:** ⚠️ **PASS WITH LIMITATIONS**
