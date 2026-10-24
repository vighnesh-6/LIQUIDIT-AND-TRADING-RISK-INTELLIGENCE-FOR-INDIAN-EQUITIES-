# DATA SOURCE AUDIT
## ML-Based Liquidity and Trading-Risk Intelligence for Indian Equities

**Version:** 1.0
**Status:** Pre-Implementation Audit
**Label convention:** [VERIFIED] = confirmed from public documentation or search results. [ESTIMATE] = calculated or inferred. [UNRESOLVED] = must be tested during implementation.

---

## 1. Primary Data Source: Yahoo Finance via yfinance

### Source Identity

| Field | Detail |
|---|---|
| **Library** | `yfinance` (Python package) |
| **PyPI URL** | https://pypi.org/project/yfinance/ |
| **GitHub** | https://github.com/ranaroussi/yfinance |
| **Underlying Source** | Yahoo Finance (unofficial API; undocumented endpoints) |
| **Access Method** | Python library (`yf.download()`, `yf.Ticker()`) |
| **Cost** | Free (no API key required) |
| **Authentication** | None required |
| **Rate Limits** | Undocumented; empirically observed HTTP 429 errors at high request rates |

### Ticker Format for Indian Stocks [VERIFIED]

| Exchange | Suffix | Example | Index Tickers |
|---|---|---|---|
| NSE (National Stock Exchange) | `.NS` | `RELIANCE.NS` | `^NSEI` (Nifty 50), `^NSEBANK` |
| BSE (Bombay Stock Exchange) | `.BO` | `RELIANCE.BO` | `^BSESN` (Sensex) |

**Decision: Use exclusively NSE (`.NS`) tickers.** NSE has higher liquidity and trading volume than BSE for most stocks. `^NSEI` will serve as the benchmark index.

### Data Fields Available [VERIFIED]

| Field | yfinance Column | Notes |
|---|---|---|
| Date | Index (DatetimeIndex) | Trading day date |
| Open | `Open` | Opening price (adjusted or unadjusted based on `auto_adjust` param) |
| High | `High` | Daily high |
| Low | `Low` | Daily low |
| Close | `Close` | Closing price |
| Adjusted Close | `Close` when `auto_adjust=True` | Split/dividend adjusted; default in recent yfinance versions |
| Volume | `Volume` | Number of shares traded |

**Note:** When `auto_adjust=True` (the default in yfinance >= 0.2), all price columns (Open, High, Low, Close) are already adjusted for splits and dividends. There is no separate `Adj Close` column in this mode. When `auto_adjust=False`, `Adj Close` is returned separately.

**Decision: Use `auto_adjust=True` for all downloads.** This ensures corporate-action-adjusted prices are used consistently. The raw (unadjusted) prices will not be separately stored.

### Coverage Assessment [VERIFIED from research]

| Segment | Coverage Level | Notes |
|---|---|---|
| Nifty 50 constituents | EXCELLENT | Data typically goes back to early 2000s for most stocks |
| Nifty Next 50 (Nifty 100 - Nifty 50) | VERY GOOD | Most have 10+ years of data |
| Nifty Midcap 150 constituents | GOOD | Most have 5-10 years; some newer listings may have gaps |
| Nifty Smallcap 250 constituents | MODERATE | Coverage drops; some stocks may fail entirely |
| Micro-caps (below Nifty 500) | POOR | Many missing; not recommended for this project |
| SME/Emerge platform stocks | VERY POOR | Largely absent from Yahoo Finance |

### Historical Depth [VERIFIED]

- Large-cap NSE stocks: typically available from ~2000-2005 onward. [VERIFIED]
- Mid-cap NSE stocks: typically from ~2008-2012 onward. [VERIFIED]
- Small-cap NSE stocks: typically from ~2010-2015 onward; newer listings from IPO date. [VERIFIED]
- Target window (2018-2025): approximately 7 years. Most Nifty 500 stocks should have coverage for this window. [ESTIMATE — requires verification per ticker.]

### Known Limitations [VERIFIED]

1. **Unofficial API:** Yahoo Finance does not publish official API documentation or SLAs. The yfinance library reverse-engineers undocumented endpoints. These may change or break without notice.

2. **Rate Limiting:** Bulk downloads of 300+ tickers will trigger HTTP 429 responses if done too aggressively. The library has built-in retry logic, but rate limiting must be handled explicitly in the pipeline.

3. **Corporate Action Errors:** Dividend and split adjustments occasionally contain errors or lags. Bonus issues common in Indian markets may not be adjusted promptly. This can produce artificial price gaps in the adjusted series.

