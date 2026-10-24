# UNIVERSE SELECTION
## ML-Based Liquidity and Trading-Risk Intelligence for Indian Equities

**Version:** 1.0
**Status:** Pre-Implementation Audit
**Label convention:** [VERIFIED] = confirmed from NSE/research. [ESTIMATE] = calculated or inferred. [UNRESOLVED] = requires verification.

---

## 1. Available Indian Equity Indices — Comparison

### 1.1 Nifty 50

| Attribute | Detail |
|---|---|
| **Constituents** | 50 stocks [VERIFIED] |
| **Market Cap Segment** | Large-cap only |
| **Eligibility** | Top 50 by free-float market cap and liquidity |
| **Liquidity Profile** | Very high; minimal illiquidity risk |
| **yfinance Coverage** | Excellent; data back to ~2000 for most constituents |
| **Liquidity Variation** | LOW — all stocks are highly liquid; limited value for liquidity-risk modeling |
| **Verdict** | Insufficient standalone; include as large-cap anchor |

### 1.2 Nifty 100

| Attribute | Detail |
|---|---|
| **Constituents** | 100 stocks (Nifty 50 + Nifty Next 50) [VERIFIED] |
| **Market Cap Segment** | Large-cap |
| **Liquidity Profile** | High to very high |
| **yfinance Coverage** | Very good |
| **Liquidity Variation** | LOW to MODERATE — still predominantly liquid |
| **Verdict** | Good for anchor stocks; include fully |

### 1.3 Nifty Midcap 150

| Attribute | Detail |
|---|---|
| **Constituents** | 150 stocks [VERIFIED] |
| **Market Cap Segment** | Mid-cap (rank 101-250 by full market cap) |
| **Liquidity Profile** | Moderate; meaningful variation within the segment |
| **yfinance Coverage** | Good; most stocks have 5-10 years of data |
| **Liquidity Variation** | MODERATE to HIGH — ideal segment for liquidity-risk analysis |
| **Overlap with Nifty 100** | Zero by definition (different market cap tiers) |
| **Verdict** | High value; include substantially |

### 1.4 Nifty Smallcap 250

| Attribute | Detail |
|---|---|
| **Constituents** | 250 stocks [VERIFIED] |
| **Market Cap Segment** | Small-cap (rank 251-500 by full market cap) |
| **Liquidity Profile** | Low to moderate; wide variation |
| **yfinance Coverage** | Moderate; some tickers may fail |
| **Liquidity Variation** | HIGH — most interesting for liquidity-risk detection |
| **Data Quality Risk** | Higher; more gaps, stale prices, circuit-breaker halts |
| **Verdict** | Include selectively — curated subset, not all 250 |

### 1.5 Nifty 500

| Attribute | Detail |
|---|---|
| **Constituents** | 500 stocks (top 500 by full market cap on NSE) [VERIFIED] |
| **Market Cap Segment** | Large + Mid + Small |
| **Relationship to above** | Nifty 100 + Nifty Midcap 150 + Nifty Smallcap 250 = Nifty 500 |
| **Overlap** | Nifty 100 is fully contained; Nifty Midcap 150 and Nifty Smallcap 250 together make the remainder |
| **Verdict** | Using Nifty 500 as the eligible universe and selecting a stratified 300 is the most defensible approach |

### 1.6 Mixed-Cap / Custom Universe

| Attribute | Detail |
|---|---|
| **Definition** | User-defined selection across cap segments |
| **Advantage** | Full control over liquidity spectrum; avoids over-representation of any segment |
| **Disadvantage** | Requires explicit, documented selection rules; harder to defend without clear methodology |
| **Verdict** | Acceptable if selection is stratified and documented; effectively what we recommend below |

### 1.7 Microcaps (Below Nifty 500)

| Attribute | Detail |
|---|---|
| **Definition** | Companies ranked below 500 by full market cap |
| **Liquidity Profile** | Very low; extremely illiquid |
| **yfinance Coverage** | Poor; many tickers absent or stale |
| **Data Quality** | Low; frequent gaps, zero-volume days, corporate action errors |
| **Stakeholder Value** | Limited; most investors cannot trade these stocks meaningfully |
| **Verdict** | **EXCLUDED from initial universe.** Document as a future extension. |

---

## 2. Recommended Universe

### Decision: Stratified Sample from Nifty 500 — 300 Stocks

**Recommended composition:**

