"""generate_mesh_plots extracted from the calibration experiment runner."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from typing import Dict

from ._plot_mesh_convergence import _plot_mesh_convergence
from ._plot_mesh_cut_edge_residuals import _plot_mesh_cut_edge_residuals
from ._plot_mesh_jacobian_conditioning import _plot_mesh_jacobian_conditioning
from .log import log


def generate_mesh_plots(run_dir: Path, mesh_results: Dict[str, Any]) -> None:
    if not mesh_results:
        return
    try:
        import matplotlib.pyplot as plt
    except Exception as exc:  # pragma: no cover - plotting optional
        log(f"[plot] skipping mesh plots (matplotlib unavailable: {exc})", force=True)
        return
    _plot_mesh_convergence(run_dir, mesh_results, plt=plt)
    _plot_mesh_cut_edge_residuals(run_dir, mesh_results, plt=plt)
    _plot_mesh_jacobian_conditioning(run_dir, mesh_results, plt=plt)
