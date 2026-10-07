"""generate_mesh_outer_round_plots extracted from the calibration experiment runner."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from typing import Dict
from typing import List
from typing import Sequence
import math
import numpy as np

from ._extract_mesh_round_series import _extract_mesh_round_series
from ._mean_series import _mean_series
from .log import log


def generate_mesh_outer_round_plots(base_results_dir: Path, mesh_runs: Sequence[Dict[str, Any]]) -> None:
    """Plot per-method MSE histories, grouping and averaging runs by mesh size.

    Other swept settings are not grouping keys, and later rounds can average a
    smaller subset after early stopping. DfC/global histories stop before polish.
    """
    if not mesh_runs:
        return
    try:
        import matplotlib.pyplot as plt
    except Exception as exc:  # pragma: no cover - plotting optional
        log(f"[plot] skipping mesh outer-round plots (matplotlib unavailable: {exc})", force=True)
        return

    by_n: Dict[int, Dict[str, List[List[float]]]] = {}
    meta_by_n: Dict[int, Dict[str, Dict[str, Any]]] = {}
    for entry in mesh_runs:
        if not isinstance(entry, dict):
            continue
        n_val = entry.get("N", None)
        if n_val is None:
            continue
        try:
            n_key = int(n_val)
        except Exception:
            continue
        res_map = entry.get("mesh_results", {})
        if not isinstance(res_map, dict):
            continue
        for method in ("dfc", "global", "tunecheck"):
            res = res_map.get(method)
            if not isinstance(res, dict):
                continue
            series = _extract_mesh_round_series(res, method)
            if not series:
                continue
            by_n.setdefault(n_key, {}).setdefault(method, []).append(series)
            meta_by_n.setdefault(n_key, {}).setdefault(method, res)

    if not by_n:
        return

    n_values = sorted(by_n.keys())
    ncols = min(3, len(n_values))
    nrows = int(math.ceil(len(n_values) / ncols))
    fig, axes = plt.subplots(nrows, ncols, figsize=(4.4 * ncols, 3.6 * nrows), sharey=True, squeeze=False)

    def _label_for(method: str, res: Dict[str, Any]) -> str:
        if method == "dfc":
            k_val = res.get("k", None)
            try:
                return f"DfC (k={int(k_val)})" if k_val is not None else "DfC"
            except Exception:
                return "DfC"
        if method == "global":
            k_val = res.get("k", 1)
            try:
                return f"Global surrogate (k={int(k_val)})"
            except Exception:
                return "Global surrogate"
        return "Tune-and-check"

    label_map: Dict[str, str] = {}
    for method in ("dfc", "global", "tunecheck"):
        for n_key in n_values:
            res_meta = meta_by_n.get(n_key, {}).get(method)
            if res_meta is not None and method not in label_map:
                label_map[method] = _label_for(method, res_meta)
    styles = {
        "dfc": {"color": "#1f77b4", "marker": "o"},
        "global": {"color": "#ff7f0e", "marker": "s"},
        "tunecheck": {"color": "#2ca02c", "marker": "D"},
    }

    for idx, n_key in enumerate(n_values):
        ax = axes[idx // ncols][idx % ncols]
        methods_here = by_n.get(n_key, {})
        max_round = 0
        for method in ("dfc", "global", "tunecheck"):
            series_list = methods_here.get(method, [])
            if not series_list:
                continue
            series = _mean_series(series_list) if len(series_list) > 1 else list(series_list[0])
            if not series:
                continue
            max_round = max(max_round, len(series) - 1)
            x_vals = np.arange(len(series), dtype=int)
            y_vals = [max(float(v), 1e-12) for v in series]
            style = styles.get(method, {})
            label = label_map.get(method, method)
            ax.semilogy(x_vals, y_vals, label=label, linewidth=1.3, markersize=4, **style)
        ax.set_title(f"N={n_key}")
        ax.set_xlabel("outer round")
        if (idx % ncols) == 0:
            ax.set_ylabel("MSE")
        if max_round >= 0:
            ax.set_xticks(np.arange(max_round + 1, dtype=int))
        ax.grid(True, which="both", alpha=0.35)

    for idx in range(len(n_values), nrows * ncols):
        axes[idx // ncols][idx % ncols].axis("off")

    handles: List[Any] = []
    labels: List[str] = []
    for ax in axes.flat:
        h, l = ax.get_legend_handles_labels()
        for hh, ll in zip(h, l):
            if ll not in labels:
                labels.append(ll)
                handles.append(hh)
    if len(n_values) == 1:
        fig.suptitle(f"MSE vs outer round (N={n_values[0]})")
    else:
        fig.suptitle("MSE vs outer round across mesh sizes")
    if handles:
        fig.legend(
            handles,
            labels,
            loc="upper center",
            bbox_to_anchor=(0.5, 0.92),
            ncol=min(3, len(labels)),
        )
        fig.subplots_adjust(top=0.78)
    else:
        fig.subplots_adjust(top=0.88)
    fig.savefig(base_results_dir / "fig_mesh_outer_rounds.png", bbox_inches="tight")
    plt.close(fig)
