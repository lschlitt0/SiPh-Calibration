"""_format_paper_peak_pm extracted from the calibration experiment runner."""

from __future__ import annotations

from typing import Any


def _format_paper_peak_pm(value: Any) -> str:
    val = float(value)
    if abs(val - round(val)) < 1e-9:
        return f"{val:.1f}"
    return f"{val:.2f}"
