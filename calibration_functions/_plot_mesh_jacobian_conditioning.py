"""_plot_mesh_jacobian_conditioning extracted from the calibration experiment runner."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple
import numpy as np
import textwrap


def _plot_mesh_jacobian_conditioning(run_dir: Path, mesh_results: Dict[str, Any], *, plt: Any) -> None:
    dfc_res = mesh_results.get("dfc")
    if not isinstance(dfc_res, dict):
        return
    blocks = dfc_res.get("blocks", [])
    if not isinstance(blocks, list) or not blocks:
        return
    max_outer = max(int(b.get("outer_round", 0)) for b in blocks if isinstance(b, dict))
    boundary_threshold = 0.3
    internal_pts: List[Tuple[int, float]] = []
    boundary_pts: List[Tuple[int, float]] = []
    cond_threshold: Optional[float] = None
    for b in blocks:
        if not isinstance(b, dict):
            continue
        if int(b.get("outer_round", 0)) != max_outer:
            continue
        try:
            size = int(b.get("n_vertices", 0))
            cond = float(b.get("jacobian_cond", 0.0))
            b_frac = float(b.get("boundary_frac", 0.0))
        except Exception:
            continue
        if cond_threshold is None:
            try:
                thresh_val = float(b.get("cond_threshold", 0.0))
            except Exception:
                thresh_val = 0.0
            if thresh_val > 0.0:
                cond_threshold = thresh_val
        if size <= 0 or cond <= 0.0 or not np.isfinite(cond):
            continue
        if b_frac >= boundary_threshold:
            boundary_pts.append((size, cond))
        else:
            internal_pts.append((size, cond))

    if not internal_pts and not boundary_pts:
        return

    fig, ax = plt.subplots(figsize=(6.0, 4.0))
    if internal_pts:
        x_int, y_int = zip(*internal_pts)
        ax.scatter(x_int, y_int, s=45, color="#4c6ef5", label="Internal blocks")
    if boundary_pts:
        x_b, y_b = zip(*boundary_pts)
        ax.scatter(
            x_b,
            y_b,
            s=55,
            color="#f08c00",
            marker="^",
            label=f"Boundary-heavy (>= {boundary_threshold:.0%})",
        )
    if cond_threshold is None:
        cond_threshold = 1e6
    ax.axhline(
        float(cond_threshold),
        linestyle="--",
        color="#e03131",
        linewidth=1.0,
        alpha=0.8,
        label="conditioning threshold",
    )
    ax.set_xlabel("Block size (tuners)")
    ax.set_ylabel("Jacobian condition number")
    ax.set_yscale("log")
    ax.grid(True, which="both", alpha=0.35)
    subtitle = (
        "High kappa(J) flags under-observed/over-coupled blocks and motivates added sensing or repartitioning."
    )
    ax.set_title(f"Jacobian conditioning vs block size\n{textwrap.fill(subtitle, width=70)}")
    ax.legend()
    fig.tight_layout()
    fig.savefig(run_dir / "fig_mesh_jacobian_conditioning.png", bbox_inches="tight")
    plt.close(fig)
