from __future__ import annotations

from ._support import CAL

# Root unittest classes bind this function; avoid duplicate pytest collection.
__test__ = False


def test_tunecheck_probe_invariant(self) -> None:
    """Each sampled coordinate requires two finite-difference probes."""
    cfg = CAL.CalibrationConfig(mesh_size=4, seed=7)
    phys = CAL.PhysicsParams()

    result = CAL.run_mesh_tune_and_check(cfg, phys, subset_frac=0.25, rounds=2, step_size=0.05, lr=0.5)

    subset_size = int(result["subset_size"])
    rounds_run = int(result["rounds_run"])
    self.assertEqual(int(result["probe_count"]), 2 * subset_size * rounds_run)
