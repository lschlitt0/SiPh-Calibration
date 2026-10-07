"""simulate_ring_scan extracted from the calibration experiment runner."""

from __future__ import annotations

from typing import Any
from typing import Dict
from typing import Optional
from typing import Tuple
import numpy as np
import time

from ._ring_cross_talk_matrix import _ring_cross_talk_matrix
from ._ring_metrics_from_trace import _ring_metrics_from_trace
from ._seed_everything import _seed_everything
from ._standardize_ring_trace import _standardize_ring_trace
from .log_kv import log_kv
from .log_section import log_section
from .models import CalibrationConfig
from .models import MetricCounters
from .models import PhysicsParams
from .summarize_effort import summarize_effort


def simulate_ring_scan(
    cfg: CalibrationConfig,
    phys: PhysicsParams,
    *,
    capture_traces: bool = True,
) -> Dict[str, Any]:
    """Simulate the sequential retuning baseline with direct noisy detuning readout.

    Uses the same pm/K, pm/command, thermal time constant, and 5 s horizon as the
    dither model, but its initial-state/noise seeds differ. All rings are sampled
    at 1 kHz; only the active ring receives a clipped command increment. The
    active index advances after 0.15 s of consecutive in-threshold measurements.
    Returns post-run metrics and optional traces, using phys only as metadata.

    The preserved update is -seq_gain*error/abs(g), while g is negative in the
    plant. A positive detuning therefore initially drives a command that increases
    detuning. Treat this baseline's sign convention as a research issue before
    interpreting performance differences as a comparison of working controllers.
    """
    _seed_everything(cfg.seed + 71)
    t_start = time.perf_counter()
    rng_init = np.random.default_rng(int(cfg.seed + 71))
    log_section("Ring-bank case (sequential scan)")

    n = int(cfg.ring_count)
    sample_rate_hz = 1000.0
    dt = 1.0 / sample_rate_hz
    sim_time_s = 5.0
    steps = int(sim_time_s / dt)

    pm_per_K = 12.0
    drift_pm = float(cfg.drift_K) * pm_per_K
    d0 = drift_pm * (0.8 + 0.4 * rng_init.random(n))

    g = -25.0
    tau_s = 0.015
    lock_threshold_pm = 0.15
    noise_std = 0.05
    seq_gain = 0.02
    dwell_steps_target = max(1, int(round(0.15 * sample_rate_hz)))
    cross_talk_level = float(cfg.ring_cross_talk)
    capture_traces = bool(capture_traces)

    def run_once(
        *, crosstalk: float, seed: int, capture: bool
    ) -> Tuple[Dict[str, Any], Optional[Dict[str, np.ndarray]], MetricCounters]:
        rng = np.random.default_rng(int(seed))
        d = d0.copy()
        u = np.zeros(n, dtype=float)
        C = _ring_cross_talk_matrix(n, crosstalk)
        det_hist = np.zeros((steps, n), dtype=float)
        trace: Optional[Dict[str, np.ndarray]] = None
        metrics_local = MetricCounters()
        if capture:
            trace = {
                "d_pm": np.zeros((steps, n), dtype=float),
                "u_cmd": np.zeros((steps, n), dtype=float),
                "e_hat": np.zeros((steps, n), dtype=float),
            }
        active = 0
        dwell_ctr = 0
        for k in range(steps):
            metrics_local.probe_count += int(n)
            u_eff = u + C @ u
            d_target = drift_pm + g * u_eff
            # Explicit Euler integration; dt/tau_s controls discrete stability.
            d += (dt / tau_s) * (d_target - d)

            meas = d + float(noise_std) * rng.standard_normal(n)
            err = float(meas[active])
            u_step = float(np.clip(-seq_gain * err / max(1.0, abs(g)), -0.01, 0.01))
            u_new = float(np.clip(u[active] + u_step, -0.4, 0.4))
            if abs(u_new - u[active]) > 1e-12:
                metrics_local.record_hw_write()
            u[active] = u_new
            metrics_local.solver_iter_count += 1

            det_hist[k] = d
            if trace is not None:
                trace["d_pm"][k] = d
                trace["u_cmd"][k] = u
                trace["e_hat"][k] = meas

            if abs(err) < lock_threshold_pm:
                dwell_ctr += 1
                if dwell_ctr >= dwell_steps_target:
                    active = (active + 1) % n
                    dwell_ctr = 0
            else:
                dwell_ctr = 0

        metrics_raw, d_lp = _ring_metrics_from_trace(
            det_hist, lock_threshold_pm=lock_threshold_pm, sample_rate_hz=sample_rate_hz, sim_time_s=sim_time_s
        )
        metrics_local.probe_time_s = float(sim_time_s)
        metrics_local.solve_time_s += float(sim_time_s)
        if trace is not None:
            trace["d_lp_pm"] = d_lp
        return metrics_raw, trace, metrics_local

    primary_metrics, primary_trace, metrics_primary = run_once(
        crosstalk=cross_talk_level, seed=cfg.seed + 777, capture=capture_traces
    )
    walltime_s = float(time.perf_counter() - t_start)
    effort = summarize_effort(
        metrics_primary,
        probe_rounds_effective=int(steps),
        n_entities=n,
        walltime_s=sim_time_s,
    )

    t_ms = (np.arange(steps, dtype=float) * dt * 1000.0).astype(float)
    trace = _standardize_ring_trace(primary_trace, t_ms) if capture_traces else None

    result = {
        "method": "scan",
        "controller_family": "sequential scan-and-retune",
        "Nr": int(n),
        "cross_talk_level": float(cross_talk_level),
        "step_K": float(cfg.drift_K),
        "lock_threshold_pm": float(lock_threshold_pm),
        "settled_all": bool(primary_metrics.get("settled_all", False)),
        "settle_step_all": primary_metrics.get("settle_step_all", None),
        "settle_ms": float(primary_metrics["settle_ms"]),
        "settle_ms_per_ring": [float(x) for x in primary_metrics.get("settle_ms_per_ring", [])],
        "peak_pm": float(primary_metrics["peak_pm"]),
        "peak_pm_per_ring": [float(x) for x in primary_metrics.get("peak_pm_per_ring", [])],
        "rms_pm": float(primary_metrics["rms_pm"]),
        "rms_pm_per_ring": [float(x) for x in primary_metrics.get("rms_pm_per_ring", [])],
        "worst_ring_id": int(primary_metrics.get("worst_ring_id", 0)),
        "rings": int(n),
        "drift_K": float(cfg.drift_K),
        "relock_ms": float(primary_metrics["settle_ms"]),
        "overshoot_pm": float(primary_metrics["peak_pm"]),
        "steady_err_pm": float(primary_metrics["rms_pm"]),
        "seq_gain": float(seq_gain),
        "update_clip": 0.01,
        "switch_dwell_ms": float(1000.0 * dwell_steps_target / sample_rate_hz),
        "sim_time_s": float(sim_time_s),
        "control_horizon_s": float(sim_time_s),
        "sample_rate_Hz": float(sample_rate_hz),
        "sample_rate_hz": float(sample_rate_hz),
        "walltime": float(walltime_s),
        "trace": trace if trace is not None else {},
        "trace_len": int(steps),
        "physics": {"dndT": phys.dndT, "L_ring_um": phys.L_ring_um},
        "probe_count": int(effort["probe_count"]),
        "probe_rounds_effective": int(effort["probe_rounds_effective"]),
        "hw_write_count": int(effort["hw_write_count"]),
        "hw_commit_count": int(effort["hw_write_count"]),
        "hw_element_touch_count": int(effort["hw_element_touch_count"]),
        "solver_iter_count": int(effort["solver_iter_count"]),
        "effort": effort,
    }
    log_kv("Scan settle (ms)", f"{result['settle_ms']:.2f}")
    log_kv("Scan peak detuning (pm)", f"{result['peak_pm']:.2f}")
    log_kv("Scan RMS (pm)", f"{result['rms_pm']:.3f}")
    return result
