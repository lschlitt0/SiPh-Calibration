"""write_paper_mesh_table extracted from the calibration experiment runner."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from typing import Dict
from typing import List

from ._format_paper_time_s import _format_paper_time_s
from ._format_sci_tex import _format_sci_tex
from ._paper_mesh_rows import _paper_mesh_rows
from ._write_csv import _write_csv
from ._write_json import _write_json
from .constants import PAPER_MESH_TABLE_FIELDS


def write_paper_mesh_table(output_dir: Path, mesh_results: Dict[str, Any]) -> List[Path]:
    """Write manuscript-facing mesh table exports (.tex/.csv/.json)."""
    rows = _paper_mesh_rows(mesh_results)
    if not rows:
        return []
    output_dir.mkdir(parents=True, exist_ok=True)
    tex_path = output_dir / "paper_table_mesh.tex"
    csv_path = output_dir / "paper_table_mesh.csv"
    json_path = output_dir / "paper_table_mesh.json"

    with tex_path.open("w", encoding="utf-8") as fh:
        fh.write("\\begin{tabular}{lrrrrrr}\n")
        fh.write("\\toprule\n")
        fh.write("Calibration strategy & $k$ & Total probes & Effective probe rounds & HW writes & Final MSE & Time \\\\\n")
        fh.write("\\midrule\n")
        for row in rows:
            fh.write(
                f"{row['Calibration strategy']} & {int(row['k'])} & {int(row['Total probes'])} & "
                f"{int(row['Effective probe rounds'])} & {int(row['HW writes'])} & "
                f"{_format_sci_tex(row['Final MSE'])} & {_format_paper_time_s(row['Time'])} \\\\\n"
            )
        fh.write("\\bottomrule\n")
        fh.write("\\end{tabular}\n\n")
        fh.write("\\vspace{2pt}\n")
        fh.write("\\begin{minipage}{0.98\\columnwidth}\\footnotesize\n")
        fh.write(
            "\\emph{Note:} ``Total probes'' counts all measurements across all blocks. "
            "``Effective probe rounds'' is the idealized full-parallel wall-clock proxy. "
            "``Time'' is simulator-side compute+calibration runtime.\n"
        )
        fh.write("\\end{minipage}\n")

    csv_rows = [{key: row[key] for key in PAPER_MESH_TABLE_FIELDS} for row in rows]
    json_payload = {"schema": list(PAPER_MESH_TABLE_FIELDS), "rows": csv_rows}
    _write_csv(csv_path, PAPER_MESH_TABLE_FIELDS, csv_rows)
    _write_json(json_path, json_payload)
    return [tex_path, csv_path, json_path]
