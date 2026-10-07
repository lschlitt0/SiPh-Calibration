"""summarize_effort extracted from the calibration experiment runner."""

from __future__ import annotations

from typing import Any
from typing import Dict

from .models import MetricCounters


def summarize_effort(metrics: MetricCounters, *, probe_rounds_effective: int, n_entities: int, walltime_s: float) -> Dict[str, Any]:
    """Collect effort counters + derived rates in a single dict."""
    derived = metrics.derived(n_entities, walltime_s)
    return {
        "probe_count": int(metrics.probe_count),
        "probe_rounds_effective": int(probe_rounds_effective),
        "hw_write_count": int(metrics.hw_write_count),
        "hw_element_touch_count": int(metrics.hw_element_touch_count),
        "solver_iter_count": int(metrics.solver_iter_count),
        "probe_time_s": float(metrics.probe_time_s),
        "solve_time_s": float(metrics.solve_time_s),
        **derived,
    }
