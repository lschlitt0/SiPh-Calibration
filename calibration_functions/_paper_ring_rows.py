"""_paper_ring_rows extracted from the calibration experiment runner."""

from __future__ import annotations

from typing import Any
from typing import Dict
from typing import List

from .pick_ring_result import pick_ring_result


def _paper_ring_rows(ring_results: Dict[str, Any], *, preferred_ct: float) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    label_map = {
        "parallel": "Parallel dither-locking",
        "scan": "Sequential scan-and-retune",
    }
    for key in ("parallel", "scan"):
        res_any = ring_results.get(key)
        if isinstance(res_any, list):
            res = pick_ring_result(res_any, preferred_ct=preferred_ct)
        else:
            res = res_any
        if not isinstance(res, dict):
            continue
        rows.append(
            {
                "Method": label_map.get(key, str(res.get("method", key))),
                "Settle time (ms)": res.get("settle_ms", ""),
                "Peak error (pm)": res.get("peak_pm", ""),
                "RMS error (pm)": res.get("rms_pm", ""),
                "settled_all": bool(res.get("settled_all", False)),
                "control_horizon_s": float(res.get("control_horizon_s", 0.0)),
                "cross_talk_level": float(res.get("cross_talk_value", res.get("cross_talk_level", preferred_ct))),
                "method_key": key,
            }
        )
    return rows
