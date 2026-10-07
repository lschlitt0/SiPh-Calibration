"""_format_paper_settle_ms extracted from the calibration experiment runner."""

from __future__ import annotations

from typing import Any
from typing import Dict


def _format_paper_settle_ms(row: Dict[str, Any]) -> str:
    if not bool(row.get("settled_all", False)):
        horizon_ms = int(round(1000.0 * float(row.get("control_horizon_s", 0.0))))
        return f"$>{horizon_ms}$"
    return f"{int(round(float(row['Settle time (ms)'])))}"
