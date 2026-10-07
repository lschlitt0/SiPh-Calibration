"""_mesh_row_from_result extracted from the calibration experiment runner."""

from __future__ import annotations

from typing import Any
from typing import Dict

from .models import CalibrationConfig


def _mesh_row_from_result(result: Dict[str, Any], cfg: CalibrationConfig, meta: Dict[str, Any]) -> Dict[str, Any]:
    walltime = result.get("walltime", result.get("walltime_s", None))
    effort = result.get("effort", {})

    def _eff(key: str, default: Any = "") -> Any:
        return result.get(key, effort.get(key, default))

    return {
        "timestamp": meta["timestamp"],
        "seed": int(cfg.seed),
        "method": result.get("method", ""),
        "N": result.get("N", cfg.mesh_size),
        "k": result.get("k", cfg.partitions),
        "outer_rounds_run": result.get("outer_rounds_run", ""),
        "probe_count": _eff("probe_count", ""),
        "probe_rounds_effective": _eff("probe_rounds_effective", _eff("probe_count", "")),
        "hw_write_count": _eff("hw_write_count", ""),
        "hw_element_touch_count": _eff("hw_element_touch_count", ""),
        "solver_iter_count": _eff("solver_iter_count", ""),
        "mse_final": result.get("mse_final", ""),
        "mse_cut_edges_before_polish": result.get("mse_cut_edges_before_polish", ""),
        "mse_cut_edges_after_polish": result.get("mse_cut_edges_after_polish", ""),
        "mse_internal_edges_before_polish": result.get("mse_internal_edges_before_polish", ""),
        "mse_internal_edges_after_polish": result.get("mse_internal_edges_after_polish", ""),
        "walltime_s": walltime,
        "target_mse": result.get("target_mse", cfg.target_mse),
        "probes_per_tuner": _eff("probes_per_tuner", ""),
        "hw_writes_per_tuner": _eff("hw_writes_per_tuner", ""),
        "hw_element_touches_per_tuner": _eff("hw_element_touches_per_tuner", ""),
        "seconds_per_probe": _eff("seconds_per_probe", ""),
        "seconds_per_solver_iter": _eff("seconds_per_solver_iter", ""),
        "partition_solver_requested": result.get("partition_solver_requested", ""),
        "partition_solver_used": result.get("partition_solver_used", ""),
        "opt_solver_requested": result.get("opt_solver_requested", ""),
        "opt_solver_used": result.get("opt_solver_used", ""),
        "subset_frac": result.get("subset_frac", ""),
        "subset_size": result.get("subset_size", result.get("tune_check_subset", "")),
        "rounds_cfg": result.get("rounds_cfg", ""),
        "step_size": result.get("step_size", result.get("tune_check_step", "")),
        "lr": result.get("lr", result.get("tune_check_lr", "")),
    }
