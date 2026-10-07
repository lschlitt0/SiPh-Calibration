"""simulate_ring_bank extracted from the calibration experiment runner."""

from __future__ import annotations

from typing import Any
from typing import Dict
from typing import Optional
from typing import Tuple
import math
import numpy as np
import time

from ._ring_cross_talk_matrix import _ring_cross_talk_matrix
from ._ring_metrics_from_trace import _ring_metrics_from_trace
from ._seed_everything import _seed_everything
from ._standardize_ring_trace import _standardize_ring_trace
from .log_kv import log_kv
from .log_section import log_section
from .models import CalibrationConfig
from .models import IncrementalPID
from .models import MetricCounters
from .models import PhysicsParams
from .summarize_effort import summarize_effort


def simulate_ring_bank(
    cfg: CalibrationConfig,
    phys: PhysicsParams,
    *,
    capture_traces: bool = True,
    method_label: str = "parallel",
) -> Dict[str, Any]:
    """Simulate parallel dither-based locking of thermally coupled rings for 5 s.

    cfg.drift_K maps to detuning through the local 12 pm/K coefficient. At 1 kHz,
    an explicit Euler thermal state tracks drift_pm + g*(u_drive + C@u_drive),
    where g=-25 pm per unitless command and tau=0.015 s. A quadratic readout
    p=d**2 plus Gaussian noise is a proxy signal in pm^2, not optical power.
    Phase-compensated lock-in filtering estimates signed detuning; incremental
    controllers update at 50 Hz with command/slew limits. The run always reaches
    its fixed horizon; lock thresholds are used only for post-run metrics.

    Returns metrics, effort, and optional (5000, rings) trace arrays. A separate
    zero-cross-talk run uses the same initial state/noise seed for comparison;
    effort counters describe the primary run. phys is descriptive metadata only.
    Noise is seeded; wall-clock runtime is machine dependent.
    """
    _seed_everything(cfg.seed + 17)
    t_start = time.perf_counter()
    rng_init = np.random.default_rng(int(cfg.seed + 17))
    log_section(f"Ring-bank case ({method_label})")

    n = int(cfg.ring_count)
    sample_rate_hz = 1000.0
    dt = 1.0 / sample_rate_hz
    pid_rate_hz = 50.0
    pid_decim = max(1, int(round(sample_rate_hz / pid_rate_hz)))
    pid_rate_hz = sample_rate_hz / float(pid_decim)
    sim_time_s = 5.0
    steps = int(sim_time_s / dt)

    # Detuning units: pm (toy). Convert applied temperature step to detuning.
    pm_per_K = 12.0
    drift_pm = float(cfg.drift_K) * pm_per_K
    d0 = drift_pm * (0.8 + 0.4 * rng_init.random(n))  # initial detuning after step disturbance

    # Heater control u is unitless in toy model; negative gain reduces detuning.
    g = -25.0  # pm per unit control
    tau_s = 0.015  # thermal time constant

    cross_talk_level = float(cfg.ring_cross_talk)

    # Stagger dither frequencies in Hz. Phase/attenuation compensation below
    # uses the first-order thermal response; larger banks extend this frequency set.
    dither_base_hz = 5.0
    dither_step_hz = 0.7
    freqs = dither_base_hz + dither_step_hz * np.arange(n, dtype=float)
    dither_amp_u = 0.01  # small-amplitude probing in actuator units

    omega = 2.0 * math.pi * freqs
    # Phase + attenuation of the first-order thermal response at each dither frequency.
    phase = -np.arctan(omega * tau_s)
    atten = 1.0 / np.sqrt(1.0 + (omega * tau_s) ** 2)

    # PI-family controller parameters (toy; includes slew + saturation safeguards).
    Kp, Ki, Kd = 0.0, 0.002, 0.0
    lock_tau_s = 0.2
    noise_std = 0.05
    pids = [
        IncrementalPID(
            Kp=Kp,
            Ki=Ki,
            Kd=Kd,
            u_min=-0.4,
            u_max=0.4,
            du_max=0.005,
        )
        for _ in range(n)
    ]

    lock_threshold_pm = 0.15

    capture_traces = bool(capture_traces)

    def run_once(
        *, crosstalk: float, seed: int, capture: bool
    ) -> Tuple[Dict[str, Any], Optional[Dict[str, np.ndarray]], MetricCounters]:
        rng = np.random.default_rng(int(seed))
        d = d0.copy()
        u = np.zeros(n, dtype=float)
        C = _ring_cross_talk_matrix(n, crosstalk)
        lock = np.zeros(n, dtype=float)
        p_mean = np.zeros(n, dtype=float)
        lock_alpha = float(np.clip(dt / float(lock_tau_s), 1e-4, 1.0))
        lock_gain = 1.0 / (g * dither_amp_u * atten)
        lock_gain = lock_gain.astype(float)
        metrics_local = MetricCounters()

        local_pids = [
            IncrementalPID(
                Kp=Kp,
                Ki=Ki,
                Kd=Kd,
                u_min=pids[0].u_min,
                u_max=pids[0].u_max,
                du_max=pids[0].du_max,
            )
            for _ in range(n)
        ]

        trace_detuning = np.zeros((steps, n), dtype=float)
        trace: Optional[Dict[str, np.ndarray]] = None
        if capture:
            trace = {
                "d_pm": np.zeros((steps, n), dtype=float),
                "u_cmd": np.zeros((steps, n), dtype=float),
                "e_hat": np.zeros((steps, n), dtype=float),
            }

        for k in range(steps):
            metrics_local.probe_count += int(n)
            t = k * dt
            ref_dither = np.sin(omega * t)
            dither_u = dither_amp_u * ref_dither
            u_drive = u + dither_u

            u_eff = u_drive + C @ u_drive
            d_target = drift_pm + g * u_eff
            # Explicit Euler integration; dt/tau_s controls discrete stability.
            d += (dt / tau_s) * (d_target - d)

            # Quadratic proxy readout: d in pm implies signal/noise in pm^2.
            # Mixing at the imposed tone extracts a signed detuning estimate.
            p = d**2 + float(noise_std) * rng.standard_normal(n)
            p_mean = (1.0 - lock_alpha) * p_mean + lock_alpha * p
            p_ac = p - p_mean

            ref_demod = np.sin(omega * t + phase)
            lock = (1.0 - lock_alpha) * lock + lock_alpha * (p_ac * ref_demod)
            e_hat = lock_gain * lock
            e_hat = np.clip(e_hat, -20.0, 20.0)

            if (k % pid_decim) == 0:
                for i in range(n):
                    metrics_local.solver_iter_count += 1
                    u_new = local_pids[i].step(float(e_hat[i]))
                    if abs(u_new - u[i]) > 1e-12:
                        metrics_local.record_hw_write()
                    u[i] = u_new

            trace_detuning[k] = d
            if trace is not None:
                trace["d_pm"][k] = d
                trace["u_cmd"][k] = u
                trace["e_hat"][k] = e_hat

        metrics_raw, d_lp = _ring_metrics_from_trace(
            trace_detuning, lock_threshold_pm=lock_threshold_pm, sample_rate_hz=sample_rate_hz, sim_time_s=sim_time_s
        )
        metrics_local.probe_time_s = float(sim_time_s)
        metrics_local.solve_time_s += float(sim_time_s)
        if trace is not None:
            trace["d_lp_pm"] = d_lp

        return metrics_raw, trace, metrics_local

    primary_metrics, primary_trace, metrics_primary = run_once(
        crosstalk=cross_talk_level, seed=cfg.seed + 999, capture=capture_traces
    )
    baseline_metrics, baseline_trace, _ = run_once(crosstalk=0.0, seed=cfg.seed + 999, capture=capture_traces)
    walltime_s = float(time.perf_counter() - t_start)
    effort = summarize_effort(
        metrics_primary,
        probe_rounds_effective=int(steps),
        n_entities=n,
        walltime_s=sim_time_s,
    )

    t_ms = (np.arange(steps, dtype=float) * dt * 1000.0).astype(float)
    trace = _standardize_ring_trace(primary_trace, t_ms) if capture_traces else None
    baseline_trace = _standardize_ring_trace(baseline_trace, t_ms) if capture_traces else None

    result = {
        "method": str(method_label),
        "Nr": int(n),
        "dither_freqs": [float(x) for x in freqs.tolist()],
        "KpKiKd": [float(Kp), float(Ki), float(Kd)],
        "controller_family": "incremental PI-family",
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
        "baseline_settle_ms": float(baseline_metrics["settle_ms"]),
        "rings": int(n),
        "drift_K": float(cfg.drift_K),
        "relock_ms": float(primary_metrics["settle_ms"]),
        "overshoot_pm": float(primary_metrics["peak_pm"]),
        "steady_err_pm": float(primary_metrics["rms_pm"]),
        "dither_freq_Hz": float(dither_base_hz),
        "dither_base_hz": float(dither_base_hz),
        "dither_step_hz": float(dither_step_hz),
        "dither_amp_u": float(dither_amp_u),
        "pid_rate_Hz": float(pid_rate_hz),
        "pid_rate_hz": float(pid_rate_hz),
        "sample_rate_Hz": float(sample_rate_hz),
        "sample_rate_hz": float(sample_rate_hz),
        "Kp": float(Kp),
        "Ki": float(Ki),
        "Kd": float(Kd),
        "lock_tau_s": float(lock_tau_s),
        "control_horizon_s": float(sim_time_s),
        "walltime": float(walltime_s),
        "trace": trace if trace is not None else {},
        "baseline_trace": baseline_trace if baseline_trace is not None else {},
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
    log_kv("Settle time (ms)", f"{result['settle_ms']:.2f}")
    log_kv("Peak detuning (pm)", f"{result['peak_pm']:.2f}")
    log_kv("RMS detuning (pm)", f"{result['rms_pm']:.3f}")
    log_kv("Baseline settle (ms)", f"{result['baseline_settle_ms']:.2f}")
    return result
