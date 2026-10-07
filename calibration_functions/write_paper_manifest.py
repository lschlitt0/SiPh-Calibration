"""write_paper_manifest extracted from the calibration experiment runner."""

from __future__ import annotations

from datetime import datetime
from datetime import timezone
from pathlib import Path
from typing import Any
from typing import Dict
from typing import Optional
from typing import Sequence

from ._git_commit_hash import _git_commit_hash
from ._write_json import _write_json
from .models import CalibrationConfig
from .pick_ring_result import pick_ring_result
from .settings import PROJECT_ROOT_DIR


def write_paper_manifest(
    output_dir: Path,
    *,
    cfg: CalibrationConfig,
    mesh_results: Dict[str, Any],
    ring_results: Dict[str, Any],
    generated_files: Sequence[Path],
    timestamp: Optional[str] = None,
) -> Path:
    """Write a reproducibility manifest for manuscript-facing outputs."""
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "paper_manifest.json"
    generated_list = [str(Path(p)) for p in generated_files]
    if str(path) not in generated_list:
        generated_list.append(str(path))
    selected_parallel = pick_ring_result(ring_results.get("parallel", []), preferred_ct=float(cfg.ring_cross_talk))
    mesh_solver_meta: Dict[str, Dict[str, Any]] = {}
    for key, res in mesh_results.items():
        if isinstance(res, dict):
            mesh_solver_meta[key] = {
                "partition_solver_requested": res.get("partition_solver_requested", cfg.partition_solver),
                "partition_solver_used": res.get("partition_solver_used", cfg.partition_solver),
                "opt_solver_requested": res.get("opt_solver_requested", cfg.opt_solver),
                "opt_solver_used": res.get("opt_solver_used", cfg.opt_solver),
            }
    manifest = {
        "timestamp": timestamp or datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "seed": int(cfg.seed),
        "locked_config": dict(cfg.__dict__),
        "requested_solvers": {
            "partition": str(cfg.partition_solver),
            "opt": str(cfg.opt_solver),
        },
        "used_solvers": mesh_solver_meta,
        "generated_files": generated_list,
        "git_commit_hash": _git_commit_hash(PROJECT_ROOT_DIR),
        "selected_ring_cross_talk_point": (
            float(selected_parallel.get("cross_talk_value", selected_parallel.get("cross_talk_level", cfg.ring_cross_talk)))
            if isinstance(selected_parallel, dict)
            else float(cfg.ring_cross_talk)
        ),
        "methods_run": {
            "mesh": sorted([str(k) for k in mesh_results.keys()]),
            "ring": sorted([str(k) for k in ring_results.keys()]),
        },
    }
    _write_json(path, manifest)
    return path
