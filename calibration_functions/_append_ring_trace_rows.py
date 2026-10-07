"""_append_ring_trace_rows extracted from the calibration experiment runner."""

from __future__ import annotations

from typing import Any
from typing import Dict
from typing import List
import numpy as np

from .constants import RING_TRACE_SHEETS


def _append_ring_trace_rows(
    rows_by_sheet: Dict[str, List[Dict[str, Any]]],
    res: Dict[str, Any],
    meta: Dict[str, Any],
    trace: Dict[str, np.ndarray],
    *,
    case: str,
) -> int:
    if not trace:
        return 0
    t_ms = trace.get("t_ms")
    if t_ms is None:
        return 0
    t_ms_arr = np.asarray(t_ms, dtype=float)
    if t_ms_arr.ndim != 1 or t_ms_arr.size == 0:
        return 0
    max_rings = 0
    cross_talk = float(res.get("cross_talk_level", 0.0))
    if case == "baseline":
        cross_talk = 0.0
    method = res.get("method", "")
    for sheet_name, signal_key in RING_TRACE_SHEETS.items():
        data = trace.get(signal_key)
        if data is None:
            continue
        arr = np.asarray(data, dtype=float)
        if arr.ndim != 2 or arr.shape[0] != t_ms_arr.size:
            continue
        max_rings = max(max_rings, int(arr.shape[1]))
        rows = rows_by_sheet.setdefault(sheet_name, [])
        for idx in range(t_ms_arr.size):
            row: Dict[str, Any] = {
                "timestamp": meta["timestamp"],
                "seed": int(meta.get("seed", 0)),
                "method": method,
                "cross_talk": cross_talk,
                "case": case,
                "t_ms": float(t_ms_arr[idx]),
            }
            for j in range(arr.shape[1]):
                row[f"ring_{j}"] = float(arr[idx, j])
            rows.append(row)
    return max_rings