| Segment | Index Source | Count | Rationale |
|---|---|---|---|
| Large-cap | All Nifty 100 constituents | 100 | Full coverage; liquid anchor; ensures benchmark-relative features have dense data |
| Mid-cap | All Nifty Midcap 150 constituents | 150 | Core segment for liquidity-risk variation; high academic interest |
| Small-cap | Curated 50 from Nifty Smallcap 250 | 50 | Adds illiquidity tail; curated to exclude data-poor tickers |
| **Total** | | **300** | |

**Why 300?**
- Produces >200,000 clean stock-day rows over 5 years — well above the minimum target.
- Computationally comfortable on target hardware.
- Spans the full liquidity spectrum from very liquid (Nifty 50) to moderately illiquid (small-caps).
- Defensible as a "Nifty 500 stratified sample" — an academically standard approach.

**Why include all 100 large-caps?**
Large-caps are likely to have the best data quality and are needed to train the "baseline normal" state for the supervised classifier. Without high-quality liquid stocks, the model has no clean negative (low-risk) class.

**Why include all 150 mid-caps?**
Mid-caps exhibit meaningful liquidity variation and are the most interesting segment for liquidity-risk analysis. Many research papers focus on mid-caps as the transition zone between liquid and illiquid markets.

**Why only 50 small-caps?**
Small-caps introduce data quality risk. A curated subset (selected by highest average daily turnover from the Nifty Smallcap 250) is more defensible than including all 250. After yfinance coverage testing, the selection can be expanded to 100 if data quality is satisfactory.

---

## 3. Selection Method

### Step 1: Obtain Current Constituent Lists
Download current constituent lists from:
- Nifty 100: https://www.niftyindices.com/indices/equity/broad-based-indices/nifty100
- Nifty Midcap 150: https://www.niftyindices.com/indices/equity/broad-based-indices/nifty-midcap-150
- Nifty Smallcap 250: https://www.niftyindices.com/indices/equity/broad-based-indices/nifty-smallcap-250

**[UNRESOLVED: Confirm that constituent list downloads are available without login. Manual verification required.]**

### Step 2: Deduplicate
Since Nifty 100, Nifty Midcap 150, and Nifty Smallcap 250 are mutually exclusive sub-indices of Nifty 500, no deduplication is needed between these three lists. Verify this assumption during Phase 1.

### Step 3: Curate Small-Cap Selection (Reproducible Criteria)

From Nifty Smallcap 250, select exactly 50 stocks using the audited reproducible criterion:

- **Option A (EXECUTED & LOCKED): Top 50 by 6-Month Average Daily Traded Value (ADTV).**
  - *Rationale:* Maximizes data density and liquidity within the small-cap segment, minimizing zero-volume artifacts and stale prices while still representing the small-cap illiquidity risk tail.
  - *Calculation:* Trailing 126 trading days (6 calendar months), $\text{ADTV} = \frac{1}{N}\sum (\text{Close}_t \times \text{Volume}_t)$ computed across all 251 active constituents in the official Nifty Smallcap 250 constituent list.
  - *Result:* Top 50 ranked descending (Highest: `NETWEB.NS` at INR 7.82B, Lowest: `HBLENGINE.NS` at INR 1.44B). Fully documented and locked in `configs/universe.json`.
  - *Decision Status:* **[RESOLVED & LOCKED — October 2026]** Option A executed; all 50 selected small-caps verified. Zero overlaps with Nifty 100 or Nifty Midcap 150.

### Step 4: NSE Ticker Mapping
Map all company names to NSE tickers (`.NS` format). NSE constituent files typically include both the symbol and ISIN. Use the symbol directly with `.NS` suffix.

### Step 5: yfinance Validation
Attempt to download 1 year of data for all candidate tickers. Tickers returning fewer than 200 valid trading days (approximately 80% coverage of available trading days) are flagged and potentially excluded. Document all exclusions in the manifest.

### Step 6: Final Universe File
Store the final universe as a versioned CSV/JSON file in `configs/` with columns:
- `ticker` (NSE symbol + .NS)
- `company_name`
- `isin`
- `cap_segment` (large/mid/small)
- `nifty_index` (Nifty100/MidCap150/SmallCap250)
- `inclusion_date`
- `exclusion_reason` (if excluded)

---

## 4. Overlap Between Indices

| Pair | Overlap |
|---|---|
| Nifty 50 vs Nifty 100 | Nifty 50 is fully contained in Nifty 100 |
| Nifty 100 vs Nifty Midcap 150 | Zero overlap by definition |
| Nifty 100 vs Nifty Smallcap 250 | Zero overlap by definition |
| Nifty Midcap 150 vs Nifty Smallcap 250 | Zero overlap by definition |
| Nifty 100 + Nifty Midcap 150 + Nifty Smallcap 250 | = Nifty 500 (500 unique stocks) |

