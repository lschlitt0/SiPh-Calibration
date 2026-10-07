"""build_arg_parser extracted from the calibration experiment runner."""

from __future__ import annotations

from pathlib import Path
import argparse

from .settings import RESULTS_DIR


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="DfC paper experiment driver (v3).")
    p.add_argument("--mesh-size", type=int, default=16, help="Mesh dimension N for NxN mesh (toy).")
    p.add_argument("--rings", type=int, default=8, help="Number of rings in the filter bank.")
    p.add_argument("--ring-cross-talk", type=float, default=0.06, help="Cross-talk level for ring simulations.")
    p.add_argument(
        "--ring-cross-talk-sweep",
        type=str,
        default="0,0.03,0.06,0.10,0.15",
        help="Cross-talk sweep list for ring robustness (comma/.. syntax; empty to disable).",
    )
    p.add_argument("--partitions", type=int, default=4, help="Number of partitions for mesh calibration.")
    p.add_argument(
        "--partition-solver",
        type=str,
        default="auto",
        choices=("heuristic", "kahypar", "auto"),
        help="Hypergraph partitioner (heuristic, kahypar, auto).",
    )
    p.add_argument(
        "--kahypar-config",
        type=Path,
        default=None,
        help="Path to KaHyPar INI config (required for kahypar).",
    )
    p.add_argument("--balance-eps", type=float, default=0.05, help="Eq. (4) balance slack ε.")
    p.add_argument("--polishing-rounds", type=int, default=2, help="Boundary polishing rounds (1–2 typical).")
    p.add_argument("--outer-rounds", type=int, default=2, help="Mesh outer-loop calibration rounds.")
    p.add_argument(
        "--opt-solver",
        type=str,
        default="auto",
        choices=("gn", "docplex", "auto"),
        help="Per-block step solver (gn=linear solve, docplex=QP).",
    )
    p.add_argument(
        "--mesh-baselines",
        type=str,
        default="dfc,global,tunecheck",
        help="Comma list of mesh methods to run: dfc, global, tunecheck.",
    )
    p.add_argument(
        "--ring-baselines",
        type=str,
        default="parallel,scan",
        help="Comma list of ring methods to run: parallel, scan.",
    )
    p.add_argument("--tune-check-rounds", type=int, default=3, help="Rounds for tune-and-check baseline.")
    p.add_argument("--tune-check-subset", type=float, default=0.3, help="Fraction of tuners sampled per round.")
    p.add_argument("--tune-check-step", type=float, default=0.05, help="Finite-difference step for tune-and-check.")
    p.add_argument("--tune-check-lr", type=float, default=0.5, help="Update gain for tune-and-check baseline.")
    p.add_argument("--sweep", type=str, default="", help="Sweep spec, e.g., \"N=8,16;k=2,4;seed=1..5\".")
    p.add_argument("--drift-K", type=float, default=0.5, help="Thermal step (K) applied to the ring bank.")
    p.add_argument("--seed", type=int, default=7, help="Random seed.")
    p.add_argument("--results-dir", type=Path, default=RESULTS_DIR, help="Directory for outputs (plots, xlsx, tables, logs).")
    p.add_argument("--paper-profile", action="store_true", help="Run the locked manuscript-facing camera-ready profile.")
    p.add_argument("--no-mesh", action="store_true", help="Skip the mesh case study.")
    p.add_argument("--no-rings", action="store_true", help="Skip the ring case study.")
    return p
