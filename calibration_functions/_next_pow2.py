"""_next_pow2 extracted from the calibration experiment runner."""

from __future__ import annotations

def _next_pow2(n: int) -> int:
    n = int(n)
    if n <= 1:
        return 1
    return 1 << (n - 1).bit_length()
