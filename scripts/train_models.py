"""Offline model training script (Phase 8).

Responsible for:
- Loading labeled feature matrix from `data/processed/`.
- Executing expanding-window walk-forward validation across candidate models.
- Evaluating out-of-fold PR-AUC and ROC-AUC.
- Serializing winning model and scaler artifacts into `models/`.
- Updating `models/model_registry.json`.
"""

import sys
from pathlib import Path


def main() -> None:
    print("[SCAFFOLD] scripts/train_models.py initialized.")
    print("Execution deferred to Phase 8: Baselines & ML Modeling.")


if __name__ == "__main__":
    main()
