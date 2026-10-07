"""apply_paper_profile extracted from the calibration experiment runner."""

from __future__ import annotations

from dataclasses import replace

from .models import CalibrationConfig
from .paper_profile import paper_profile


def apply_paper_profile(cfg: CalibrationConfig) -> CalibrationConfig:
    """Replace experiment settings with paper_profile, retaining the output path."""
    locked = paper_profile(results_dir=cfg.results_dir)
    return replace(
        cfg,
        mesh_size=locked.mesh_size,
        ring_count=locked.ring_count,
        ring_cross_talk=locked.ring_cross_talk,
        ring_cross_talk_sweep=locked.ring_cross_talk_sweep,
        partitions=locked.partitions,
        partition_solver=locked.partition_solver,
        kahypar_config=locked.kahypar_config,
        balance_eps=locked.balance_eps,
        polishing_rounds=locked.polishing_rounds,
        outer_rounds=locked.outer_rounds,
        opt_solver=locked.opt_solver,
        mesh_baselines=locked.mesh_baselines,
        ring_baselines=locked.ring_baselines,
        tune_check_rounds=locked.tune_check_rounds,
        tune_check_subset=locked.tune_check_subset,
        tune_check_step=locked.tune_check_step,
        tune_check_lr=locked.tune_check_lr,
        drift_K=locked.drift_K,
        target_mse=locked.target_mse,
        seed=locked.seed,
        sweep=None,
        results_dir=locked.results_dir,
    )
