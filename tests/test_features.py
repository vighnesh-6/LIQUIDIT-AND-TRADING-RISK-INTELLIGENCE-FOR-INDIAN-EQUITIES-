"""Unit tests for feature engineering modules."""

import pytest
from src.features.engineer import FeatureEngineer


def test_feature_engineer_initialization():
    """Verifies default warm-up window and numeric dtype settings."""
    engineer = FeatureEngineer(warmup_rows=80, output_dtype="float32")
    assert engineer.warmup_rows == 80
    assert engineer.output_dtype == "float32"


def test_feature_engineer_method_signatures():
    """Verifies that FeatureEngineer exposes required orchestration methods."""
    engineer = FeatureEngineer()
    assert hasattr(engineer, "compute_stock_features")
    assert hasattr(engineer, "process_universe")
