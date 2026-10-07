"""_orthogonal_sign_patterns extracted from the calibration experiment runner."""

from __future__ import annotations

import numpy as np

from ._hadamard import _hadamard
from ._next_pow2 import _next_pow2


def _orthogonal_sign_patterns(n_patterns: int, dim: int, *, seed: int) -> np.ndarray:
    """Return seeded sign patterns with shape (n_patterns, dim) from Hadamard rows.

    The full all-ones row is omitted and each retained row receives a random sign.
    Truncating the matrix to dim columns need not preserve row orthogonality;
    clipping the resulting actuator probes can further change their geometry.
    """
    dim = int(dim)
    n_patterns = int(n_patterns)
    if dim <= 0:
        raise ValueError("dim must be >= 1")
    if n_patterns <= 0:
        raise ValueError("n_patterns must be >= 1")

    size = _next_pow2(max(dim, n_patterns + 1))
    H = _hadamard(size)
    # Skip the all-ones row to avoid degenerate “DC” probing.
    patterns = H[1 : 1 + n_patterns, :dim].copy()
    rng = np.random.default_rng(int(seed))
    patterns *= rng.choice([-1.0, 1.0], size=(n_patterns, 1))
    return patterns
