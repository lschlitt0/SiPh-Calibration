"""_ring_row_from_result extracted from the calibration experiment runner."""

from __future__ import annotations

from typing import Any
from typing import Dict

from .models import CalibrationConfig


def _ring_row_from_result(result: Dict[str, Any], cfg: CalibrationConfig, meta: Dict[str, Any]) -> Dict[str, Any]:
    walltime = result.get("walltime", result.get("walltime_s", None))
    effort = result.get("effort", {})

    def _eff(key: str, default: Any = "") -> Any:
        return result.get(key, effort.get(key, default))

    return {
        "timestamp": meta["timestamp"],
        "seed": int(cfg.seed),
        "method": result.get("method", ""),
        "rings": result.get("Nr", cfg.ring_count),
        "cross_talk": result.get("cross_talk_level", cfg.ring_cross_talk),
        "probe_count": _eff("probe_count", ""),
        "probe_rounds_effective": _eff("probe_rounds_effective", _eff("probe_count", "")),
        "hw_write_count": _eff("hw_write_count", ""),
        "hw_element_touch_count": _eff("hw_element_touch_count", ""),
        "solver_iter_count": _eff("solver_iter_count", ""),
        "settled_all": result.get("settled_all", ""),
        "settle_step_all": result.get("settle_step_all", ""),
        "settle_ms": result.get("settle_ms", ""),
        "peak_pm": result.get("peak_pm", ""),
        "rms_pm": result.get("rms_pm", ""),
        "walltime_s": walltime,
        "baseline_settle_ms": result.get("baseline_settle_ms", ""),
        "drift_K": result.get("drift_K", cfg.drift_K),
        "controller_family": result.get("controller_family", ""),
        "lock_threshold_pm": result.get("lock_threshold_pm", ""),
        "control_horizon_s": result.get("control_horizon_s", ""),
        "dither_base_hz": result.get("dither_base_hz", ""),
        "dither_step_hz": result.get("dither_step_hz", ""),
        "pid_rate_hz": result.get("pid_rate_hz", ""),
        "Kp": result.get("Kp", ""),
        "Ki": result.get("Ki", ""),
        "Kd": result.get("Kd", ""),
        "seq_gain": result.get("seq_gain", ""),
        "update_clip": result.get("update_clip", ""),
        "switch_dwell_ms": result.get("switch_dwell_ms", ""),
        "sim_time_s": result.get("sim_time_s", ""),
    }
