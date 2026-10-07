"""_standardize_ring_trace extracted from the calibration experiment runner."""

from __future__ import annotations

from typing import Dict
from typing import Optional
import numpy as np


def _standardize_ring_trace(
    trace: Optional[Dict[str, np.ndarray]], t_ms: np.ndarray
) -> Optional[Dict[str, np.ndarray]]:
    if trace is None:
        return None
    det = trace.get("d_pm")
    det_lp = trace.get("d_lp_pm", det)
    return {
        "t_ms": np.asarray(t_ms, dtype=float),
        "detuning_pm": np.asarray(det, dtype=float) if det is not None else np.array([], dtype=float),
        "detuning_lp_pm": np.asarray(det_lp, dtype=float) if det_lp is not None else np.array([], dtype=float),
        "u_cmd": np.asarray(trace.get("u_cmd"), dtype=float) if trace.get("u_cmd") is not None else np.array([], dtype=float),
        "e_hat": np.asarray(trace.get("e_hat"), dtype=float) if trace.get("e_hat") is not None else np.array([], dtype=float),
    }
