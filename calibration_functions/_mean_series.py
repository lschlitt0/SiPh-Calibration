"""_mean_series extracted from the calibration experiment runner."""

from __future__ import annotations

from typing import List
from typing import Sequence
import numpy as np


def _mean_series(series_list: Sequence[Sequence[float]]) -> List[float]:
    """Average finite values at each index; shorter histories do not contribute later."""
    if not series_list:
        return []
    max_len = max(len(s) for s in series_list)
    out: List[float] = []
    for i in range(max_len):
        vals = [float(s[i]) for s in series_list if len(s) > i and np.isfinite(s[i])]
        if not vals:
            break
        out.append(float(np.mean(vals)))
    return out
