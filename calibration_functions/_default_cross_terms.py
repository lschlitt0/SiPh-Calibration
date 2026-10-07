"""_default_cross_terms extracted from the calibration experiment runner."""

from __future__ import annotations

from typing import List
from typing import Tuple


def _default_cross_terms(m: int, *, max_terms: int = 64) -> List[Tuple[int, int]]:
    """Return adjacent input-index pairs, capped at max_terms in index order."""
    pairs: List[Tuple[int, int]] = []
    for a in range(int(m) - 1):
        pairs.append((a, a + 1))
        if len(pairs) >= int(max_terms):
            break
    return pairs
