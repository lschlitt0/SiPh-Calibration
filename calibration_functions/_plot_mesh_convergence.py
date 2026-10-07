"""_plot_mesh_convergence extracted from the calibration experiment runner."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
import numpy as np

from .log import log


def _plot_mesh_convergence(run_dir: Path, mesh_results: Dict[str, Any], *, plt: Any) -> None:
    method_key = "dfc" if "dfc" in mesh_results else (next(iter(mesh_results.keys()), None))
    if not method_key:
        return
    res = mesh_results.get(method_key)
    if not isinstance(res, dict):
        return
    trace_rows = res.get("mesh_trace_rows", [])
    if not trace_rows:
        log("[plot] mesh trace missing from results", force=True)
        return

    def _int_or(row: Dict[str, Any], key: str, default: int) -> int:
        try:
            return int(float(row.get(key, default)))
        except Exception:
            return default

    def _find_event_row(stage: str, outer_round: Optional[int], *, first: bool) -> Optional[Dict[str, Any]]:
        matches: List[Dict[str, Any]] = []
        for r in trace_rows:
            if str(r.get("stage", "")) != stage:
                continue
            if outer_round is not None and _int_or(r, "outer_round", -999) != outer_round:
                continue
            matches.append(r)
        if not matches:
            return None
        return matches[0] if first else matches[-1]

    def _col(row: Dict[str, Any], key: str) -> float:
        try:
            return float(row.get(key, 0.0))
        except Exception:
            return 0.0

    def _event_x(row: Dict[str, Any], key: str) -> Optional[float]:
        if key not in row:
            return None
        try:
            val = float(row.get(key))
        except Exception:
            return None
        return val if np.isfinite(val) else None

    events = [
        ("R1 end", _find_event_row("outer_apply", 0, first=False), {"color": "#495057", "linestyle": "--"}),
        ("R2 end", _find_event_row("outer_apply", 1, first=False), {"color": "#868e96", "linestyle": "--"}),
        ("Polish start", _find_event_row("polish", None, first=True), {"color": "#f08c00", "linestyle": ":"}),
        ("Polish end", _find_event_row("polish", None, first=False), {"color": "#37b24d", "linestyle": "-."}),
    ]

    probe_counts = [_col(r, "probe_count") for r in trace_rows]
    probe_rounds_eff = [_col(r, "probe_rounds_effective") for r in trace_rows]
    hw_writes = [_col(r, "hw_write_count") for r in trace_rows]
    mse_vals = [max(_col(r, "global_mse"), 1e-12) for r in trace_rows]
    fig, axes = plt.subplots(1, 3, figsize=(12, 4))
    x_sets = (
        (probe_counts, "Probes"),
        (probe_rounds_eff, "Effective probe rounds"),
        (hw_writes, "Setpoint commits (W)"),
    )
    for ax, (x, label) in zip(axes, x_sets):
        ax.semilogy(x, mse_vals, marker="o", linewidth=1.2, markersize=3)
        ax.set_xlabel(label)
        ax.set_ylabel("MSE")
        ax.grid(True, which="both", alpha=0.35)
        for event_label, event_row, style in events:
            if event_row is None:
                continue
            key = "probe_count" if label == "Probes" else "probe_rounds_effective"
            if label == "Setpoint commits (W)":
                key = "hw_write_count"
            x_pos = _event_x(event_row, key)
            if x_pos is None:
                continue
            ax.axvline(x_pos, linewidth=1.0, alpha=0.7, **style)
            ax.text(
                x_pos,
                0.98,
                event_label,
                transform=ax.get_xaxis_transform(),
                rotation=90,
                va="top",
                ha="right",
                fontsize=7,
                color=style["color"],
            )
    fig.suptitle(f"Mesh convergence ({method_key})")
    fig.tight_layout()
    fig.savefig(run_dir / "fig_mesh_convergence.png", bbox_inches="tight")
    plt.close(fig)
