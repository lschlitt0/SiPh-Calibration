"""_mtkahypar_preset extracted from the calibration experiment runner."""

from __future__ import annotations

from typing import Any
import os


def _mtkahypar_preset() -> Any:
    """Select KAHYPAR_PRESET; the default preset does not promise deterministic runs."""
    import mtkahypar

    preset_map = {
        "default": mtkahypar.PresetType.DEFAULT,
        "quality": mtkahypar.PresetType.QUALITY,
        "highest_quality": mtkahypar.PresetType.HIGHEST_QUALITY,
        "deterministic": mtkahypar.PresetType.DETERMINISTIC,
        "deterministic_quality": mtkahypar.PresetType.DETERMINISTIC_QUALITY,
        "large_k": mtkahypar.PresetType.LARGE_K,
    }
    preset_raw = os.getenv("KAHYPAR_PRESET", "").strip().lower()
    return preset_map.get(preset_raw, mtkahypar.PresetType.DEFAULT)
