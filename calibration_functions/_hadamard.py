"""_hadamard extracted from the calibration experiment runner."""

from __future__ import annotations

import numpy as np


def _hadamard(n: int) -> np.ndarray:
    """
    Hadamard matrix of order n (n must be a power of 2), entries in {+1,-1}.
    """
    n = int(n)
    if n <= 0 or (n & (n - 1)) != 0:
        raise ValueError("Hadamard order must be a power of 2")
    H = np.array([[1.0]], dtype=float)
    while H.shape[0] < n:
        H = np.block([[H, H], [H, -H]])
    return H
