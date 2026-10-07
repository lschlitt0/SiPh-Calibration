"""_mesh_trace_rows_for_xlsx extracted from the calibration experiment runner."""

from __future__ import annotations

from typing import Any
from typing import Dict
from typing import List

from .constants import MESH_TRACE_FIELDS
from .models import CalibrationConfig


def _mesh_trace_rows_for_xlsx(
    mesh_results: Dict[str, Any], cfg: CalibrationConfig, meta: Dict[str, Any]
) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for method, res in mesh_results.items():
        if not isinstance(res, dict):
            continue
        trace_rows = res.get("mesh_trace_rows", [])
        if not trace_rows:
            continue
        for tr in trace_rows:
            row = {
                "timestamp": meta["timestamp"],
                "seed": int(cfg.seed),
                "method": method,
                "N": int(res.get("N", cfg.mesh_size)),
                "k": int(res.get("k", cfg.partitions)),
            }
            for key in MESH_TRACE_FIELDS:
                row[key] = tr.get(key, "")
            rows.append(row)
    return rows
