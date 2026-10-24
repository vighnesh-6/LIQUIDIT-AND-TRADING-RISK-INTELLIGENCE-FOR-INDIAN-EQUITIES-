"""Unit tests for Composite Liquidity-Risk Score (LRS) module."""

import pytest
from src.labels.lrs import compute_lrs


def test_lrs_callable():
    """Verifies that compute_lrs is callable."""
    assert callable(compute_lrs)
