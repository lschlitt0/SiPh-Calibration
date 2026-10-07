"""generate_ring_plots extracted from the calibration experiment runner."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from typing import Dict
import numpy as np

from .log import log
from .pick_ring_result import pick_ring_result


def generate_ring_plots(run_dir: Path, ring_results: Dict[str, Any]) -> None:
    """Plot a selected ring run with filtered trace and aggregate metrics.

    Selection defaults to cross-talk nearest 0.06. The trace peak annotation is
    filtered, while the aggregate peak metric is raw. The plotted settling marker
    also uses the horizon-valued sentinel when the run did not settle.
    """
    if not ring_results:
        return
    method_key = "parallel" if "parallel" in ring_results else (next(iter(ring_results.keys()), None))
    res_candidate = ring_results.get(method_key) if method_key else None
    if isinstance(res_candidate, list):
        res = pick_ring_result(res_candidate)
    else:
        res = res_candidate
    if not isinstance(res, dict):
        return
    ct_val = res.get("cross_talk_value", res.get("cross_talk_level", None))
    trace = res.get("trace", {})
    if not isinstance(trace, dict) or not trace:
        log("[plot] ring trace missing from results", force=True)
        return
    try:
        import matplotlib.pyplot as plt
    except Exception as exc:  # pragma: no cover - plotting optional
        log(f"[plot] skipping ring plots (matplotlib unavailable: {exc})", force=True)
        return

    t_ms = trace.get("t_ms")
    det_lp = trace.get("detuning_lp_pm")
    if det_lp is None or (isinstance(det_lp, np.ndarray) and det_lp.size == 0):
        det_lp = trace.get("detuning_pm")
    lock_threshold_pm = res.get("lock_threshold_pm", None)
    if t_ms is None or det_lp is None:
        log("[plot] ring trace missing expected arrays", force=True)
        return

    t_ms = np.asarray(t_ms, dtype=float)
    worst_idx = int(res.get("worst_ring_id", 0))
    det_arr = np.asarray(det_lp, dtype=float)
    if det_arr.ndim != 2 or det_arr.shape[0] != t_ms.size:
        log("[plot] ring trace shape mismatch; skipping ring plot", force=True)
        return
    if worst_idx < 0 or worst_idx >= det_arr.shape[1]:
        worst_idx = 0

    det_series = det_arr[:, worst_idx]
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    axes[0].plot(t_ms, det_series, linewidth=1.4)
    try:
        lock_threshold_pm = float(lock_threshold_pm) if lock_threshold_pm is not None else None
    except Exception:
        lock_threshold_pm = None
    if lock_threshold_pm is not None and np.isfinite(lock_threshold_pm) and lock_threshold_pm > 0.0:
        axes[0].axhline(lock_threshold_pm, linestyle="--", color="#adb5bd", linewidth=1.0, alpha=0.8)
        axes[0].axhline(-lock_threshold_pm, linestyle="--", color="#adb5bd", linewidth=1.0, alpha=0.8)
    axes[0].set_xlabel("time (ms)")
    axes[0].set_ylabel("detuning (pm)")
    axes[0].set_title(f"Worst ring {worst_idx}")
    axes[0].grid(True, alpha=0.35)

    settle_ms = float(res.get("settle_ms", 0.0))
    if np.isfinite(settle_ms) and t_ms.size:
        settle_x = float(np.clip(settle_ms, float(t_ms[0]), float(t_ms[-1])))
        axes[0].axvline(settle_x, linestyle=":", color="#495057", linewidth=1.0, alpha=0.8)
        ymin, ymax = axes[0].get_ylim()
        y_text = ymax - 0.08 * (ymax - ymin)
        x_span = float(t_ms[-1] - t_ms[0])
        x_text = min(settle_x + 0.02 * x_span, float(t_ms[-1]))
        axes[0].annotate(
            f"settle {settle_ms:.2f} ms",
            xy=(settle_x, y_text),
            xytext=(x_text, y_text),
            textcoords="data",
            fontsize=8,
            color="#495057",
        )

    if det_series.size and t_ms.size:
        peak_idx = int(np.argmax(np.abs(det_series)))
        peak_val = float(det_series[peak_idx])
        peak_t = float(t_ms[peak_idx])
        y_span = float(np.max(det_series) - np.min(det_series))
        y_offset = 0.1 * y_span if y_span > 0.0 else 0.1
        y_text = peak_val + (y_offset if peak_val >= 0.0 else -y_offset)
        axes[0].scatter([peak_t], [peak_val], color="#e03131", s=20, zorder=5)
        axes[0].annotate(
            f"peak {abs(peak_val):.2f} pm",
            xy=(peak_t, peak_val),
            xytext=(peak_t, y_text),
            textcoords="data",
            fontsize=8,
            color="#e03131",
        )

    metrics_labels = ["Peak (pm)", "RMS (pm)", "Settle (ms)"]
    metrics_values = [
        float(res.get("peak_pm", 0.0)),
        float(res.get("rms_pm", 0.0)),
        float(res.get("settle_ms", 0.0)),
    ]
    bars = axes[1].bar(np.arange(len(metrics_values)), metrics_values, color=["#4c6ef5", "#37b24d", "#f08c00"])
    axes[1].set_xticks(np.arange(len(metrics_values)), metrics_labels)
    axes[1].set_ylabel("value")
    axes[1].set_title(f"Cross-talk={ct_val:.2f}" if ct_val is not None else "Aggregate metrics")
    axes[1].grid(True, axis="y", alpha=0.35)
    for bar, val in zip(bars, metrics_values):
        axes[1].text(bar.get_x() + bar.get_width() / 2.0, val, f"{val:.2f}", ha="center", va="bottom", fontsize=8)

    fig.tight_layout()
    fig.savefig(run_dir / "fig_ring_response.png", bbox_inches="tight")
    plt.close(fig)
