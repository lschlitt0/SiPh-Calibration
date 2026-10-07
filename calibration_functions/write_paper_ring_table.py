"""write_paper_ring_table extracted from the calibration experiment runner."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from typing import Dict
from typing import List

from ._format_paper_peak_pm import _format_paper_peak_pm
from ._format_paper_rms_pm import _format_paper_rms_pm
from ._format_paper_settle_ms import _format_paper_settle_ms
from ._paper_ring_rows import _paper_ring_rows
from ._write_csv import _write_csv
from ._write_json import _write_json
from .constants import PAPER_RING_TABLE_FIELDS


def write_paper_ring_table(output_dir: Path, ring_results: Dict[str, Any], *, preferred_ct: float = 0.06) -> List[Path]:
    """Write manuscript-facing ring table exports (.tex/.csv/.json)."""
    rows = _paper_ring_rows(ring_results, preferred_ct=preferred_ct)
    if not rows:
        return []
    output_dir.mkdir(parents=True, exist_ok=True)
    tex_path = output_dir / "paper_table_ring.tex"
    csv_path = output_dir / "paper_table_ring.csv"
    json_path = output_dir / "paper_table_ring.json"

    with tex_path.open("w", encoding="utf-8") as fh:
        fh.write("\\begin{tabular}{lrrr}\n")
        fh.write("\\toprule\n")
        fh.write("Method & Settle time (ms) & Peak error (pm) & RMS error (pm) \\\\\n")
        fh.write("\\midrule\n")
        for row in rows:
            fh.write(
                f"{row['Method']} & {_format_paper_settle_ms(row)} & "
                f"{_format_paper_peak_pm(row['Peak error (pm)'])} & {_format_paper_rms_pm(row['RMS error (pm)'])} \\\\\n"
            )
        fh.write("\\bottomrule\n")
        fh.write("\\end{tabular}\n")

    csv_rows = []
    for row in rows:
        csv_rows.append(
            {
                "Method": row["Method"],
                "Settle time (ms)": _format_paper_settle_ms(row),
                "Peak error (pm)": _format_paper_peak_pm(row["Peak error (pm)"]),
                "RMS error (pm)": _format_paper_rms_pm(row["RMS error (pm)"]),
            }
        )
    json_payload = {
        "schema": list(PAPER_RING_TABLE_FIELDS),
        "preferred_cross_talk": float(preferred_ct),
        "rows": csv_rows,
    }
    _write_csv(csv_path, PAPER_RING_TABLE_FIELDS, csv_rows)
    _write_json(json_path, json_payload)
    return [tex_path, csv_path, json_path]
