"""_plot_hypergraph extracted from the calibration experiment runner."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from typing import Optional
from typing import Set
import math
import numpy as np

from ._partition_palette import _partition_palette
from .log import log
from .models import Hypergraph


def _plot_hypergraph(
    hg: Hypergraph,
    part: np.ndarray,
    positions: np.ndarray,
    path: Path,
    title: str,
    *,
    plt: Any,
    boundary: Optional[Set[int]] = None,
) -> None:
    part = np.asarray(part, dtype=int)
    if part.shape != (hg.n_vertices,):
        log(f"[plot] hypergraph part size mismatch for {path}", force=True)
        return
    pos = np.asarray(positions, dtype=float)
    if pos.shape != (hg.n_vertices, 2):
        log(f"[plot] hypergraph positions size mismatch for {path}", force=True)
        return

    boundary_set = set(boundary) if boundary is not None else hg.boundary_vertices(part)
    cut_edges = set(hg.cut_hyperedges(part))
    max_weight = max((float(e.weight) for e in hg.edges), default=1.0)
    max_weight = max(1e-9, float(max_weight))

    x_span = float(np.max(pos[:, 0]) - np.min(pos[:, 0])) if pos.size else 1.0
    y_span = float(np.max(pos[:, 1]) - np.min(pos[:, 1])) if pos.size else 1.0
    span = max(x_span, y_span)
    fig_size = max(4.5, min(12.0, 0.45 * span + 4.0))
    fig, ax = plt.subplots(figsize=(fig_size, fig_size))

    for ei, e in enumerate(hg.edges):
        pins = [int(v) for v in e.pins]
        if len(pins) < 2:
            continue
        weight_norm = float(e.weight) / max_weight
        is_cut = ei in cut_edges
        edge_color = "#f08c00" if is_cut else "#adb5bd"
        alpha_base = 0.15 + 0.45 * weight_norm
        alpha = min(0.85, alpha_base + (0.25 if is_cut else 0.0))
        lw = 0.4 + 1.6 * weight_norm
        if len(pins) == 2:
            pts = pos[pins]
            ax.plot(pts[:, 0], pts[:, 1], color=edge_color, alpha=alpha, linewidth=lw, zorder=1)
        else:
            centroid = np.mean(pos[pins], axis=0)
            for v in pins:
                p = pos[int(v)]
                ax.plot(
                    [centroid[0], p[0]],
                    [centroid[1], p[1]],
                    color=edge_color,
                    alpha=alpha,
                    linewidth=lw,
                    zorder=1,
                )

    palette = _partition_palette(plt)
    node_colors = [palette[int(part[v]) % len(palette)] for v in range(hg.n_vertices)]
    node_size = max(12.0, min(120.0, 900.0 / math.sqrt(max(1, hg.n_vertices))))
    ax.scatter(
        pos[:, 0],
        pos[:, 1],
        s=node_size,
        c=node_colors,
        edgecolors="#212529",
        linewidths=0.6,
        zorder=3,
    )

    if boundary_set:
        b_idx = np.array(sorted(boundary_set), dtype=int)
        ax.scatter(
            pos[b_idx, 0],
            pos[b_idx, 1],
            s=node_size * 1.7,
            facecolors="none",
            edgecolors="#212529",
            linewidths=1.1,
            zorder=4,
        )

    ax.set_aspect("equal")
    ax.set_axis_off()
    fig.suptitle(title)
    fig.savefig(path, bbox_inches="tight", dpi=200)
    plt.close(fig)
