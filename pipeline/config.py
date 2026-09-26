"""Project paths and configuration loading.

Every path in the pipeline derives from ROOT, so nothing is hard-coded and the
repo works on macOS and Windows alike (PROMPT.md section 2.9).
"""

from __future__ import annotations

from functools import cache
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = ROOT / "config"
RAW = ROOT / "data" / "raw"
MANUAL = ROOT / "data" / "manual"
PROCESSED = ROOT / "data" / "processed"
ARTIFACTS = ROOT / "artifacts"
DOCS = ROOT / "docs"

STORAGE_CRS = "EPSG:4326"      # everything stored and exported
MEASUREMENT_CRS = "EPSG:32642"  # UTM 42N, for every distance and area


@cache
def load(name: str) -> dict[str, Any]:
    """Load config/<name>.yaml."""
    path = CONFIG_DIR / f"{name}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"missing config file: {path}")
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)
