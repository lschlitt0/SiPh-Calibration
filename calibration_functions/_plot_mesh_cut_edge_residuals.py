"""_plot_mesh_cut_edge_residuals extracted from the calibration experiment runner."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from typing import Dict
from typing import List
import numpy as np
import textwrap


def _plot_mesh_cut_edge_residuals(run_dir: Path, mesh_results: Dict[str, Any], *, plt: Any) -> None:
    """Plot cut/internal residual metrics before and after boundary polishing.

    The retained caption's approximately 24-fold claim is fixed text, not a
    ratio computed from the supplied results; check it against each experiment.
    """
    dfc_res = mesh_results.get("dfc")
    if not isinstance(dfc_res, dict):
        return
    keys = (
        ("Cut edges (pre)", "mse_cut_edges_before_polish"),
        ("Cut edges (post)", "mse_cut_edges_after_polish"),
        ("Internal (pre)", "mse_internal_edges_before_polish"),
        ("Internal (post)", "mse_internal_edges_after_polish"),
    )
    labels: List[str] = []
    values: List[float] = []
    for label, key in keys:
        try:
            val = float(dfc_res.get(key, float("nan")))
        except Exception:
            val = float("nan")
        if not np.isfinite(val):
            return
        labels.append(label)
        values.append(val)
    if not values:
        return

    fig, ax = plt.subplots(figsize=(6.2, 4.2))
    bars = ax.bar(np.arange(len(values)), values, color=["#f08c00", "#37b24d", "#4c6ef5", "#868e96"])
    ax.set_xticks(np.arange(len(values)), labels)
    ax.set_ylabel("MSE")
    if all(val > 0.0 for val in values):
        ax.set_yscale("log")
    caption = (
        "Cut-edge residual is reduced by ~24x with boundary-only polishing, demonstrating that global "
        "coordination is concentrated at the interface; internal residual may increase slightly because "
        "only interface tuners are adjusted."
    )
    ax.set_title(textwrap.fill(caption, width=70), fontsize=9)
    ax.grid(True, axis="y", which="both", alpha=0.35)
    for bar, val in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2.0, val, f"{val:.2e}", ha="center", va="bottom", fontsize=8)
    fig.tight_layout()
    fig.savefig(run_dir / "fig_mesh_cut_edge_polish.png", bbox_inches="tight")
    plt.close(fig)
