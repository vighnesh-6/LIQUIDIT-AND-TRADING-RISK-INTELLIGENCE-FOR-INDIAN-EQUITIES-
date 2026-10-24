# Notebook Sequence & Architecture Guide
## ML-Based Liquidity and Trading-Risk Intelligence for Indian Equities

This directory contains the sequential research and experimental notebooks for the project.

### Chronological Execution Order

| # | Notebook | Phase | Focus / Deliverable | Inputs | Primary Outputs |
|---|---|---|---|---|---|
| 01 | `01_data_collection.ipynb` | Phase 1 & 3 | Pilot check, yfinance `.NS` audit, Nifty 50, India VIX availability | `configs/universe.json`, `configs/pipeline_config.yaml` | Validation logs, verified ticker lists |
| 02 | `02_eda.ipynb` | Phase 6 | Raw OHLCV quality checks, volume distributions, circuit halts | `data/raw/*.parquet`, `data/interim/*/*.parquet` | Data distribution profiles, initial hypotheses |
| 03 | `03_feature_exploration.ipynb` | Phase 6 | 55 features distribution, correlation matrix, Amihud/CS scaling | `data/processed/features_*.parquet` | Feature distribution stats, correlation heatmaps |
| 04 | `04_label_analysis.ipynb` | Phase 7 | Composite LRS calibration, `HRE_5d` class balance | `data/processed/features_*.parquet` | Labeled dataset, class ratio tables |
| 05 | `05_model_baseline.ipynb` | Phase 8 | Logistic Regression baseline, walk-forward splits (10 folds) | `data/processed/features_labeled.parquet` | Baseline ROC-AUC, PR-AUC, fold scores |
| 06 | `06_model_rf.ipynb` | Phase 8 | Random Forest classifier, Gini & permutation importance | `data/processed/features_labeled.parquet` | RF metrics, feature importance rankings |
| 07 | `07_model_hgbt.ipynb` | Phase 8 | HistGradientBoosting classifier, low-RAM evaluation | `data/processed/features_labeled.parquet` | HGBT metrics, model comparison tables |
| 08 | `08_anomaly_detection.ipynb` | Phase 8 | Isolation Forest unsupervised historical unusualness | `data/processed/features_labeled.parquet` | Anomaly score distributions, overlap tables |
| 09 | `09_event_analysis.ipynb` | Phase 9 | Event study on market shocks, elections, VIX interaction | `data/events/*.csv`, `data/processed/*.parquet` | Event window liquidity impact charts |
| 10 | `10_dashboard_prototype.ipynb` | Phase 11 | Component prototyping, Plotly charts, UI mockups | `data/predictions/*.parquet` | Chart functions for Streamlit integration |

### Golden Rules for Notebooks
1. **Unexecuted by default:** Notebooks are committed with outputs cleared unless specifically reviewing an experiment artifact.
2. **No Data Leakage:** Never use global scalers or shuffle time series. All validation must follow chronological splits.
3. **Hardware Mindful:** Avoid creating in-memory duplicate DataFrames; downcast float columns to `float32`.
4. **Production Code Separation:** Production logic belongs in `src/`. Notebooks import from `src/` rather than defining standalone business logic.
