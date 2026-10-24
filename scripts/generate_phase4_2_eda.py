"""Generates basic EDA figures and statistical summaries for Phase 4.2 Quality Report."""

import json
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

FIGURES_DIR = Path("reports/figures")
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

INTERIM_PATH = Path("data/interim/stocks/ohlcv_clean.parquet")
print(f"Loading interim data from {INTERIM_PATH}...")
df = pd.read_parquet(INTERIM_PATH)

print(f"Dataset shape: {df.shape}")

# 1. Summary Statistics for Returns
valid_returns = df["daily_return"].dropna()
ret_stats = {
    "count": int(valid_returns.count()),
    "mean": float(valid_returns.mean()),
    "std": float(valid_returns.std()),
    "skewness": float(valid_returns.skew()),
    "kurtosis": float(valid_returns.kurtosis()),
    "min": float(valid_returns.min()),
    "p001": float(valid_returns.quantile(0.001)),
    "p01": float(valid_returns.quantile(0.01)),
    "p05": float(valid_returns.quantile(0.05)),
    "p25": float(valid_returns.quantile(0.25)),
    "p50_median": float(valid_returns.quantile(0.50)),
    "p75": float(valid_returns.quantile(0.75)),
    "p95": float(valid_returns.quantile(0.95)),
    "p99": float(valid_returns.quantile(0.99)),
    "p999": float(valid_returns.quantile(0.999)),
    "max": float(valid_returns.max()),
}

# 2. Summary Statistics for Volume
vol_series = df["volume"]
vol_stats = {
    "count": int(vol_series.count()),
    "mean": float(vol_series.mean()),
    "std": float(vol_series.std()),
    "median": float(vol_series.median()),
    "min": int(vol_series.min()),
    "zero_volume_count": int((vol_series == 0).sum()),
    "p01": float(vol_series.quantile(0.01)),
    "p05": float(vol_series.quantile(0.05)),
    "p25": float(vol_series.quantile(0.25)),
    "p50": float(vol_series.quantile(0.50)),
    "p75": float(vol_series.quantile(0.75)),
    "p95": float(vol_series.quantile(0.95)),
    "p99": float(vol_series.quantile(0.99)),
    "max": int(vol_series.max()),
}

# 3. Quality Flags Distribution
flags_stats = {
    "is_zero_volume": int(df["is_zero_volume"].sum()),
    "is_zero_volume_nonzero_return": int(df["is_zero_volume_nonzero_return"].sum()),
    "is_stale_price": int(df["is_stale_price"].sum()),
    "is_extreme_move": int(df["is_extreme_move"].sum()),
    "is_corporate_action_gap": int(df["is_corporate_action_gap"].sum()),
    "is_market_shock": int(df["is_market_shock"].sum()),
    "is_short_history": int(df["is_short_history"].sum()),
    "is_warmup": int(df["is_warmup"].sum()),
    "is_valid_ohlcv": int(df["is_valid_ohlcv"].sum()),
    "is_benchmark_available": int(df["is_benchmark_available"].sum()),
    "missing_benchmark": int((~df["is_benchmark_available"]).sum()),
    "is_muhurat_session": int(df["is_muhurat_session"].sum()),
}

# 4. Stale price streaks breakdown
stale_df = df[df["stale_price_streak"] >= 3]
streak_lengths = stale_df["stale_price_streak"].value_counts().sort_index().to_dict()

# 5. Missing benchmark dates breakdown
missing_bm = df[~df["is_benchmark_available"]]
missing_by_date = missing_bm["date"].dt.strftime("%Y-%m-%d").value_counts().sort_index().to_dict()

# 6. Extreme Moves Details
extreme_df = df[df["is_extreme_move"]]
extreme_records = []
for _, r in extreme_df.iterrows():
    extreme_records.append({
        "ticker": r["ticker"],
        "date": str(r["date"].date()),
        "prev_close": float(r["prev_close"]),
        "close": float(r["close"]),
        "volume": int(r["volume"]),
        "daily_return_pct": float(r["daily_return"] * 100),
        "is_corporate_action_gap": bool(r["is_corporate_action_gap"]),
        "is_market_shock": bool(r["is_market_shock"]),
    })

eda_summary = {
    "total_rows": len(df),
    "total_tickers": int(df["ticker"].nunique()),
    "return_stats": ret_stats,
    "volume_stats": vol_stats,
    "flags_stats": flags_stats,
    "streak_lengths": {str(k): int(v) for k, v in streak_lengths.items()},
    "missing_benchmark_dates": {str(k): int(v) for k, v in missing_by_date.items()},
    "extreme_moves": extreme_records,
}

with open("reports/eda_summary_metrics.json", "w", encoding="utf-8") as f:
    json.dump(eda_summary, f, indent=2)

print("Saved reports/eda_summary_metrics.json")

# ----------------- PLOTTING -----------------
sns.set_theme(style="whitegrid")
plt.rcParams.update({"font.sans-serif": "Arial", "font.family": "sans-serif"})

