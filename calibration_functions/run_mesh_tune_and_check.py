"""run_mesh_tune_and_check extracted from the calibration experiment runner."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
import numpy as np
import time

from ._seed_everything import _seed_everything
from .build_toy_mesh_hypergraph import build_toy_mesh_hypergraph
from .build_toy_mesh_plant import build_toy_mesh_plant
from .log import log
from .log_kv import log_kv
from .log_section import log_section
from .models import CalibrationConfig
from .models import MetricCounters
from .models import PhysicsParams
from .summarize_effort import summarize_effort


def run_mesh_tune_and_check(
    cfg: CalibrationConfig,
    phys: PhysicsParams,
    *,
    out_dir: Optional[Path] = None,
    subset_frac: float = 0.3,
    rounds: int = 3,
    step_size: float = 0.05,
    lr: float = 0.5,
) -> Dict[str, Any]:
    """Apply noisy finite-difference coordinate updates on the same toy mesh.

    Each round selects a seeded subset of tuners and probes plus/minus step_size
    command offsets. The MSE difference divided by 2*step_size drives an lr-scaled
    update, clipped to plant bounds. subset_frac is clipped to [0.05, 1].
    Stops after rounds (at least one) or noiseless MSE <= cfg.target_mse.

    Returns metrics and a round-level MSE history, without a final command vector.
    step_size must be nonzero; near bounds, clipped probe spacing can differ from
    the fixed denominator. Updates have no measured-cost acceptance check.
    phys is metadata only and out_dir does not trigger file export.
    """
    _seed_everything(cfg.seed + 313)
    t_start = time.perf_counter()
    rng_probe = np.random.default_rng(int(cfg.seed + 313))
    rng_eval = np.random.default_rng(int(cfg.seed + 99999))
    log_section("Mesh baseline (tunecheck)")
    metrics = MetricCounters()

    hg = build_toy_mesh_hypergraph(cfg.mesh_size, seed=cfg.seed)
    plant = build_toy_mesh_plant(hg, seed=cfg.seed + 101)
    u_min, u_max = plant.bounds()
    u = np.zeros(hg.n_vertices, dtype=float)

    def eval_mse(u_eval: np.ndarray) -> float:
        noise_std = float(plant.noise_std)
        plant.noise_std = 0.0
        y = plant.measure(u_eval, rng=rng_eval)
        plant.noise_std = noise_std
        return float(np.mean(y**2))

    def measure_cost(u_vec: np.ndarray) -> float:
        t0 = time.perf_counter()
        y = plant.measure(u_vec, rng=rng_probe)
        dt = float(time.perf_counter() - t0)
        metrics.record_probes(1, time_s=dt)
        return float(np.mean(y**2))

    mse_curve: List[float] = [eval_mse(u)]
    round_summaries: List[Dict[str, Any]] = []
    rounds_cfg = max(1, int(rounds))
    subset_frac = float(np.clip(subset_frac, 0.05, 1.0))
    subset_size = max(1, int(round(subset_frac * hg.n_vertices)))

    for r in range(rounds_cfg):
        idxs = rng_probe.choice(hg.n_vertices, size=subset_size, replace=False)
        for v in idxs:
            t_step0 = time.perf_counter()
            metrics.solver_iter_count += 1

            u_plus = u.copy()
            u_plus[v] = np.clip(u[v] + step_size, u_min[v], u_max[v])
            mse_plus = measure_cost(u_plus)

            u_minus = u.copy()
            u_minus[v] = np.clip(u[v] - step_size, u_min[v], u_max[v])
            mse_minus = measure_cost(u_minus)

            grad = (mse_plus - mse_minus) / (2.0 * float(step_size))
            update = -float(lr) * grad
            u_new = float(np.clip(u[v] + update, u_min[v], u_max[v]))
            if np.isfinite(u_new) and abs(u_new - u[v]) > 1e-12:
                u[v] = u_new
                metrics.record_hw_write()
            metrics.solve_time_s += float(time.perf_counter() - t_step0)

        mse_now = eval_mse(u)
        mse_curve.append(float(mse_now))
        round_summaries.append(
            {
                "round": int(r),
                "mse": float(mse_now),
                "probe_count": int(metrics.probe_count),
                "hw_write_count": int(metrics.hw_write_count),
                "solver_iter_count": int(metrics.solver_iter_count),
            }
        )
        log_kv(f"Tune-check round {r + 1}", f"{mse_now:.2e}")
        if mse_now <= float(cfg.target_mse):
            log("Target MSE reached; stopping tune-and-check early.")
            break

    mse_final = eval_mse(u)
    walltime_s = float(time.perf_counter() - t_start)
    effort = summarize_effort(
        metrics,
        probe_rounds_effective=int(metrics.probe_count),
        n_entities=hg.n_vertices,
        walltime_s=walltime_s,
    )

    result = {
        "method": "tunecheck",
        "N": int(cfg.mesh_size),
        "k": 1,
        "probe_count": int(effort["probe_count"]),
        "probe_rounds_effective": int(effort["probe_rounds_effective"]),
        "hw_write_count": int(effort["hw_write_count"]),
        "hw_commit_count": int(effort["hw_write_count"]),
        "hw_element_touch_count": int(effort["hw_element_touch_count"]),
        "solver_iter_count": int(effort["solver_iter_count"]),
        "total_probes": int(effort["probe_count"]),
        "tuner_updates": int(effort["solver_iter_count"]),
        "mse_final": float(mse_final),
        "mse_curve": [float(x) for x in mse_curve],
        "walltime": float(walltime_s),
        "probes_per_tuner": float(effort["probes_per_tuner"]),
        "hw_writes_per_tuner": float(effort["hw_writes_per_tuner"]),
        "hw_element_touches_per_tuner": float(effort["hw_element_touches_per_tuner"]),
        "seconds_per_probe": float(effort["seconds_per_probe"]),
        "seconds_per_solver_iter": float(effort["seconds_per_solver_iter"]),
        "probes_per_second": float(effort["probes_per_second"]),
        "initial_mse": float(mse_curve[0]) if mse_curve else float("nan"),
        "target_mse": float(cfg.target_mse),
        "rounds": int(len(round_summaries)),
        "rounds_cfg": int(rounds_cfg),
        "rounds_run": int(len(round_summaries)),
        "round_summaries": round_summaries,
        "subset_frac": float(subset_frac),
        "subset_size": int(subset_size),
        "tune_check_subset": int(subset_size),
        "tune_check_step": float(step_size),
        "tune_check_lr": float(lr),
        "step_size": float(step_size),
        "lr": float(lr),
        "timing_s": {
            "probe_s": float(metrics.probe_time_s),
            "solve_s": float(metrics.solve_time_s),
            "walltime_s": float(walltime_s),
        },
        "mesh_trace_rows": [],
        "physics": {"lam0_nm": phys.lam0_nm, "n_eff": phys.n_eff},
        "effort": effort,
    }
    log_kv("Tune-and-check MSE", f"{result['mse_final']:.2e}")
    log_kv("Probes (total)", result["probe_count"])
    log_kv("HW writes", result["hw_write_count"])
    log_kv("Solver iterations", result["solver_iter_count"])
    log_kv("Walltime (s)", f"{result['walltime']:.3f}")
    return result
