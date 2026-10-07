"""_paper_mesh_rows extracted from the calibration experiment runner."""

from __future__ import annotations

from typing import Any
from typing import Dict
from typing import List

from ._paper_mesh_strategy_and_k import _paper_mesh_strategy_and_k


def _paper_mesh_rows(mesh_results: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for key in ("tunecheck", "global", "dfc"):
        res = mesh_results.get(key)
        if not isinstance(res, dict):
            continue
        effort = res.get("effort", {})
        strategy_label, k_value = _paper_mesh_strategy_and_k(key, res)
        row = {
            "Calibration strategy": strategy_label,
            "k": int(k_value),
            "Total probes": int(res.get("probe_count", effort.get("probe_count", 0))),
            "Effective probe rounds": int(
                res.get("probe_rounds_effective", effort.get("probe_rounds_effective", 0))
            ),
            "HW writes": int(res.get("hw_write_count", effort.get("hw_write_count", 0))),
            "Final MSE": float(res.get("mse_final", float("nan"))),
            "Time": float(res.get("walltime", res.get("walltime_s", float("nan")))),
            "method_key": key,
        }
        rows.append(row)
    return rows