# Figure 1: Return Distribution & Extreme Move Tails
fig, ax = plt.subplots(figsize=(10, 6), dpi=300)
# Filter clipped range for visualization of density
clip_rets = np.clip(valid_returns * 100, -15, 15)
sns.histplot(clip_rets, bins=120, kde=True, color="#1f77b4", stat="density", ax=ax, alpha=0.6)
ax.axvline(0, color="black", linestyle="--", linewidth=1.0, alpha=0.7)
ax.axvline(ret_stats["p01"] * 100, color="crimson", linestyle=":", linewidth=1.5, label=f"1st %ile ({ret_stats['p01']*100:.2f}%)")
ax.axvline(ret_stats["p99"] * 100, color="forestgreen", linestyle=":", linewidth=1.5, label=f"99th %ile ({ret_stats['p99']*100:.2f}%)")
ax.set_title("Cross-Sectional Daily Return Distribution (300 Stocks, 2018–2026)\nCentered body [-15%, +15%] with Fat Tails", fontsize=13, fontweight="bold", pad=12)
ax.set_xlabel("Daily Return (%)", fontsize=11)
ax.set_ylabel("Empirical Density", fontsize=11)
ax.legend(loc="upper right", frameon=True)
plt.tight_layout()
fig1_path = FIGURES_DIR / "return_distribution_and_tails.png"
fig.savefig(fig1_path)
plt.close(fig)
print(f"Generated {fig1_path}")

# Figure 2: Daily Volume Distribution (Log Scale) & Zero-Volume
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5), dpi=300)
# Subplot 1: Log10(Volume) distribution for positive volume
pos_vol = vol_series[vol_series > 0]
log_vol = np.log10(pos_vol)
sns.histplot(log_vol, bins=80, color="#2ca02c", ax=ax1, kde=True)
ax1.set_title("Log10 Trading Volume Distribution (Positive Volume Days)", fontsize=11, fontweight="bold")
ax1.set_xlabel("Log10(Daily Volume in Shares)", fontsize=10)
ax1.set_ylabel("Frequency", fontsize=10)
ax1.axvline(np.log10(vol_stats["p50"]), color="darkblue", linestyle="--", label=f"Median: {int(vol_stats['p50']):,} shares")
ax1.legend(loc="upper left")

# Subplot 2: Zero Volume Count by Year
df["year"] = df["date"].dt.year
zv_by_year = df[df["is_zero_volume"]].groupby("year").size()
all_years = sorted(df["year"].unique())
zv_counts_all = [zv_by_year.get(y, 0) for y in all_years]
sns.barplot(x=all_years, y=zv_counts_all, color="#d62728", ax=ax2)
ax2.set_title("Zero-Volume Observations by Year (Total = 751)", fontsize=11, fontweight="bold")
ax2.set_xlabel("Year", fontsize=10)
ax2.set_ylabel("Zero-Volume Rows Count", fontsize=10)
for i, v in enumerate(zv_counts_all):
    if v > 0:
        ax2.text(i, v + 5, str(v), ha="center", fontsize=9, fontweight="bold")
plt.tight_layout()
fig2_path = FIGURES_DIR / "volume_distribution_log.png"
fig.savefig(fig2_path)
plt.close(fig)
print(f"Generated {fig2_path}")

# Figure 3: Stale Price Streak Length Distribution
fig, ax = plt.subplots(figsize=(9, 5), dpi=300)
keys = [int(k) for k in streak_lengths.keys()]
vals = [int(v) for v in streak_lengths.values()]
sns.barplot(x=keys, y=vals, color="#9467bd", ax=ax)
ax.set_title("Distribution of Stale Price Streak Observations (>=3 Consecutive Unchanged Closes)", fontsize=12, fontweight="bold", pad=12)
ax.set_xlabel("Consecutive Unchanged Close Streak Length", fontsize=11)
ax.set_ylabel("Number of Observations", fontsize=11)
for i, v in enumerate(vals):
    ax.text(i, v + 2, str(v), ha="center", fontsize=9, fontweight="bold")
plt.tight_layout()
fig3_path = FIGURES_DIR / "stale_price_streaks_distribution.png"
fig.savefig(fig3_path)
plt.close(fig)
print(f"Generated {fig3_path}")

# Figure 4: Stock History Coverage & Missing Benchmark Sessions
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5), dpi=300)
# Subplot 1: Distribution of Stock Row Counts
row_counts = df.groupby("ticker").size()
sns.histplot(row_counts, bins=40, color="#17becf", ax=ax1)
ax1.set_title("Stock Historical Observation Coverage (300 Stocks)", fontsize=11, fontweight="bold")
ax1.set_xlabel("Total Trading Days in History", fontsize=10)
ax1.set_ylabel("Number of Stocks", fontsize=10)
ax1.axvline(200, color="red", linestyle="--", label="Min Required History (200 days)")
ax1.legend(loc="upper left")

# Subplot 2: Missing Benchmark Rows by Date
dates_list = list(missing_by_date.keys())
counts_list = list(missing_by_date.values())
sns.barplot(x=dates_list, y=counts_list, color="#ff7f0e", ax=ax2)
ax2.set_title("Unmatched Equity Trading Sessions Absent in ^NSEI (Total = 1,219)", fontsize=11, fontweight="bold")
ax2.set_xlabel("Trading Date", fontsize=10)
ax2.set_ylabel("Stock Observations Missing Benchmark", fontsize=10)
ax2.tick_params(axis="x", rotation=25)
for i, v in enumerate(counts_list):
    ax2.text(i, v + 5, str(v), ha="center", fontsize=9, fontweight="bold")
plt.tight_layout()
fig4_path = FIGURES_DIR / "history_coverage_and_unmatched_benchmark.png"
fig.savefig(fig4_path)
plt.close(fig)
print(f"Generated {fig4_path}")

print("All EDA figures and metrics generated successfully!")
