"""paper_profile extracted from the calibration experiment runner."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from .models import CalibrationConfig
from .settings import RESULTS_DIR


def paper_profile(*, results_dir: Optional[Path] = None) -> CalibrationConfig:
    """Return the fixed experiment configuration used by --paper-profile.

    The profile fixes seed 7, heuristic partitioning, NumPy Gauss-Newton steps,
    all baseline methods, and cross-talk 0.06 without a cross-talk sweep.
    """
    return CalibrationConfig(
        mesh_size=16,
        ring_count=8,
        ring_cross_talk=0.06,
        ring_cross_talk_sweep=None,
        partitions=4,
        partition_solver="heuristic",
        kahypar_config=None,
        balance_eps=0.05,
        polishing_rounds=2,
        outer_rounds=2,
        opt_solver="gn",
        mesh_baselines="dfc,global,tunecheck",
        ring_baselines="parallel,scan",
        tune_check_rounds=3,
        tune_check_subset=0.3,
        tune_check_step=0.05,
        tune_check_lr=0.5,
        drift_K=0.5,
        target_mse=1e-4,
        seed=7,
        sweep=None,
        results_dir=(results_dir.resolve() if results_dir is not None else RESULTS_DIR),
    )
