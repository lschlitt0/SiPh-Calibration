"""_extract_mesh_round_series extracted from the calibration experiment runner."""

from __future__ import annotations

from typing import Any
from typing import Dict
from typing import List
from typing import Optional


def _extract_mesh_round_series(res: Dict[str, Any], method: str) -> Optional[List[float]]:
    if not isinstance(res, dict):
        return None
    if method in ("dfc", "global"):
        series: List[float] = []
        initial = res.get("initial_mse", None)
        if initial is None:
            curve = res.get("mse_curve", [])
            if isinstance(curve, list) and curve:
                initial = curve[0]
        if initial is not None:
            try:
                series.append(float(initial))
            except Exception:
                pass
        rounds = res.get("mse_after_rounds", [])
        if isinstance(rounds, list):
            for val in rounds:
                try:
                    series.append(float(val))
                except Exception:
                    continue
        return series or None
    if method == "tunecheck":
        curve = res.get("mse_curve", [])
        if isinstance(curve, list) and curve:
            out: List[float] = []
            for val in curve:
                try:
                    out.append(float(val))
                except Exception:
                    continue
            return out or None
    return None
