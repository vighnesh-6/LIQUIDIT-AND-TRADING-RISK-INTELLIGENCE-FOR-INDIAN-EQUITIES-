"""Unit tests for supervised target construction module."""

import pytest
from src.labels.targets import construct_hre_target


def test_target_builder_callable():
    """Verifies that construct_hre_target is callable."""
    assert callable(construct_hre_target)
