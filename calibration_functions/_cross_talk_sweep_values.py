"""_cross_talk_sweep_values extracted from the calibration experiment runner."""

from __future__ import annotations

from typing import List

from ._expand_token_list import _expand_token_list
from .models import CalibrationConfig


def _cross_talk_sweep_values(cfg: CalibrationConfig) -> List[float]:
    vals = _expand_token_list(cfg.ring_cross_talk_sweep) if cfg.ring_cross_talk_sweep else []
    if not vals:
        vals = [cfg.ring_cross_talk]
    uniq: List[float] = []
    for v in vals:
        try:
            f = float(v)
        except Exception:
            continue
        if f not in uniq:
            uniq.append(f)
    base_ct = float(cfg.ring_cross_talk)
    if base_ct not in uniq:
        uniq.append(base_ct)
    return uniq
