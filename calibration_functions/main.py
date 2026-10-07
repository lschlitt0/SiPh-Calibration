"""main extracted from the calibration experiment runner."""

from __future__ import annotations

from datetime import datetime
from datetime import timezone
from pathlib import Path
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Sequence
from typing import Tuple
import sys
import time

from ._append_ring_trace_rows import _append_ring_trace_rows
from ._mesh_trace_rows_for_xlsx import _mesh_trace_rows_for_xlsx
from ._parse_method_list import _parse_method_list
from ._setup_output_capture import _setup_output_capture
from ._write_xlsx import _write_xlsx
from .apply_paper_profile import apply_paper_profile
from .apply_sweep_overrides import apply_sweep_overrides
from .build_arg_parser import build_arg_parser
from .constants import MESH_ROW_FIELDS
from .constants import MESH_TRACE_SHEET_FIELDS
from .constants import RING_ROW_FIELDS
from .constants import RING_TRACE_BASE_FIELDS
from .constants import RUN_SUMMARY_FIELDS
from .expand_sweep_spec import expand_sweep_spec
from .generate_hypergraph_plots import generate_hypergraph_plots
from .generate_mesh_outer_round_plots import generate_mesh_outer_round_plots
from .generate_mesh_plots import generate_mesh_plots
from .generate_ring_plots import generate_ring_plots
from .log_kv import log_kv
from .log_section import log_section
from .models import CalibrationConfig
from .models import PhysicsParams
from .pick_ring_result import pick_ring_result
from .run_mesh_suite import run_mesh_suite
from .run_ring_suite import run_ring_suite
from .settings import PAPER_DATA_DIR
from .validate_paper_artifacts import validate_paper_artifacts
from .validate_paper_results import validate_paper_results
from .write_mesh_table import write_mesh_table
from .write_paper_manifest import write_paper_manifest
from .write_paper_mesh_table import write_paper_mesh_table
from .write_paper_ring_table import write_paper_ring_table
from .write_ring_table import write_ring_table


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Run CLI-selected experiments/sweeps and export tables, plots, logs, and XLSX.

    Returns zero after export. Optional plotting/workbook dependencies may be
    absent; diagnostics are logged and those artifacts are skipped. The paper
    profile additionally creates JSON/CSV/LaTeX tables and a manifest. Existing
    files with the same output names are overwritten by the export functions.
    """
    args = build_arg_parser().parse_args(argv)
    cfg_base = CalibrationConfig(
        mesh_size=args.mesh_size,
        ring_count=args.rings,
        ring_cross_talk=args.ring_cross_talk,
        ring_cross_talk_sweep=args.ring_cross_talk_sweep or None,
        partitions=args.partitions,
        partition_solver=args.partition_solver,
        kahypar_config=args.kahypar_config,
        balance_eps=args.balance_eps,
        polishing_rounds=args.polishing_rounds,
        outer_rounds=args.outer_rounds,
        opt_solver=args.opt_solver,
        mesh_baselines=args.mesh_baselines,
        ring_baselines=args.ring_baselines,
        tune_check_rounds=args.tune_check_rounds,
        tune_check_subset=args.tune_check_subset,
        tune_check_step=args.tune_check_step,
        tune_check_lr=args.tune_check_lr,
        drift_K=args.drift_K,
        seed=args.seed,
        sweep=args.sweep or None,
        results_dir=args.results_dir,
    )
    if args.paper_profile:
        cfg_base = apply_paper_profile(cfg_base)
    phys = PhysicsParams()
    mesh_methods = _parse_method_list(cfg_base.mesh_baselines, ("dfc", "global", "tunecheck"))
    ring_methods = _parse_method_list(cfg_base.ring_baselines, ("parallel", "scan"))
    sweep_specs = expand_sweep_spec(cfg_base.sweep)
    cfg_list = [cfg_base] if not sweep_specs else [apply_sweep_overrides(cfg_base, spec) for spec in sweep_specs]

    base_results_dir = cfg_base.results_dir.resolve()
    base_results_dir.mkdir(parents=True, exist_ok=True)
    log_fh, stdout_orig, stderr_orig = _setup_output_capture(base_results_dir / "terminal_output.txt")
    mesh_runs_for_plot: List[Dict[str, Any]] = []
    mesh_rows_all: List[Dict[str, Any]] = []
    ring_rows_all: List[Dict[str, Any]] = []
    run_rows_all: List[Dict[str, Any]] = []
    mesh_trace_rows_all: List[Dict[str, Any]] = []
    ring_trace_rows_by_sheet: Dict[str, List[Dict[str, Any]]] = {}
    max_ring_count = 0

    try:
        for idx_cfg, cfg in enumerate(cfg_list):
            run_start = time.perf_counter()
            dt_run = datetime.now(timezone.utc).astimezone()
            timestamp = dt_run.isoformat(timespec="seconds")
            meta = {"timestamp": timestamp, "seed": int(cfg.seed)}
            if len(cfg_list) > 1:
                run_dir = base_results_dir / f"run_{idx_cfg:03d}_N{cfg.mesh_size}_k{cfg.partitions}_seed{cfg.seed}"
            else:
                run_dir = base_results_dir
            run_dir.mkdir(parents=True, exist_ok=True)

            mesh_results: Dict[str, Any] = {}
            ring_results: Dict[str, Any] = {}
            mesh_rows: List[Dict[str, Any]] = []
            ring_rows: List[Dict[str, Any]] = []

            if not args.no_mesh:
                mesh_results, mesh_rows = run_mesh_suite(cfg, phys, mesh_methods, meta)
                if mesh_rows:
                    mesh_rows_all.extend(mesh_rows)
                if mesh_results:
                    mesh_runs_for_plot.append({"N": cfg.mesh_size, "mesh_results": mesh_results})
                    mesh_trace_rows_all.extend(_mesh_trace_rows_for_xlsx(mesh_results, cfg, meta))

            if not args.no_rings:
                ring_results, ring_rows = run_ring_suite(cfg, phys, ring_methods, meta)
                if ring_rows:
                    ring_rows_all.extend(ring_rows)
                for res_list in ring_results.values():
                    if isinstance(res_list, list):
                        candidates = res_list
                    elif isinstance(res_list, dict):
                        candidates = [res_list]
                    else:
                        candidates = []
                    for res in candidates:
                        if not isinstance(res, dict):
                            continue
                        trace = res.get("trace", {})
                        max_ring_count = max(
                            max_ring_count,
                            _append_ring_trace_rows(ring_trace_rows_by_sheet, res, meta, trace, case="primary"),
                        )
                        baseline_trace = res.get("baseline_trace", {})
                        if isinstance(baseline_trace, dict) and baseline_trace:
                            max_ring_count = max(
                                max_ring_count,
                                _append_ring_trace_rows(
                                    ring_trace_rows_by_sheet, res, meta, baseline_trace, case="baseline"
                                ),
                            )

            run_walltime_s = float(time.perf_counter() - run_start)
            mesh_primary = mesh_results.get("dfc") or (next(iter(mesh_results.values())) if mesh_results else None)
            ring_primary_candidates = ring_results.get("parallel") or (
                next(iter(ring_results.values())) if ring_results else None
            )
            if isinstance(ring_primary_candidates, list):
                ring_primary = pick_ring_result(ring_primary_candidates, preferred_ct=float(cfg.ring_cross_talk))
            elif ring_primary_candidates is None:
                ring_primary = None
            else:
                ring_primary = ring_primary_candidates

            def _eff(result_obj: Optional[Dict[str, Any]], key: str) -> Any:
                if not result_obj:
                    return ""
                if key in result_obj:
                    return result_obj.get(key, "")
                effort_obj = result_obj.get("effort", {}) if isinstance(result_obj, dict) else {}
                return effort_obj.get(key, "")

            run_row: Dict[str, Any] = {
                "timestamp": timestamp,
                "seed": int(cfg.seed),
                "run_walltime_s": run_walltime_s,
                "mesh_method": mesh_primary.get("method") if mesh_primary else "",
                "mesh_mse_final": mesh_primary.get("mse_final") if mesh_primary else "",
                "mesh_probe_count": _eff(mesh_primary, "probe_count"),
                "mesh_probe_rounds_effective": _eff(mesh_primary, "probe_rounds_effective"),
                "mesh_hw_write_count": _eff(mesh_primary, "hw_write_count"),
                "mesh_solver_iter_count": _eff(mesh_primary, "solver_iter_count"),
                "mesh_walltime_s": mesh_primary.get("walltime", mesh_primary.get("walltime_s", "")) if mesh_primary else "",
                "rings_method": ring_primary.get("method") if ring_primary else "",
                "rings_settle_ms": ring_primary.get("settle_ms") if ring_primary else "",
                "rings_peak_pm": ring_primary.get("peak_pm") if ring_primary else "",
                "rings_rms_pm": ring_primary.get("rms_pm") if ring_primary else "",
                "rings_probe_count": _eff(ring_primary, "probe_count"),
                "rings_probe_rounds_effective": _eff(ring_primary, "probe_rounds_effective"),
                "rings_hw_write_count": _eff(ring_primary, "hw_write_count"),
                "rings_solver_iter_count": _eff(ring_primary, "solver_iter_count"),
                "rings_walltime_s": ring_primary.get("walltime", ring_primary.get("walltime_s", "")) if ring_primary else "",
            }
            run_rows_all.append(run_row)

            generate_hypergraph_plots(
                run_dir,
                cfg,
                include_mesh=not args.no_mesh,
                include_rings=not args.no_rings,
            )
            generate_mesh_plots(run_dir, mesh_results)
            generate_ring_plots(run_dir, ring_results)
            write_mesh_table(run_dir, mesh_results)
            write_ring_table(run_dir, ring_results, preferred_ct=float(cfg.ring_cross_talk))

            if args.paper_profile:
                validate_paper_results(cfg, mesh_results, ring_results)
                generated_files: List[Path] = []
                generated_files.extend(write_paper_mesh_table(run_dir, mesh_results))
                generated_files.extend(write_paper_ring_table(run_dir, ring_results, preferred_ct=float(cfg.ring_cross_talk)))
                manifest_path = write_paper_manifest(
                    run_dir,
                    cfg=cfg,
                    mesh_results=mesh_results,
                    ring_results=ring_results,
                    generated_files=generated_files,
                    timestamp=timestamp,
                )
                generated_files.append(manifest_path)
                validate_paper_artifacts(
                    cfg=cfg,
                    ring_results=ring_results,
                    ring_table_path=run_dir / "paper_table_ring.tex",
                    manifest_path=manifest_path,
                )
                if PAPER_DATA_DIR != run_dir:
                    write_paper_mesh_table(PAPER_DATA_DIR, mesh_results)
                    write_paper_ring_table(PAPER_DATA_DIR, ring_results, preferred_ct=float(cfg.ring_cross_talk))
                    write_paper_manifest(
                        PAPER_DATA_DIR,
                        cfg=cfg,
                        mesh_results=mesh_results,
                        ring_results=ring_results,
                        generated_files=[
                            PAPER_DATA_DIR / "paper_table_mesh.tex",
                            PAPER_DATA_DIR / "paper_table_mesh.csv",
                            PAPER_DATA_DIR / "paper_table_mesh.json",
                            PAPER_DATA_DIR / "paper_table_ring.tex",
                            PAPER_DATA_DIR / "paper_table_ring.csv",
                            PAPER_DATA_DIR / "paper_table_ring.json",
                        ],
                        timestamp=timestamp,
                    )

            log_section("Run complete")
            log_kv("Saved to", run_dir)

        if mesh_runs_for_plot:
            generate_mesh_outer_round_plots(base_results_dir, mesh_runs_for_plot)

        sheets: Dict[str, Tuple[Sequence[str], Sequence[Dict[str, Any]]]] = {}
        if run_rows_all:
            sheets["run_summary"] = (RUN_SUMMARY_FIELDS, run_rows_all)
        if mesh_rows_all:
            sheets["mesh_results"] = (MESH_ROW_FIELDS, mesh_rows_all)
        if ring_rows_all:
            sheets["ring_results"] = (RING_ROW_FIELDS, ring_rows_all)
        if mesh_trace_rows_all:
            sheets["mesh_trace"] = (MESH_TRACE_SHEET_FIELDS, mesh_trace_rows_all)

        ring_cols = [f"ring_{i}" for i in range(max_ring_count)]
        ring_trace_fields = list(RING_TRACE_BASE_FIELDS) + ring_cols
        for sheet_name, rows in ring_trace_rows_by_sheet.items():
            if rows:
                sheets[sheet_name] = (ring_trace_fields, rows)

        if sheets:
            xlsx_path = base_results_dir / "results.xlsx"
            _write_xlsx(xlsx_path, sheets)
            log_kv("Workbook", xlsx_path)

        log_kv("Terminal log", base_results_dir / "terminal_output.txt")
        log_section("Done")
        log_kv("Saved to", base_results_dir)
    finally:
        sys.stdout = stdout_orig
        sys.stderr = stderr_orig
        if log_fh is not None:
            log_fh.flush()
            log_fh.close()
    return 0
