"""_jacobian_condition_number extracted from the calibration experiment runner."""

from __future__ import annotations

import numpy as np


def _jacobian_condition_number(J: np.ndarray) -> float:
    """Return the largest/smallest singular-value ratio, or inf for a zero minimum.

    For a wide Jacobian, this ratio does not expose all unobservable input-space
    directions; it is not by itself a full-column-rank or identifiability test.
    """
    if J.size == 0:
        return float("inf")
    s = np.linalg.svd(J, compute_uv=False)
    smax = float(np.max(s))
    smin = float(np.min(s))
    if smin <= 0.0:
        return float("inf")
    return smax / smin
