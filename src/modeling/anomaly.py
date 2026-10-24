"""Unsupervised anomaly detection module.

Responsible for:
- Fitting `IsolationForest` on historical feature subspace (12 features).
- Generating `isolation_score` and `isolation_flag`.
- Rescaling anomaly scores to 0–100 range for dashboard presentation.
- STRICT ARCHITECTURAL PRINCIPLE: Isolation Forest detects historical unusualness,
  NOT forward risk.
"""

from pathlib import Path
from typing import List, Optional
import pandas as pd


class AnomalyDetector:
    """Unsupervised anomaly detection using Isolation Forest."""

    def __init__(
        self,
        n_estimators: int = 100,
        contamination: float = 0.05,
        random_state: int = 42,
        feature_subset: Optional[List[str]] = None,
    ) -> None:
        self.n_estimators = n_estimators
        self.contamination = contamination
        self.random_state = random_state
        self.feature_subset = feature_subset or [
            "amihud_ratio",
            "amihud_z20",
            "volume_ratio",
            "volume_z20",
            "vol_20d",
            "vol_ratio_5_20",
            "daily_range",
            "range_z20",
            "overnight_gap_abs",
            "cs_spread_est",
            "nifty_vol_20d",
            "return_z20",
        ]
        self.model: Optional[Any] = None

    def fit(self, df: pd.DataFrame) -> "AnomalyDetector":
        """Fits Isolation Forest on historical feature observations.

        Args:
            df: Historical training feature matrix.

        Returns:
            AnomalyDetector: Fitted instance.
        """
        raise NotImplementedError("Scaffold only — implementation pending Phase 8")

    def score(self, df: pd.DataFrame) -> pd.DataFrame:
        """Scores observations and returns rescaled 0-100 anomaly scores.

        Args:
            df: Feature DataFrame to score.

        Returns:
            pd.DataFrame: Contains `isolation_score`, `isolation_flag`, and `anomaly_score_scaled`.
        """
        raise NotImplementedError("Scaffold only — implementation pending Phase 8")

    def save_artifact(self, dest_path: Path | str) -> Path:
        """Saves fitted Isolation Forest model artifact.

        Args:
            dest_path: Destination file path.

        Returns:
            Path: Written artifact path.
        """
        raise NotImplementedError("Scaffold only — implementation pending Phase 8")
