# GitHub Repository Audit: Missing Parquet Data Files

**Project:** ML-Based Liquidity and Trading-Risk Intelligence for Indian Equities  
**Date of Audit:** October 25, 2026  
**Audit Type:** Strictly Read-Only Investigation  
**Working Directory:** `c:\Users\vighn\OneDrive\Desktop\Liquidity and Trading-Risk Intelligence for Indian Equities`  
**Current Branch:** `main` | **Head Commit:** `bdb3699` (`Initial commit`)  
**Configured Remote:** `origin` -> `https://github.com/vighnesh-6/Liquidity-and-Trading-Risk-Intelligence-for-Indian-Equities.git`  

---

## 1. Executive Summary & Verdict

### Verdict
The historical Parquet data files are missing from GitHub **not because of a network error, push rejection, file-size cutoff, or data corruption**, but because **the repository's `.gitignore` explicitly excludes all raw, interim, and processed data files by design**.

### Key Findings
1. **Data Is 100% Safe Locally:** All **300 stock raw Parquet files**, **3 market index raw Parquet files**, and the **interim clean dataset** (`ohlcv_clean.parquet`, 565,190 rows × 27 columns) are fully intact on the local filesystem. Zero bytes of data were lost or altered.
2. **Git Tracking Status:** The Parquet files have **never been staged, tracked, or committed** in Git history. Commit `bdb3699` (`Initial commit`) only committed directory placeholder files (`.gitkeep`), metadata manifests (`.json`), event tables (`.csv`), documentation, source code, and configuration files.
3. **Remote Synchronization:** The remote repository is completely up to date with the local `main` branch (`origin/main` == `HEAD` at `bdb3699`). GitHub displays exactly what was committed to Git.
4. **File Sizes Are Well Within GitHub Limits:** The largest data file in the project is `data/interim/stocks/ohlcv_clean.parquet` at **44.16 MB**, which is below GitHub's 50 MB warning threshold and well below GitHub's 100 MB hard rejection limit. All 300 raw stock files average ~72 KB (totaling ~20.75 MB).
5. **Git LFS Status:** Git LFS (v3.7.1) is installed on the host system, but is neither configured in `.gitattributes` nor used in the repository.

---

## 2. Local File Inventory & Verification Results

A read-only inspection of the local filesystem verified all historical and interim datasets:

| Target Directory / Asset | Expected | Found On Local Disk | Total Disk Size | Verification Details |
|---|---|---|---|---|
| `data/raw/stocks/` | 300 stock Parquet files | **300 `.parquet` files** + 1 `.gitkeep` | 21,759,900 bytes (~20.75 MB) | Exact match with universe (e.g., `RELIANCE.NS.parquet`, `HDFCBANK.NS.parquet`, `360ONE.NS.parquet`). |
| `data/raw/market/` | 3 market Parquet files | **3 `.parquet` files** + 1 `.gitkeep` | 215,368 bytes (~0.21 MB) | `^NSEI.parquet` (82.5 KB), `^NSEBANK.parquet` (79.5 KB), `^INDIAVIX.parquet` (53.3 KB). |
| `data/interim/stocks/ohlcv_clean.parquet` | Clean interim dataset (~565,190 rows, 27 cols) | **1 `.parquet` file** (Exists at `data/interim/stocks/ohlcv_clean.parquet`) | 46,302,787 bytes (~44.16 MB) | Verified via PyArrow metadata: **Rows: 565,190**, **Cols: 27**. Matches Phase 4.2 audit exactly. |
| `data/interim/market/` | Clean market benchmark Parquets | **3 `.parquet` files** + 1 `.gitkeep` | 296,896 bytes (~0.28 MB) | `nifty50_clean.parquet`, `banknifty_clean.parquet`, `india_vix_clean.parquet`. |
| `data/manifests/` | Collection audit manifest | **1 `.json` file** + 1 `.gitkeep` | 244,117 bytes (~0.23 MB) | `manifest_data_collection_20261024_150615.json` (tracked in Git). |
| `data/events/` | Market event calendar | **2 `.csv` files** + 1 `.gitkeep` | 45,575 bytes (~0.04 MB) | `market_events.csv`, `market_events_template.csv` (tracked in Git). |
| `data/processed/` | Processed modeling datasets | 1 `.gitkeep` | 71 bytes | Directory ready for Phase 5. |
| `data/predictions/` | Model inference outputs | 1 `.gitkeep` | 73 bytes | Directory ready for Phase 6. |

*Note on Path Discrepancy:* In the project structure, the interim stock dataset was generated into `data/interim/stocks/ohlcv_clean.parquet` rather than the parent `data/interim/ohlcv_clean.parquet`. Both directory levels contain `.gitkeep` placeholders.

