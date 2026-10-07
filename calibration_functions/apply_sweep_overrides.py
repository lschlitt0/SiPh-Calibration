"""apply_sweep_overrides extracted from the calibration experiment runner."""

from __future__ import annotations

from dataclasses import field
from dataclasses import replace
from typing import Any
from typing import Dict

from .models import CalibrationConfig


def apply_sweep_overrides(cfg: CalibrationConfig, overrides: Dict[str, Any]) -> CalibrationConfig:
    """Return a replaced configuration, accepting aliases N, k, rings, and outer."""
    key_map = {
        "N": "mesh_size",
        "k": "partitions",
        "seed": "seed",
        "rings": "ring_count",
        "outer": "outer_rounds",
        "outer_rounds": "outer_rounds",
        "cross_talk": "ring_cross_talk",
    }
    mapped: Dict[str, Any] = {}
    for k, v in overrides.items():
        key_norm = str(k).strip()
        field = key_map.get(key_norm, key_map.get(key_norm.lower(), key_norm))
        mapped[field] = v
    return replace(cfg, **mapped)
