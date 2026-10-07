"""pick_ring_result extracted from the calibration experiment runner."""

from __future__ import annotations

from typing import Any
from typing import Dict
from typing import Optional
from typing import Sequence


def pick_ring_result(res_list: Sequence[Any], preferred_ct: float = 0.06) -> Optional[Dict[str, Any]]:
    """Pick the ring result whose cross-talk value is closest to the requested manuscript point."""
    best: Optional[Dict[str, Any]] = None
    best_diff: Optional[float] = None
    for item in res_list:
        if not isinstance(item, dict):
            continue
        ct_val = item.get("cross_talk_value", item.get("cross_talk_level", None))
        try:
            diff = abs(float(ct_val) - float(preferred_ct))
        except Exception:
            continue
        if best is None or best_diff is None or diff < best_diff:
            best = item
            best_diff = diff
    if best is not None:
        return best
    for item in res_list:
        if isinstance(item, dict):
            return item
    return None
