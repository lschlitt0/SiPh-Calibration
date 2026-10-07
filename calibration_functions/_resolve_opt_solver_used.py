"""_resolve_opt_solver_used extracted from the calibration experiment runner."""

from __future__ import annotations

def _resolve_opt_solver_used(opt_solver: str) -> str:
    solver_norm = str(opt_solver or "").strip().lower()
    if solver_norm in ("", "gn", "linear"):
        return "gn"
    if solver_norm in ("docplex", "cplex"):
        return "docplex"
    if solver_norm == "auto":
        try:
            from docplex.mp.model import Model  # noqa: F401
        except Exception:
            return "gn"
        return "docplex"
    return solver_norm
