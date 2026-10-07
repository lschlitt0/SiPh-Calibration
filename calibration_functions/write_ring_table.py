"""write_ring_table extracted from the calibration experiment runner."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from typing import Dict
from typing import List
from typing import Tuple

from .pick_ring_result import pick_ring_result


def write_ring_table(run_dir: Path, ring_results: Dict[str, Any], *, preferred_ct: float = 0.06) -> None:
    if not ring_results:
        return
    order = ("parallel", "scan")
    rows: List[Tuple[str, str, float, float, Any]] = []
    for key in order:
        res_list = ring_results.get(key)
        res = pick_ring_result(res_list, preferred_ct=preferred_ct) if isinstance(res_list, list) else res_list
        if not isinstance(res, dict):
            continue
        effort = res.get("effort", {})
        if not bool(res.get("settled_all", True)):
            horizon_ms = int(round(1000.0 * float(res.get("control_horizon_s", 0.0))))
            settle_repr = f">{horizon_ms}"
        else:
            settle_repr = f"{float(res.get('settle_ms', 0.0)):.2f}"
        rows.append(
            (
                key,
                settle_repr,
                float(res.get("peak_pm", 0.0)),
                float(res.get("rms_pm", 0.0)),
                res.get("probe_count", effort.get("probe_count", "")),
            )
        )
    if not rows:
        return
    path = run_dir / "table_ring.tex"
    with path.open("w", encoding="utf-8") as fh:
        fh.write("\\begin{tabular}{lrrrr}\\hline\n")
        fh.write("Method & Settle (ms) & Peak (pm) & RMS (pm) & Probes \\\\\n\\hline\n")
        for method, settle_repr, peak_pm, rms_pm, probes in rows:
            fh.write(f"{method} & {settle_repr} & {peak_pm:.2f} & {rms_pm:.3f} & {probes} \\\\\n")
        fh.write("\\hline\\end{tabular}\n")
