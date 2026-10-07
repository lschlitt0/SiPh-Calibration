"""Shared module loading and paths for the extracted unittest functions."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
FUNCTION_DIRECTORY = REPOSITORY_ROOT / "calibration_functions"
SUPPORT_MODULES = {"__init__", "models", "settings", "constants"}
MODULE_PATH = REPOSITORY_ROOT / "Calibration.py"
SPEC = importlib.util.spec_from_file_location("paper_calibration", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Unable to load module from {MODULE_PATH}")
CAL = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = CAL
SPEC.loader.exec_module(CAL)
