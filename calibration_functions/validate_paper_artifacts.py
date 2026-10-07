"""validate_paper_artifacts extracted from the calibration experiment runner."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from typing import Dict
import json

from .models import CalibrationConfig
from .pick_ring_result import pick_ring_result


def validate_paper_artifacts(
    *,
    cfg: CalibrationConfig,
    ring_results: Dict[str, Any],
    ring_table_path: Path,
    manifest_path: Path,
) -> None:
    """Check manifest fields and the unsettled-scan table marker using assertions."""
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert "requested_solvers" in manifest
    assert "used_solvers" in manifest
    ring_text = ring_table_path.read_text(encoding="utf-8")
    scan_res = ring_results.get("scan")
    if isinstance(scan_res, list):
        scan_res = pick_ring_result(scan_res, preferred_ct=float(cfg.ring_cross_talk))
    if isinstance(scan_res, dict) and not bool(scan_res.get("settled_all", True)):
        horizon_ms = int(round(1000.0 * float(scan_res.get("control_horizon_s", 0.0))))
        assert f"$>{horizon_ms}$" in ring_text
