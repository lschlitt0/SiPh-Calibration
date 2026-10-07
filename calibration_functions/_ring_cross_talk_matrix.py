"""_ring_cross_talk_matrix extracted from the calibration experiment runner."""

from __future__ import annotations

import numpy as np


def _ring_cross_talk_matrix(n: int, level: float) -> np.ndarray:
    """Return dimensionless exponentially decaying inter-ring command coupling.

    C[i,j] = level*exp(-abs(i-j)/2) off diagonal, with zero self-coupling.
    The plant applies u_eff = u + C @ u; the matrix is not row-normalized.
    """
    idx = np.arange(n)
    C = float(level) * np.exp(-np.abs(idx[:, None] - idx[None, :]) / 2.0)
    np.fill_diagonal(C, 0.0)
    return C.astype(float)
