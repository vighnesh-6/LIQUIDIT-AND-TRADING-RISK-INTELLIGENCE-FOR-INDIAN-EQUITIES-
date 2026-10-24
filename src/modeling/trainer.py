"""Walk-forward model training orchestrator.

Responsible for:
- Implementing expanding-window walk-forward validation (10 chronological folds).
- Fitting feature scalers (StandardScaler) strictly within training folds.
- Training:
  1. Logistic Regression (baseline)
  2. Random Forest Classifier
  3. HistGradientBoosting Classifier
- Selecting best model by out-of-fold PR-AUC.
- Saving fitted model artifacts to `models/`.
"""

from pathlib import Path
from typing import Any, Dict, List, Tuple
import pandas as pd


class ModelTrainer:
    """Orchestrates expanding-window walk-forward training across candidate models."""

    def __init__(
        self,
        n_splits: int = 10,
        min_train_days: int = 490,
        test_window_days: int = 60,
        embargo_gap_days: int = 1,
        models_dir: Path | str = "models",
    ) -> None:
        self.n_splits = n_splits
        self.min_train_days = min_train_days
        self.test_window_days = test_window_days
        self.embargo_gap_days = embargo_gap_days
        self.models_dir = Path(models_dir)

    def generate_walk_forward_splits(
        self,
        df: pd.DataFrame,
    ) -> List[Tuple[pd.Index, pd.Index]]:
        """Generates chronological train/test index splits without future leakage.

        Args:
            df: Feature DataFrame indexed or containing 'date'.

        Returns:
            List[Tuple[pd.Index, pd.Index]]: List of (train_idx, test_idx).
        """
        raise NotImplementedError("Scaffold only — implementation pending Phase 8")

    def train_and_evaluate_models(
        self,
        df: pd.DataFrame,
        feature_cols: List[str],
        target_col: str = "hre_5d",
    ) -> Dict[str, Any]:
        """Runs walk-forward evaluation across LogisticRegression, RF, and HGBT.

        Args:
            df: Labeled feature matrix (excluding warm-up and holdout).
            feature_cols: List of 55 feature column names.
            target_col: Target column name ('hre_5d').

        Returns:
            Dict[str, Any]: Validation metrics and per-fold scores.
        """
        raise NotImplementedError("Scaffold only — implementation pending Phase 8")

    def fit_final_model(
        self,
        df: pd.DataFrame,
        feature_cols: List[str],
        best_model_name: str,
        target_col: str = "hre_5d",
    ) -> Path:
        """Fits best model on full training set and serializes artifact with metadata.

        Args:
            df: Labeled feature matrix.
            feature_cols: Feature column names.
            best_model_name: Selected model identifier.
            target_col: Target column name.

        Returns:
            Path: Path to saved .joblib model artifact.
        """
        raise NotImplementedError("Scaffold only — implementation pending Phase 8")
