"""Universe management module.

Responsible for:
- Loading and validating `configs/universe.json`.
- Managing the 300-stock universe (100 Large-Cap, 150 Mid-Cap, 50 Small-Cap).
- Formatting tickers to standard NSE format (`<SYMBOL>.NS`).
- Tracking exclusions and logging survivorship bias metadata.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


class UniverseManager:
    """Manages the 300-stock universe for Indian equities."""

    def __init__(self, config_path: Path | str = "configs/universe.json") -> None:
        self.config_path = Path(config_path)
        self.universe_data: Dict[str, Any] = {}
        if self.config_path.exists():
            self.load_universe()

    def load_universe(self) -> Dict[str, Any]:
        """Loads and parses the universe JSON configuration.

        Returns:
            Dict[str, Any]: Universe metadata and ticker groupings.
        """
        if not self.config_path.exists():
            raise FileNotFoundError(f"Universe configuration not found: {self.config_path}")

        with open(self.config_path, "r", encoding="utf-8") as f:
            self.universe_data = json.load(f)

        return self.universe_data

    def validate_universe(self) -> Dict[str, Any]:
        """Validates consistency and integrity of loaded universe.

        Checks:
        - 100 Large-caps
        - 150 Mid-caps
        - 50 Small-caps
        - Exactly 300 unique tickers
        - No segment overlaps

        Returns:
            Dict[str, Any]: Summary validation report.
        """
        if not self.universe_data:
            self.load_universe()

        tickers_section = self.universe_data.get("tickers", {})
        large = tickers_section.get("large_cap_nifty_100", [])
        mid = tickers_section.get("mid_cap_nifty_midcap_150", [])
        small = tickers_section.get("small_cap_nifty_smallcap_250_selected", [])

        large_tickers = [s["ticker"] if isinstance(s, dict) else s for s in large]
        mid_tickers = [s["ticker"] if isinstance(s, dict) else s for s in mid]
        small_tickers = [s["ticker"] if isinstance(s, dict) else s for s in small]

        total_tickers = large_tickers + mid_tickers + small_tickers
        unique_tickers = set(total_tickers)

        overlap_large_mid = set(large_tickers).intersection(set(mid_tickers))
        overlap_large_small = set(large_tickers).intersection(set(small_tickers))
        overlap_mid_small = set(mid_tickers).intersection(set(small_tickers))

        is_valid = (
            len(large_tickers) == 100
            and len(mid_tickers) == 150
            and len(small_tickers) == 50
            and len(total_tickers) == 300
            and len(unique_tickers) == 300
            and len(overlap_large_mid) == 0
            and len(overlap_large_small) == 0
            and len(overlap_mid_small) == 0
        )

        return {
            "is_valid": is_valid,
            "large_count": len(large_tickers),
            "mid_count": len(mid_tickers),
            "small_count": len(small_tickers),
            "total_count": len(total_tickers),
            "unique_count": len(unique_tickers),
            "overlaps": {
                "large_mid": list(overlap_large_mid),
                "large_small": list(overlap_large_small),
                "mid_small": list(overlap_mid_small),
            },
        }

    def get_all_tickers(self) -> List[str]:
        """Returns flat list of all active 300 .NS tickers across segments.

        Returns:
            List[str]: List of standardized NSE tickers.
        """
        if not self.universe_data:
            self.load_universe()

        flat_list = self.universe_data.get("flat_ticker_list", [])
        if flat_list:
            return flat_list

        tickers_section = self.universe_data.get("tickers", {})
        all_t = []
        for group in ["large_cap_nifty_100", "mid_cap_nifty_midcap_150", "small_cap_nifty_smallcap_250_selected"]:
            for item in tickers_section.get(group, []):
                ticker = item["ticker"] if isinstance(item, dict) else item
                all_t.append(ticker)
        return all_t

    def get_segment_mapping(self) -> Dict[str, str]:
        """Returns mapping of ticker to market-cap segment (large, mid, small).

        Returns:
            Dict[str, str]: Map of ticker -> cap_segment.
        """
        if not self.universe_data:
            self.load_universe()

        tickers_section = self.universe_data.get("tickers", {})
        mapping = {}
        for item in tickers_section.get("large_cap_nifty_100", []):
            t = item["ticker"] if isinstance(item, dict) else item
            mapping[t] = "large"
        for item in tickers_section.get("mid_cap_nifty_midcap_150", []):
            t = item["ticker"] if isinstance(item, dict) else item
            mapping[t] = "mid"
        for item in tickers_section.get("small_cap_nifty_smallcap_250_selected", []):
            t = item["ticker"] if isinstance(item, dict) else item
            mapping[t] = "small"
        return mapping

    def get_benchmark_ticker(self) -> str:
        """Returns the market benchmark index ticker (^NSEI).

        Returns:
            str: Benchmark ticker string.
        """
        if not self.universe_data:
            self.load_universe()
        bm = self.universe_data.get("metadata", {}).get("benchmark", {})
        return bm.get("ticker", "^NSEI")

    def get_bank_nifty_ticker(self) -> str:
        """Returns candidate ticker for Bank Nifty (^NSEBANK).

        Returns:
            str: Bank Nifty ticker.
        """
        if not self.universe_data:
            self.load_universe()
        supp = self.universe_data.get("metadata", {}).get("supplementary_market_indices", {})
        bn = supp.get("bank_nifty", {})
        return bn.get("ticker", "^NSEBANK")

    def get_vix_candidate_ticker(self) -> Optional[str]:
        """Returns candidate ticker for India VIX (^INDIAVIX).

        Returns:
            Optional[str]: India VIX ticker or None.
        """
        if not self.universe_data:
            self.load_universe()
        supp = self.universe_data.get("metadata", {}).get("supplementary_market_indices", {})
        vix = supp.get("india_vix", {})
        return vix.get("ticker", "^INDIAVIX")
