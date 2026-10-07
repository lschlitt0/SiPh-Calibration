from __future__ import annotations

from pathlib import Path
import tempfile
from ._support import CAL

# Root unittest classes bind this function; avoid duplicate pytest collection.
__test__ = False


def test_paper_export_and_manifest_invariants(self) -> None:
    """Check exact table formatting and solver provenance using fixed fixtures."""
    mesh_results = {
        "tunecheck": {
            "method": "tunecheck",
            "k": 1,
            "probe_count": 462,
            "probe_rounds_effective": 462,
            "hw_write_count": 231,
            "mse_final": 1.759e-1,
            "walltime": 3.94,
            "subset_size": 77,
            "rounds_run": 3,
        },
        "global": {
            "method": "global",
            "k": 1,
            "probe_count": 6144,
            "probe_rounds_effective": 6144,
            "hw_write_count": 2,
            "mse_final": 2.300e-2,
            "walltime": 394.26,
            "partition_solver_requested": "heuristic",
            "partition_solver_used": "heuristic",
            "opt_solver_requested": "gn",
            "opt_solver_used": "gn",
        },
        "dfc": {
            "method": "dfc",
            "k": 4,
            "probe_count": 2864,
            "probe_rounds_effective": 1352,
            "hw_write_count": 10,
            "mse_final": 2.062e-4,
            "walltime": 208.35,
            "partition_solver_requested": "heuristic",
            "partition_solver_used": "heuristic",
            "opt_solver_requested": "gn",
            "opt_solver_used": "gn",
        },
    }
    ring_results = {
        "parallel": [
            {
                "method": "parallel",
                "cross_talk_level": 0.0,
                "settle_ms": 111.0,
                "settled_all": True,
                "peak_pm": 1.0,
                "rms_pm": 0.100,
                "probe_count": 40000,
                "probe_rounds_effective": 5000,
                "trace_len": 5000,
                "rings": 8,
                "control_horizon_s": 5.0,
            },
            {
                "method": "parallel",
                "cross_talk_level": 0.06,
                "settle_ms": 2881.0,
                "settled_all": True,
                "peak_pm": 6.96,
                "rms_pm": 0.0146,
                "probe_count": 40000,
                "probe_rounds_effective": 5000,
                "trace_len": 5000,
                "rings": 8,
                "control_horizon_s": 5.0,
            },
        ],
        "scan": {
            "method": "scan",
            "cross_talk_level": 0.06,
            "settle_ms": 5000.0,
            "settled_all": False,
            "peak_pm": 16.0,
            "rms_pm": 8.054,
            "probe_count": 40000,
            "probe_rounds_effective": 5000,
            "trace_len": 5000,
            "rings": 8,
            "control_horizon_s": 5.0,
        },
    }
    cfg = CAL.apply_paper_profile(CAL.CalibrationConfig())

    with tempfile.TemporaryDirectory() as tmpdir:
        run_dir = Path(tmpdir)
        CAL.validate_paper_results(cfg, mesh_results, ring_results)
        mesh_files = CAL.write_paper_mesh_table(run_dir, mesh_results)
        ring_files = CAL.write_paper_ring_table(run_dir, ring_results, preferred_ct=0.06)
        manifest_path = CAL.write_paper_manifest(
            run_dir,
            cfg=cfg,
            mesh_results=mesh_results,
            ring_results=ring_results,
            generated_files=[*mesh_files, *ring_files, run_dir / "paper_manifest.json"],
            timestamp="2026-03-30T00:00:00-06:00",
        )
        CAL.validate_paper_artifacts(
            cfg=cfg,
            ring_results=ring_results,
            ring_table_path=run_dir / "paper_table_ring.tex",
            manifest_path=manifest_path,
        )
        mesh_text = (run_dir / "paper_table_mesh.tex").read_text(encoding="utf-8")
        ring_text = (run_dir / "paper_table_ring.tex").read_text(encoding="utf-8")
        manifest = manifest_path.read_text(encoding="utf-8")

    expected_mesh = (
        "\\begin{tabular}{lrrrrrr}\n"
        "\\toprule\n"
        "Calibration strategy & $k$ & Total probes & Effective probe rounds & HW writes & Final MSE & Time \\\\\n"
        "\\midrule\n"
        "Tune-and-check (coordinate descent) & 1 & 462 & 462 & 231 & $1.76\\times10^{-1}$ & 3.94\\,s \\\\\n"
        "Global surrogate (no partition) & 1 & 6144 & 6144 & 2 & $2.30\\times10^{-2}$ & 394.26\\,s \\\\\n"
        "DfC: partition + surrogates + polish & 4 & 2864 & 1352 & 10 & $2.06\\times10^{-4}$ & 208.35\\,s \\\\\n"
        "\\bottomrule\n"
        "\\end{tabular}\n\n"
        "\\vspace{2pt}\n"
        "\\begin{minipage}{0.98\\columnwidth}\\footnotesize\n"
        "\\emph{Note:} ``Total probes'' counts all measurements across all blocks. ``Effective probe rounds'' is the idealized full-parallel wall-clock proxy. ``Time'' is simulator-side compute+calibration runtime.\n"
        "\\end{minipage}\n"
    )
    expected_ring = (
        "\\begin{tabular}{lrrr}\n"
        "\\toprule\n"
        "Method & Settle time (ms) & Peak error (pm) & RMS error (pm) \\\\\n"
        "\\midrule\n"
        "Parallel dither-locking & 2881 & 6.96 & 0.0146 \\\\\n"
        "Sequential scan-and-retune & $>5000$ & 16.0 & 8.05 \\\\\n"
        "\\bottomrule\n"
        "\\end{tabular}\n"
    )

    self.assertEqual(mesh_text, expected_mesh)
    self.assertEqual(ring_text, expected_ring)
    self.assertIn("partition_solver_requested", manifest)
    self.assertIn("opt_solver_used", manifest)
