"""run_ring_suite extracted from the calibration experiment runner."""

from __future__ import annotations

from dataclasses import replace
from typing import Any
from typing import Dict
from typing import List
from typing import Sequence
from typing import Tuple

from ._cross_talk_sweep_values import _cross_talk_sweep_values
from ._ring_row_from_result import _ring_row_from_result
from .models import CalibrationConfig
from .models import PhysicsParams
from .simulate_ring_bank import simulate_ring_bank
from .simulate_ring_scan import simulate_ring_scan


def run_ring_suite(
    cfg: CalibrationConfig, phys: PhysicsParams, methods: Sequence[str], meta: Dict[str, Any]
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """Run selected ring methods at each cross-talk value and return results/rows.

    Each simulation reuses its method-specific seed offsets across cross-talk
    values, providing matched random streams within each method's sweep.
    """
    ring_results: Dict[str, Any] = {}
    ring_rows: List[Dict[str, Any]] = []
    ct_values = _cross_talk_sweep_values(cfg)
    for method in methods:
        method_results: List[Dict[str, Any]] = []
        for idx_ct, ct_val in enumerate(ct_values):
            cfg_ct = replace(cfg, ring_cross_talk=float(ct_val))
            if method == "parallel":
                res = simulate_ring_bank(cfg_ct, phys, capture_traces=True, method_label="parallel")
            elif method == "scan":
                res = simulate_ring_scan(cfg_ct, phys, capture_traces=True)
            else:
                continue
            res["sweep_idx"] = int(idx_ct)
            res["cross_talk_value"] = float(ct_val)
            method_results.append(res)
            ring_rows.append(_ring_row_from_result(res, cfg_ct, meta))
        if method_results:
            ring_results[method] = method_results
    return ring_results, ring_rows
