"""Unit tests for UniverseManager module (offline, no network required)."""

import pytest
from pathlib import Path
from src.data.universe import UniverseManager


@pytest.fixture
def universe_mgr():
    config_path = Path("configs/universe.json")
    if not config_path.exists():
        pytest.skip("configs/universe.json does not exist")
    return UniverseManager(config_path=config_path)


def test_universe_loading(universe_mgr):
    """Verifies that configs/universe.json can be loaded cleanly."""
    data = universe_mgr.universe_data
    assert "tickers" in data
    assert "metadata" in data
    assert "small_cap_selection_criterion" in data["metadata"]


def test_universe_validation_report(universe_mgr):
    """Verifies that the canonical universe passes all structural integrity checks."""
    report = universe_mgr.validate_universe()
    assert report["is_valid"] is True
    assert report["large_count"] == 100
    assert report["mid_count"] == 150
    assert report["small_count"] == 50
    assert report["total_count"] == 300
    assert report["unique_count"] == 300
    assert len(report["overlaps"]["large_mid"]) == 0
    assert len(report["overlaps"]["large_small"]) == 0
    assert len(report["overlaps"]["mid_small"]) == 0


def test_all_tickers_format(universe_mgr):
    """Verifies that all 300 tickers follow the standard NSE symbol convention."""
    tickers = universe_mgr.get_all_tickers()
    assert len(tickers) == 300
    for t in tickers:
        assert isinstance(t, str)
        assert t.endswith(".NS"), f"Ticker {t} does not end with .NS"
        assert len(t) > 3


def test_segment_mapping_completeness(universe_mgr):
    """Verifies that segment mapping covers all 300 tickers with valid segment labels."""
    mapping = universe_mgr.get_segment_mapping()
    assert len(mapping) == 300
    counts = {"large": 0, "mid": 0, "small": 0}
    for t, seg in mapping.items():
        assert seg in counts
        counts[seg] += 1
    assert counts["large"] == 100
    assert counts["mid"] == 150
    assert counts["small"] == 50


def test_market_index_getters(universe_mgr):
    """Verifies getters for benchmark (^NSEI), Bank Nifty (^NSEBANK), and India VIX (^INDIAVIX)."""
    assert universe_mgr.get_benchmark_ticker() == "^NSEI"
    assert universe_mgr.get_bank_nifty_ticker() == "^NSEBANK"
    assert universe_mgr.get_vix_candidate_ticker() == "^INDIAVIX"
