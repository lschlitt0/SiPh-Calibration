"""run_mesh_suite extracted from the calibration experiment runner."""

from __future__ import annotations

from typing import Any
from typing import Dict
from typing import List
from typing import Sequence
from typing import Tuple

from ._mesh_row_from_result import _mesh_row_from_result
from .models import CalibrationConfig
from .models import PhysicsParams
from .run_dfc_mesh import run_dfc_mesh
from .run_mesh_global_surrogate import run_mesh_global_surrogate
from .run_mesh_tune_and_check import run_mesh_tune_and_check


def run_mesh_suite(
    cfg: CalibrationConfig, phys: PhysicsParams, methods: Sequence[str], meta: Dict[str, Any]
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """Run selected mesh methods and return method results plus flat summary rows."""
    mesh_results: Dict[str, Any] = {}
    mesh_rows: List[Dict[str, Any]] = []
    for method in methods:
        if method == "dfc":
            res = run_dfc_mesh(cfg, phys, out_dir=None, method_label="dfc")
        elif method == "global":
            res = run_mesh_global_surrogate(cfg, phys, out_dir=None)
        elif method == "tunecheck":
            res = run_mesh_tune_and_check(
                cfg,
                phys,
                out_dir=None,
                subset_frac=cfg.tune_check_subset,
                rounds=cfg.tune_check_rounds,
                step_size=cfg.tune_check_step,
                lr=cfg.tune_check_lr,
            )
        else:
            continue
        mesh_results[method] = res
        mesh_rows.append(_mesh_row_from_result(res, cfg, meta))
    return mesh_results, mesh_rows