---

## 3. `.gitignore` Findings

Inspection of `.gitignore` revealed explicit ignore patterns designed to block binary market data from being committed.

### `.gitignore` Excerpt (Lines 58–79)
```gitignore
# Project Data Directories (DO NOT COMMIT RAW OR PROCESSED MARKET DATA)
data/raw/*
!data/raw/.gitkeep
!data/raw/stocks/
data/raw/stocks/*
!data/raw/stocks/.gitkeep
!data/raw/market/
data/raw/market/*
!data/raw/market/.gitkeep
data/interim/*
!data/interim/.gitkeep
!data/interim/stocks/
data/interim/stocks/*
!data/interim/stocks/.gitkeep
!data/interim/market/
data/interim/market/*
!data/interim/market/.gitkeep
data/processed/*
!data/processed/.gitkeep
data/predictions/*
!data/predictions/.gitkeep
```

### Empirical Validation (`git check-ignore -v`)
Testing representative files confirms the exact rules blocking tracking:

```powershell
> git check-ignore -v "data/raw/stocks/360ONE.NS.parquet"
.gitignore:62:data/raw/stocks/*    data/raw/stocks/360ONE.NS.parquet

> git check-ignore -v "data/raw/market/^NSEI.parquet"
.gitignore:65:data/raw/market/*    data/raw/market/^NSEI.parquet

> git check-ignore -v "data/interim/ohlcv_clean.parquet"
.gitignore:67:data/interim/*    data/interim/ohlcv_clean.parquet

> git check-ignore -v "data/interim/stocks/ohlcv_clean.parquet"
.gitignore:70:data/interim/stocks/*    data/interim/stocks/ohlcv_clean.parquet

> git check-ignore -v "data/interim/market/nifty50_clean.parquet"
.gitignore:73:data/interim/market/*    data/interim/market/nifty50_clean.parquet
```

Because of these rules, running `git add .` skips all Parquet files silently.

---

## 4. Git Tracking & Commit History Status

### Tracked Files in `data/`
Running `git ls-files "data/**"` proves that **only `.gitkeep` files, CSV events, and JSON manifests are tracked**:
- `data/events/.gitkeep`
- `data/events/market_events.csv`
- `data/events/market_events_template.csv`
- `data/interim/.gitkeep`
- `data/interim/market/.gitkeep`
- `data/interim/stocks/.gitkeep`
- `data/manifests/.gitkeep`
- `data/manifests/manifest_data_collection_20261024_150615.json`
- `data/predictions/.gitkeep`
- `data/processed/.gitkeep`
- `data/raw/.gitkeep`
- `data/raw/market/.gitkeep`
- `data/raw/stocks/.gitkeep`

### Git Commit Log Inspection
Executing `git ls-files "data/raw/stocks/*.parquet"` and `git ls-files "data/interim/stocks/*.parquet"` produces zero results.

Checking the single commit in the repository:
```powershell
> git log -1 --oneline
bdb3699 Initial commit
```
Inspection of `git show --stat bdb3699` confirmed 130 files committed. The Parquet data files were never included in that commit.

---

## 5. Local vs. Remote Branch & Push Status

Inspection of the remote configuration and branch tracking:

```powershell
> git branch -vv
* main bdb3699 [origin/main] Initial commit

> git rev-parse origin/main
bdb3699acd03c3da9004fd9f682ec60dba659b31

> git rev-parse HEAD
bdb3699acd03c3da9004fd9f682ec60dba659b31
```

- **Branch:** `main`
- **Upstream:** `origin/main`
- **Sync Status:** 0 commits ahead, 0 commits behind. The local branch is identical to the remote branch.
- **Push Status:** Commit `bdb3699` was pushed to GitHub successfully. GitHub is displaying the true contents of commit `bdb3699`. Because `bdb3699` did not contain the Parquet files, GitHub does not show them.

*(Note on `git ls-remote`: Executing `git ls-remote` without interactive credentials returned `repository not found`, which is standard Git behavior for private GitHub repositories in non-interactive shells. The local remote-tracking reference `origin/main` confirms full synchronization at `bdb3699`.)*

---

## 6. GitHub File-Size Limitations & Git LFS Analysis

### File Size Verification
GitHub enforces the following limits:
- **Warning limit:** 50 MB per file.
- **Hard reject limit:** 100 MB per file.