4. **Ticker Symbol Changes:** Indian companies occasionally change their NSE ticker symbols. Yahoo Finance may not synchronize these changes immediately, causing some tickers to return empty data frames.

5. **Delisted Stocks:** Data for stocks delisted from NSE becomes frozen or disappears from Yahoo Finance. This creates survivorship bias — stocks that were delisted due to business failure or regulatory action are typically inaccessible.

6. **Zero-Volume Days:** Some tickers occasionally show zero volume on days when trading was actually halted by circuit breakers or exchange suspensions. These require special treatment during cleaning.

7. **Stale Prices:** Some thinly traded stocks may show the same closing price for multiple consecutive days (no trades occurred; price is carried forward). These rows must be identified and handled.

8. **No Bid-Ask Spread:** Daily OHLCV contains no bid-ask spread, order flow, or market depth information. All liquidity measures will be academic proxies derived from price and volume.

9. **Terms of Service:** Yahoo Finance's ToS prohibits commercial redistribution of data. For an academic project, personal use is generally acceptable, but the raw data files must not be committed to a public repository or redistributed.

### Recommended yfinance Version

- Pin to a specific version (e.g., `yfinance==0.2.x`) to prevent breaking changes.
- Check PyPI for the latest stable version at implementation time.
- [UNRESOLVED: Exact version to pin pending verification of API stability at implementation time.]

---

## 2. Benchmark / Market Index Data

### Nifty 50 Index

| Field | Detail |
|---|---|
| **yfinance Ticker** | `^NSEI` |
| **Description** | NSE Nifty 50 — top 50 stocks by market cap and liquidity on NSE |
| **Use in Project** | Market-relative feature computation (beta, correlation, excess return, benchmark volatility) |
| **Coverage** | Available from 1999 onward via yfinance [VERIFIED] |
| **Availability** | Generally reliable; frequently updated by Yahoo Finance |

### Other Index Tickers Available via yfinance [VERIFIED]

| Index | Ticker | Use Case |
|---|---|---|
| Nifty Bank | `^NSEBANK` | Sector-specific benchmark (optional) |
| BSE Sensex | `^BSESN` | Alternative benchmark (not used; using NSE as primary) |
| Nifty IT | Not reliably available | — |
| Nifty Midcap 150 | Not available as direct index | ETF proxy: `MID150BEES.NS` |
| Nifty Smallcap 250 | Not available as direct index | ETF proxy available; not used in primary pipeline |

### 2.2 Supplementary Market-Fear Index: India VIX

| Field | Detail |
|---|---|
| **Candidate yfinance Ticker** | `^INDIAVIX` |
| **Description** | NSE India Volatility Index — measures 30-day expected annualized market volatility |
| **Role in Project** | Supplementary market-fear and expected-volatility indicator for market stress analysis |
| **Status** | [VERIFIED — October 2026] |
| **Historical Availability** | Verified: 2,156 continuous trading days (2018-01-01 to 2026-10-23) with 0 null values across OHLCV. Full historical coverage confirmed. |
| **Fallback Protocol** | Fallback not required; continuous daily data verified. Realized volatility features remain available as standard inputs. |

**Decision on Benchmark vs. Supplementary Fear Index:**
- `^NSEI` is the **mandatory core benchmark** for all market-relative calculations (beta, correlation, alpha).
- `^INDIAVIX` is verified and incorporated as the **supplementary fear dataset** for volatility regime and market-stress analysis.

---

## 3. Stock Universe Definition Source

### NSE Indices Limited (NSE Indices)

| Field | Detail |
|---|---|
| **URL** | https://www.niftyindices.com |
| **Purpose** | Obtain constituent lists for Nifty 100, Nifty Midcap 150, Nifty Smallcap 250 |
| **Format** | Official CSV downloads (`ind_nifty100list.csv`, `ind_niftymidcap150list.csv`, `ind_niftysmallcap250list.csv`) |
| **Access** | Free, publicly available without authentication [VERIFIED — October 2026] |
| **Update Frequency** | Semi-annual/quarterly reconstitution |
| **Limitation** | Provides CURRENT constituents only; historical membership data requires purchase |

**Decision: Download current constituent lists from NSE Indices website.** [VERIFIED — Constituent lists obtained directly without login; zero segment overlap confirmed.]

### NSE Website (NSE India)

| Field | Detail |
|---|---|
| **URL** | https://www.nseindia.com |
| **Purpose** | Cross-reference ticker symbols; verify that tickers are actively traded |
| **Access** | Publicly accessible; some pages require JavaScript rendering |
| **Use** | Verification only; not used for bulk data download |

---

## 4. Additional Data Sources Considered

### 4.1 NSE Bhavcopies (Daily Trade Files)

