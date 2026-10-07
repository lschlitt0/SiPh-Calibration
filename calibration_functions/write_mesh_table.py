"""write_mesh_table extracted from the calibration experiment runner."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from typing import Dict
from typing import List
from typing import Tuple


def write_mesh_table(run_dir: Path, mesh_results: Dict[str, Any]) -> None:
    if not mesh_results:
        return
    order = ("dfc", "global", "tunecheck")
    rows: List[Tuple[str, float, Any, Any, Any]] = []
    for key in order:
        res = mesh_results.get(key)
        if not res:
            continue
        effort = res.get("effort", {})
        rows.append(
            (
                key,
                float(res.get("mse_final", 0.0)),
                res.get("probe_count", effort.get("probe_count", "")),
                res.get("probe_rounds_effective", effort.get("probe_rounds_effective", "")),
                res.get("hw_write_count", effort.get("hw_write_count", "")),
            )
        )
    if not rows:
        return
    path = run_dir / "table_mesh.tex"
    with path.open("w", encoding="utf-8") as fh:
        fh.write("\\begin{tabular}{lrrrr}\\hline\n")
        fh.write("Method & MSE$_{\\text{final}}$ & Probes & Eff. rounds & HW writes \\\\\n\\hline\n")
        for method, mse_final, probes, eff_rounds, hw_writes in rows:
            fh.write(f"{method} & {mse_final:.3e} & {probes} & {eff_rounds} & {hw_writes} \\\\\n")
        fh.write("\\hline\\end{tabular}\n")