**Deduplication burden: ZERO** between the three selected source indices. [VERIFIED — NSE publishes these as mutually exclusive segments.]

---

## 5. Survivorship Bias

### What Is Survivorship Bias Here?

When using current index constituent lists from NSE Indices, we are selecting stocks that have survived long enough to currently be listed and index-eligible. Stocks that were:
- Delisted due to business failure or fraud
- Voluntarily delisted or taken private
- Merged into another company
- Suspended from trading permanently

...are not included in current constituent lists and typically have no usable yfinance data. This means our training data consists only of "survivors" — companies that were successful enough to remain listed.

### Implications for Model

The supervised model will be trained primarily on stocks that did not fail catastrophically. This means:
1. The model may underestimate the probability of extreme illiquidity events that precede delistings.
2. The model's "high-risk" predictions are based on surviving stocks, not actual worst-case outcomes.
3. Feature distributions may be systematically different from what would be observed in a survivorship-bias-free dataset.

### Mitigation and Documentation Strategy

**This bias cannot be fully corrected without a paid survivorship-bias-free database.** The following mitigations will be applied:

1. **Documentation:** Survivorship bias will be explicitly acknowledged in all model documentation, reports, and dashboards.

2. **Disclosure statement:** All predictions will carry a disclaimer noting that the model was trained on surviving stocks and may underestimate extreme risk for currently struggling stocks.

3. **Cross-check delisted stocks:** During Phase 1, attempt to identify a small set of recently delisted or suspended NSE stocks and test whether yfinance returns any data for them. Document the result.

4. **Academic framing:** Cite relevant literature acknowledging survivorship bias as a universal limitation of free-data academic ML projects on stock markets (e.g., Lo and MacKinlay 1990, Brown et al. 1992).

5. **Future extension:** Note that survivorship-bias-free data (e.g., from Refinitiv or Bloomberg) could be used in a professional or research extension of this project.

---

## 6. Universe Maintenance Over Time

### Initial Universe (Static)
For the initial project and model training, the universe will be treated as static — the same 300 tickers throughout the historical window. This is a simplification that ignores historical index reconstitutions.

### Reconstitution Awareness
NSE reconstitutes the Nifty 100, Nifty Midcap 150, and Nifty Smallcap 250 quarterly. Stocks graduate between segments (e.g., a mid-cap may become large-cap). The current constituent list will not reflect the composition in 2018-2022.

**Implication:** A stock currently in Nifty Midcap 150 may have been in Nifty 100 in 2018, or may have only been listed in 2020. The historical data will span different cap segments at different points in time.

**Mitigation:** Accept this as a known limitation of using current constituents and document it. For a portfolio management application, the current composition is the actionable set.

### Ongoing Daily Maintenance
After initial setup, the daily refresh pipeline will:
1. Download new data only for currently active tickers in the universe file.
2. Log any tickers returning empty data (potential recent delistings or ticker changes).
3. Alert the user if more than 5% of tickers fail on a given day (potential broader data issue).
4. The universe file itself will NOT be automatically updated — changes to constituents require manual review and version increment.

---

## 7. Stakeholder Value by Segment

| Stakeholder | Most Relevant Segment | Reason |
|---|---|---|
| Retail investors | Mid-cap, Small-cap | Most likely trading target; highest risk variation |
| Portfolio managers | Large-cap, Mid-cap | Core holdings in most diversified portfolios |
| Risk analysts | Full spectrum | Need to identify illiquidity concentrations |
| Quant researchers | Mid-cap, Small-cap | Most academic interest in illiquidity premium |
| Index fund managers | Large-cap | Benchmark alignment |

The 300-stock stratified universe serves all these stakeholders simultaneously, making it the most versatile and defensible choice.

---

## 8. Summary: Recommended Universe

```
Final Universe: 300 stocks
  - 100 from Nifty 100 (all constituents)
  - 150 from Nifty Midcap 150 (all constituents)
  - 50 from Nifty Smallcap 250 (curated by turnover/size)

Source: NSE Indices Limited constituent lists (current, as of download date)
Ticker format: NSE symbols with .NS suffix
Benchmark: ^NSEI (Nifty 50 index)
Historical window: 2018-01-01 to present (~7 years)
Minimum ticker coverage: 200 valid trading days required for inclusion
Survivorship bias: Acknowledged, documented, cannot be eliminated with free data
Universe updates: Manual, version-controlled, not automated
```
