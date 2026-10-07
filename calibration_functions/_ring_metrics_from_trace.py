"""_ring_metrics_from_trace extracted from the calibration experiment runner."""

from __future__ import annotations

from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple
import numpy as np


def _ring_metrics_from_trace(
    detuning_pm: np.ndarray,
    *,
    lock_threshold_pm: float,
    sample_rate_hz: float,
    sim_time_s: float,
) -> Tuple[Dict[str, Any], np.ndarray]:
    """Compute raw peak, filtered RMS, and dwell-based settling from detuning in pm.

    detuning_pm has shape (time_samples, rings). A first-order 0.25 s low-pass
    filter feeds settling and RMS calculations. Settling is the start of the
    first 0.25 s interval strictly below lock_threshold_pm for all rings; later
    excursions do not revoke it. RMS uses the final 1 s of filtered samples;
    peak_pm uses the full unfiltered trace. A missing dwell is represented by
    settled_all=False and settle_ms equal to the simulated horizon in ms.

    Returns (metrics, filtered_trace). Requires nonempty traces and positive
    sample_rate_hz; no input-domain validation is performed here.
    """
    steps, n = detuning_pm.shape
    dt = 1.0 / float(sample_rate_hz)
    abs_raw = np.abs(detuning_pm)
    peak_pm_per_ring = [float(x) for x in np.max(abs_raw, axis=0).tolist()]
    peak_pm = float(np.max(np.array(peak_pm_per_ring, dtype=float))) if peak_pm_per_ring else float("nan")
    worst_ring_id = int(np.argmax(np.array(peak_pm_per_ring, dtype=float))) if peak_pm_per_ring else 0

    settle_tau_s = 0.25
    alpha = float(np.clip(dt / settle_tau_s, 1e-4, 1.0))
    d_lp = np.zeros_like(detuning_pm)
    d_lp[0] = detuning_pm[0]
    for k_lp in range(1, steps):
        d_lp[k_lp] = (1.0 - alpha) * d_lp[k_lp - 1] + alpha * detuning_pm[k_lp]
    abs_lp = np.abs(d_lp)

    dwell_s = 0.25
    dwell_steps = max(1, int(round(dwell_s * sample_rate_hz)))
    settle_step_all: Optional[int] = None
    settle_step_per_ring: List[Optional[int]] = [None for _ in range(n)]

    below_all = np.all(abs_lp < float(lock_threshold_pm), axis=1)
    viol = (~below_all).astype(int)
    prefix = np.concatenate([np.array([0], dtype=int), np.cumsum(viol)])
    for k0 in range(0, steps - dwell_steps + 1):
        if int(prefix[k0 + dwell_steps] - prefix[k0]) == 0:
            settle_step_all = int(k0)
            break

    for i in range(n):
        below_i = abs_lp[:, i] < float(lock_threshold_pm)
        viol_i = (~below_i).astype(int)
        prefix_i = np.concatenate([np.array([0], dtype=int), np.cumsum(viol_i)])
        for k0 in range(0, steps - dwell_steps + 1):
            if int(prefix_i[k0 + dwell_steps] - prefix_i[k0]) == 0:
                settle_step_per_ring[i] = int(k0)
                break

    window = max(1, int(1.0 * sample_rate_hz))
    d_win = d_lp[-window:, :]
    rms_pm = float(np.sqrt(np.mean(d_win**2)))
    rms_pm_per_ring = [float(x) for x in np.sqrt(np.mean(d_win**2, axis=0)).tolist()]

    settle_ms = 1000.0 * (float(settle_step_all) * dt) if settle_step_all is not None else 1000.0 * sim_time_s
    settle_ms_per_ring = [
        1000.0 * (float(s) * dt) if s is not None else 1000.0 * sim_time_s for s in settle_step_per_ring
    ]

    metrics = {
        "settled_all": bool(settle_step_all is not None),
        "settle_step_all": int(settle_step_all) if settle_step_all is not None else None,
        "settle_step_per_ring": [int(s) if s is not None else None for s in settle_step_per_ring],
        "settle_ms": float(settle_ms),
        "settle_ms_per_ring": [float(x) for x in settle_ms_per_ring],
        "peak_pm": float(peak_pm),
        "peak_pm_per_ring": [float(x) for x in peak_pm_per_ring],
        "rms_pm": float(rms_pm),
        "rms_pm_per_ring": [float(x) for x in rms_pm_per_ring],
        "worst_ring_id": int(worst_ring_id),
    }
    return metrics, d_lp
