"""run_mesh_global_surrogate extracted from the calibration experiment runner."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Any
from typing import Dict
from typing import Optional

from .models import CalibrationConfig
from .models import PhysicsParams
from .run_dfc_mesh import run_dfc_mesh


def run_mesh_global_surrogate(cfg: CalibrationConfig, phys: PhysicsParams, *, out_dir: Optional[Path] = None) -> Dict[str, Any]:
    """Run the same mesh surrogate workflow with one block and no boundary polish."""
    cfg_global = replace(cfg, partitions=1, polishing_rounds=0)
    return run_dfc_mesh(cfg_global, phys, out_dir=out_dir, method_label="global")
