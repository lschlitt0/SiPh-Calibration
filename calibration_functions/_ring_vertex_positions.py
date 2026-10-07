"""_ring_vertex_positions extracted from the calibration experiment runner."""

from __future__ import annotations

import math
import numpy as np


def _ring_vertex_positions(n: int) -> np.ndarray:
    n = int(n)
    if n <= 0:
        return np.zeros((0, 2), dtype=float)
    angles = np.linspace(0.0, 2.0 * math.pi, n, endpoint=False)
    return np.column_stack((np.cos(angles), np.sin(angles))).astype(float)
