from __future__ import annotations

from pathlib import Path
from ._support import CAL

# Root unittest classes bind this function; avoid duplicate pytest collection.
__test__ = False


def test_paper_profile_locks_requested_camera_ready_fields(self) -> None:
    """Check the fixed profile inputs without running its larger mesh case."""
    cfg = CAL.paper_profile(results_dir=Path("paper-profile"))

    self.assertEqual(cfg.mesh_size, 16)
    self.assertEqual(cfg.ring_count, 8)
    self.assertAlmostEqual(cfg.ring_cross_talk, 0.06)
    self.assertIsNone(cfg.ring_cross_talk_sweep)
    self.assertEqual(cfg.partitions, 4)
    self.assertEqual(cfg.partition_solver, "heuristic")
    self.assertIsNone(cfg.kahypar_config)
    self.assertEqual(cfg.opt_solver, "gn")
    self.assertEqual(cfg.outer_rounds, 2)
    self.assertEqual(cfg.polishing_rounds, 2)
    self.assertEqual(cfg.tune_check_rounds, 3)
    self.assertAlmostEqual(cfg.tune_check_subset, 0.3)
    self.assertAlmostEqual(cfg.tune_check_step, 0.05)
    self.assertAlmostEqual(cfg.tune_check_lr, 0.5)
    self.assertAlmostEqual(cfg.drift_K, 0.5)
    self.assertEqual(cfg.seed, 7)
