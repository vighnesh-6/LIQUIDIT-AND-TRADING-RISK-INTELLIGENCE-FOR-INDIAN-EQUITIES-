"""Configuration loader utility.

Loads and validates YAML and JSON configurations.
"""

import json
from pathlib import Path
from typing import Any, Dict
import yaml


def load_yaml_config(path: Path | str) -> Dict[str, Any]:
    """Loads a YAML configuration file.

    Args:
        path: Path to YAML file.

    Returns:
        Dict[str, Any]: Parsed configuration dictionary.
    """
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {file_path}")
    with open(file_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_json_config(path: Path | str) -> Dict[str, Any]:
    """Loads a JSON configuration file.

    Args:
        path: Path to JSON file.

    Returns:
        Dict[str, Any]: Parsed configuration dictionary.
    """
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {file_path}")
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)
