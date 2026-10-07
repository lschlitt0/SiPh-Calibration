"""_paper_mesh_strategy_and_k extracted from the calibration experiment runner."""

from __future__ import annotations

from typing import Any
from typing import Dict
from typing import Tuple


def _paper_mesh_strategy_and_k(method_key: str, res: Dict[str, Any]) -> Tuple[str, int]:
    key = str(method_key).strip().lower()
    if key == "tunecheck":
        return "Tune-and-check (coordinate descent)", 1
    if key == "global":
        return "Global surrogate (no partition)", 1
    if key == "dfc":
        return "DfC: partition + surrogates + polish", int(res.get("k", 4))
    return str(res.get("method", method_key)), int(res.get("k", 1))
