"""_parse_method_list extracted from the calibration experiment runner."""

from __future__ import annotations

from typing import List
from typing import Sequence


def _parse_method_list(raw: str, allowed: Sequence[str]) -> List[str]:
    allowed_list = [a.lower() for a in allowed]
    allowed_set = set(allowed_list)
    if not raw:
        return allowed_list
    items: List[str] = []
    for tok in str(raw).split(","):
        name = tok.strip().lower()
        if not name or name not in allowed_set:
            continue
        if name not in items:
            items.append(name)
    return items or allowed_list
