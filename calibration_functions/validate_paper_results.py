"""validate_paper_results extracted from the calibration experiment runner."""

from __future__ import annotations

from typing import Any
from typing import Dict

from .models import CalibrationConfig
from .pick_ring_result import pick_ring_result


def validate_paper_results(cfg: CalibrationConfig, mesh_results: Dict[str, Any], ring_results: Dict[str, Any]) -> None:
    """Check export/accounting invariants with assertions; not a convergence test."""
    assert cfg.ring_cross_talk_sweep is None, "paper profile must disable ring cross-talk sweep"

    tunecheck = mesh_results.get("tunecheck")
    if isinstance(tunecheck, dict):
        subset_size = int(tunecheck.get("subset_size", tunecheck.get("tune_check_subset", 0)))
        rounds_run = int(tunecheck.get("rounds_run", tunecheck.get("rounds", 0)))
        assert int(tunecheck.get("probe_count", 0)) == 2 * subset_size * rounds_run

    for key in ("dfc", "global"):
        res = mesh_results.get(key)
        if isinstance(res, dict):
            assert "partition_solver_requested" in res
            assert "partition_solver_used" in res
            assert "opt_solver_requested" in res
            assert "opt_solver_used" in res

    for key in ("parallel", "scan"):
        res_any = ring_results.get(key)
        if isinstance(res_any, list):
            res = pick_ring_result(res_any, preferred_ct=float(cfg.ring_cross_talk))
        else:
            res = res_any
        if not isinstance(res, dict):
            continue
        trace_len = int(res.get("trace_len", 0))
        rings = int(res.get("rings", 0))
        assert int(res.get("probe_count", -1)) == rings * trace_len
        assert int(res.get("probe_rounds_effective", -1)) == trace_len

    parallel_primary = pick_ring_result(ring_results.get("parallel", []), preferred_ct=float(cfg.ring_cross_talk))
    if isinstance(parallel_primary, dict):
        selected_ct = float(parallel_primary.get("cross_talk_value", parallel_primary.get("cross_talk_level", -1.0)))
        assert abs(selected_ct - float(cfg.ring_cross_talk)) < 1e-12
