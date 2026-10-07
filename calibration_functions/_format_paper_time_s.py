"""_format_paper_time_s extracted from the calibration experiment runner."""

from __future__ import annotations

from typing import Any


def _format_paper_time_s(value: Any) -> str:
    return f"{float(value):.2f}\\,s"
