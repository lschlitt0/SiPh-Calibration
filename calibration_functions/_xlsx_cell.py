"""_xlsx_cell extracted from the calibration experiment runner."""

from __future__ import annotations

from pathlib import Path
from typing import Any
import numpy as np


def _xlsx_cell(value: Any) -> Any:
    if value is None:
        return ""
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, (list, tuple, dict)):
        return str(value)
    return value