| Field | Detail |
|---|---|
| **URL** | https://www.nseindia.com/all-reports |
| **Format** | CSV (daily Bhavcopy files) |
| **Content** | OHLCV, delivery percentage, circuit limits for all NSE stocks |
| **Advantage** | Official NSE data; includes delivery percentage (useful liquidity proxy) |
| **Limitation** | Requires daily manual download or web scraping (JavaScript-heavy site) |
| **Decision** | **EXCLUDED** from primary pipeline. The user's constraint prohibits scraping or dependence on APIs from Indian stock-market websites. yfinance provides equivalent OHLCV data with automated access. |

**Note:** Delivery percentage (percentage of trades resulting in actual share delivery vs. intraday reversal) is an additional liquidity proxy NOT available via yfinance. This is documented as a data gap.

### 4.2 RBI / SEBI Open Data

| Field | Detail |
|---|---|
| **Purpose** | Macroeconomic context (repo rate, CPI, FII/DII flows) |
| **Availability** | Partial; some data available via public APIs |
| **Decision** | **EXCLUDED** from initial scope. Could be added as a future enhancement for macro-stress features. |

### 4.3 Stooq.com

| Field | Detail |
|---|---|
| **Purpose** | Alternative free data source for Indian equities |
| **Limitation** | Coverage of Indian stocks is limited; primarily useful for global indices |
| **Decision** | **EXCLUDED.** yfinance provides more comprehensive Indian equity coverage. |

### 4.4 Paid Data Sources (Not Used)

The following paid sources provide survivorship-bias-free, high-quality Indian equity data but are excluded due to cost constraints:

- **Refinitiv (LSEG) Eikon:** Comprehensive; expensive.
- **Bloomberg Terminal:** Industry standard; prohibitively expensive.
- **Quandl / Nasdaq Data Link:** Some Indian equity datasets; requires paid subscription for clean historical data.
- **True Beacon / Smallcase APIs:** Indian market specific; subscription required.
- **Zerodha Kite Connect:** Excellent Indian data; requires brokerage account and API key; includes intraday data.

---

## 5. Data Provenance and Reproducibility

| Concern | Approach |
|---|---|
| **Reproducibility** | All downloads tagged with date, yfinance version, and ticker list. Manifests stored in `data/manifests/`. |
| **Versioning** | Raw data stored in Parquet with filename encoding the download date. |
| **Data lineage** | Each processed file references the raw file it was derived from. |
| **No redistribution** | `.gitignore` excludes all files under `data/raw/`, `data/processed/`, `data/predictions/`. |
| **Attribution** | All notebooks and reports cite Yahoo Finance as data source and acknowledge proxy limitations. |

---

## 6. Summary: Data Source Decision Matrix

| Source | Used? | Primary Use | Key Risk |
|---|---|---|---|
| Yahoo Finance via yfinance | YES (PRIMARY) | OHLCV daily data for 300 stocks | API instability, rate limits |
| ^NSEI via yfinance | YES (MANDATORY) | Benchmark market index | Generally reliable |
| ^INDIAVIX via yfinance | YES (CONDITIONAL) | Supplementary market-fear / expected volatility | Historical coverage gaps to be verified in Phase 1 |
| NSE Indices website | YES (manual) | 300-stock universe constituent lists | Historical reconstitutions unavailable |
| Public Event Sources (ECI, RBI, PIB) | YES (manual) | Market-wide event calendar | Date precision / alignment; curated once |
| Individual stock news / transcripts | NO (EXCLUDED) | Out of scope per design | High noise, NLP complexity, rate limits |
| NSE Bhavcopies | NO | Excluded per constraints | Scraping required |
| RBI / SEBI live feeds | NO (future) | Macro features | Out of initial scope |
| Any paid source | NO | N/A | Cost constraints |

---

## 7. Independent Data Source Requirement

For academic projects, reviewers often expect multiple independent data sources. This project integrates:

1. **Yahoo Finance (`yfinance`):** Primary daily OHLCV execution series for 300 stocks, Nifty 50 (`^NSEI`), and candidate India VIX (`^INDIAVIX`).
2. **NSE Indices Limited:** Universe constituent definitions for Nifty 100, Nifty Midcap 150, and Nifty Smallcap 250 (independent exchange-operator source).
3. **Curated Public Market Events Calendar:** Authoritative public dates for major macro disruptions, national elections (ECI), regulatory exchange halts (NSE/SEBI circulars), and geopolitical shocks.

**Assessment:** The project integrates exchange-defined constituent lists, multi-asset market data (equities, index benchmark, implied volatility proxy), and a curated market event calendar. This satisfies and exceeds the independent multi-source standard.

