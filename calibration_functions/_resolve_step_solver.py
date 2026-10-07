"""_resolve_step_solver extracted from the calibration experiment runner."""

from __future__ import annotations

def _resolve_step_solver(opt_solver: str) -> str:
    val = str(opt_solver or "").strip().lower()
    if val in ("auto", "docplex", "cplex"):
        return val
    return "linear"