Let us inspect the largest files in the project:
1. `data/interim/stocks/ohlcv_clean.parquet`: **44.16 MB** (46,302,787 bytes) — *Below 50 MB warning threshold, below 100 MB limit.*
2. `data/manifests/manifest_data_collection_20261024_150615.json`: **0.23 MB** (244,117 bytes).
3. `data/raw/stocks/*.parquet` (300 files): **~0.07–0.09 MB each** (21.75 MB total across all 300 files).
4. `data/raw/market/*.parquet` (3 files): **~0.05–0.08 MB each** (0.21 MB total).

Total storage for all 320 files in `data/` is **~65.67 MB**. No individual file exceeds GitHub's 100 MB limit, and none would have caused a push rejection.

### Git LFS Analysis
- Git LFS binary is available on the machine (`git-lfs/3.7.1`).
- `.gitattributes` currently contains only:
  ```gitattributes
  * text=auto
  ```
- Git LFS is **not active** in this repository.

---

## 7. Exact Root Cause

The root cause of missing historical data on GitHub is:

1. **Explicit Ignore Rules in `.gitignore`:** Lines 62, 65, 67, 70, 73, 75, and 77 explicitly ignore all `.parquet` files within `data/raw/`, `data/interim/`, `data/processed/`, and `data/predictions/`.
2. **Intentional Software Engineering Pattern:** As stated in the header of `.gitignore` line 58 (`# Project Data Directories (DO NOT COMMIT RAW OR PROCESSED MARKET DATA)`), this pattern is standard in production ML/data engineering repositories to prevent binary datasets from bloating the Git tree.
3. **Commit Scope:** When the `Initial commit` (`bdb3699`) was created, Git staged only the non-ignored files (`.gitkeep` markers, code, docs, manifests, and event CSVs). When pushed, GitHub mirrored that exact tree.

---

## 8. Safe, Minimal Remediation Plan (Awaiting Approval)

> **DO NOT EXECUTE ANY OF THESE STEPS YET.** Review the options below and choose the path that best fits your project goals.

### Option A: Follow Industry Best Practice (Recommended)
In institutional ML systems, large tabular datasets are typically stored in cloud object storage (S3, GCS, Azure Blob) or tracked via DVC (Data Version Control) rather than raw Git blobs. The repository already tracks:
- `data/manifests/manifest_data_collection_20261024_150615.json` (SHA-256 hashes and row counts)
- `audit/raw_data_sha256.json` (Per-file cryptographic verification)
- `scripts/backfill_history.py` (Deterministic reproducibility script)

If this is acceptable, **no changes are needed**. The data is safe on your machine and fully reproducible via the automated pipelines.

---

### Option B: Track Parquet Files via Git LFS (Recommended if GitHub must host data)
If your academic evaluators, peers, or teammates need the exact Parquet files directly from GitHub:
Git Large File Storage (LFS) keeps the Git commit history light by replacing binary files with lightweight text pointers in Git, while hosting the binary payload on GitHub LFS.

**Exact commands (Pending Approval):**
```powershell
# 1. Initialize Git LFS in the repository
git lfs install

# 2. Configure Git LFS to track parquet files
git lfs track "*.parquet"
git add .gitattributes

# 3. Update .gitignore to allow parquet tracking (or adjust rules)
# (Adjust .gitignore lines 58-79 to remove data/raw/stocks/*, data/interim/stocks/*, etc.)

# 4. Stage parquet files
git add data/raw/stocks/*.parquet
git add data/raw/market/*.parquet
git add data/interim/stocks/ohlcv_clean.parquet
git add data/interim/market/*.parquet

# 5. Commit and push
git commit -m "chore: track historical and interim parquet datasets via Git LFS"
git push origin main
```

---

### Option C: Direct Git Blob Tracking (Without LFS)
Because the interim file is 44.16 MB (< 100 MB limit) and raw stock files total 20.75 MB, standard Git can store them directly without LFS if you do not want to set up LFS quotas.

**Exact commands (Pending Approval):**
```powershell
# 1. Force-stage the parquet files bypassing .gitignore, OR modify .gitignore to whitelist them:
git add -f data/raw/stocks/*.parquet
git add -f data/raw/market/*.parquet
git add -f data/interim/stocks/ohlcv_clean.parquet
git add -f data/interim/market/*.parquet

# 2. Verify staging
git status --short

# 3. Commit and push
git commit -m "feat(data): commit raw and interim parquet datasets"
git push origin main
```
*Caution regarding Option C:* Committing 65 MB of binary data directly to Git history permanently increases `.git` clone size for all future clones.

---

## 9. Conclusion
- **Data safety:** 100% verified intact locally.
- **GitHub state:** Completely in sync with the commit history.
- **Action required:** Decide between Option A (leave data local/manifested), Option B (Git LFS), or Option C (force-commit to Git).
