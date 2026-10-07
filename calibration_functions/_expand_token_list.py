"""_expand_token_list extracted from the calibration experiment runner."""

from __future__ import annotations

from typing import Any
from typing import List
import numpy as np


def _expand_token_list(raw_vals: str) -> List[Any]:
    vals: List[Any] = []
    for tok in str(raw_vals).split(","):
        token = tok.strip()
        if not token:
            continue
        if ".." in token:
            start, end = token.split("..", 1)
            try:
                a = int(start)
                b = int(end)
                vals.extend(list(range(a, b + 1)))
                continue
            except ValueError:
                try:
                    a = float(start)
                    b = float(end)
                    n_steps = max(1, int(round((b - a))))
                    vals.extend(list(np.linspace(a, b, n_steps + 1)))
                    continue
                except ValueError:
                    pass
        try:
            vals.append(int(token))
            continue
        except ValueError:
            try:
                vals.append(float(token))
                continue
            except ValueError:
                vals.append(token)
    return vals
