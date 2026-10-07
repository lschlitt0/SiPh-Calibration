"""Run a small seeded mesh calibration and ring-bank relocking simulation.

Run from the repository root with ``python examples/example_usage.py``.
The functions and result fields are the existing Calibration_v3 interfaces.
The mesh uses normalized residuals; the ring model reports detuning in pm.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


# Make the compatibility entry point and function package importable from this example.
REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT))

from Calibration_v3 import (  # noqa: E402
    CalibrationConfig,
    PhysicsParams,
    run_dfc_mesh,
    simulate_ring_bank,
)


def main() -> None:
    """Print calibration accuracy and effort without optional plotting or solvers."""
    cfg = CalibrationConfig(
        mesh_size=4,
        partitions=2,
        partition_solver="heuristic",
        opt_solver="gn",
        outer_rounds=2,
        polishing_rounds=2,
        ring_count=4,
        ring_cross_talk=0.06,
        ring_cross_talk_sweep=None,
        drift_K=0.5,
        seed=7,
    )
    # These parameters are returned as metadata by the current toy simulations.
    # State equations and controller constants are in calibration_functions/:
    # models.py (mesh plant) and simulate_ring_bank.py (ring dynamics/controller).
    phys = PhysicsParams()

    mesh = run_dfc_mesh(cfg, phys)
    rings = simulate_ring_bank(cfg, phys, capture_traces=False)

    summary = {
        "seed": cfg.seed,
        "mesh": {
            "tuners": mesh["vertices"],
            "initial_mse": mesh["initial_mse"],
            "final_mse": mesh["mse_final"],
            "target_mse": cfg.target_mse,
            "target_reached": mesh["mse_final"] <= cfg.target_mse,
            "probe_count": mesh["probe_count"],
            "effective_probe_rounds": mesh["probe_rounds_effective"],
            "hardware_writes": mesh["hw_write_count"],
            "solver_iterations": mesh["solver_iter_count"],
        },
        "rings": {
            "count": rings["rings"],
            "settled_all": rings["settled_all"],
            "settle_ms": rings["settle_ms"],
            "peak_pm": rings["peak_pm"],
            "rms_pm": rings["rms_pm"],
            "probe_count": rings["probe_count"],
        },
    }
    print("\nExample summary (MSE in normalized residual units squared):")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
