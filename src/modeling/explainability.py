"""Model explainability and feature importance module.

Responsible for:
- Computing Gini importance and Permutation importance.
- Tracking feature importance stability across walk-forward folds.
- Flagging features with anomalous or unstable rankings.
"""

from typing import List, Optional
import pandas as pd


class ModelExplainer:
    """Computes interpretability and importance metrics for trained models."""

    @staticmethod
    def get_feature_importances(
        model: Any,
        feature_names: List[str],
    ) -> pd.DataFrame:
        """Extracts native feature importance from tree-based estimators.

        Args:
            model: Trained estimator.
            feature_names: List of feature names.

        Returns:
            pd.DataFrame: Sorted DataFrame of feature importances.
        """
        raise NotImplementedError("Scaffold only — implementation pending Phase 8")

    @staticmethod
    def compute_permutation_importance(
        model: Any,
        X_val: pd.DataFrame,
        y_val: pd.Series,
        n_repeats: int = 5,
        random_state: int = 42,
    ) -> pd.DataFrame:
        """Computes permutation importance on out-of-fold validation data.

        Args:
            model: Trained estimator.
            X_val: Validation feature matrix.
            y_val: Validation targets.
            n_repeats: Number of shuffle repeats.
            random_state: Seed.

        Returns:
            pd.DataFrame: Feature permutation importance summary.
        """
        raise NotImplementedError("Scaffold only — implementation pending Phase 8")
