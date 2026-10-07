"""expand_sweep_spec extracted from the calibration experiment runner."""

from __future__ import annotations

from typing import Any
from typing import Dict
from typing import List
from typing import Optional

from ._expand_token_list import _expand_token_list


def expand_sweep_spec(spec: Optional[str]) -> List[Dict[str, Any]]:
    """Expand semicolon-separated key=value lists into a Cartesian product.

    Comma-separated values and inclusive integer ranges such as seed=1..5 are
    supported. Floating ranges use linspace with a step count inferred from their
    span; comma-separated floats give explicit sampling points.
    """
    if not spec:
        return []
    parts = [p.strip() for p in str(spec).split(";") if p.strip()]
    value_map: Dict[str, List[Any]] = {}
    for part in parts:
        if "=" not in part:
            continue
        key, raw_vals = part.split("=", 1)
        value_map[key.strip()] = _expand_token_list(raw_vals)

    combos: List[Dict[str, Any]] = [dict()]
    for key, vals in value_map.items():
        next_combos: List[Dict[str, Any]] = []
        for base in combos:
            for v in vals:
                updated = dict(base)
                updated[key] = v
                next_combos.append(updated)
        combos = next_combos
    return combos
