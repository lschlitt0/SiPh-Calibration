"""_format_paper_rms_pm extracted from the calibration experiment runner."""

from __future__ import annotations

from typing import Any


def _format_paper_rms_pm(value: Any) -> str:
    val = float(value)
    if abs(val) < 0.1:
        return f"{val:.4f}"
    return f"{val:.2f}"
