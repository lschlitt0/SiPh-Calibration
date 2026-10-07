"""run_dfc_mesh extracted from the calibration experiment runner."""

from __future__ import annotations

from numpy.typing import NDArray
from pathlib import Path
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple
import numpy as np
import time

from ._jacobian_condition_number import _jacobian_condition_number
from ._orthogonal_sign_patterns import _orthogonal_sign_patterns
from ._partition_with_solver_metadata import _partition_with_solver_metadata
from ._resolve_opt_solver_used import _resolve_opt_solver_used
from ._resolve_step_solver import _resolve_step_solver
from ._seed_everything import _seed_everything
from .build_toy_mesh_hypergraph import build_toy_mesh_hypergraph
from .build_toy_mesh_plant import build_toy_mesh_plant
from .cross_terms_from_internal_edges import cross_terms_from_internal_edges
from .fit_surrogate_with_trust_region import fit_surrogate_with_trust_region
from .gauss_newton_solve import gauss_newton_solve
from .log import log
from .log_kv import log_kv
from .log_section import log_section
from .models import BlockModel
from .models import CalibrationConfig
from .models import MetricCounters
from .models import PhysicsParams
from .models import PolyRidgeSurrogate
from .models import SurrogateFitReport
from .summarize_effort import summarize_effort


def run_dfc_mesh(
    cfg: CalibrationConfig,
    phys: PhysicsParams,
    *,
    out_dir: Optional[Path] = None,
    method_label: str = "dfc",
) -> Dict[str, Any]:
    """Calibrate the synthetic mesh using partitioned local surrogate models.

    cfg selects graph size, partitioner, retry rounds, solver, and random seed.
    phys contributes metadata only; out_dir is retained in the interface but is
    not used to export files here. All tuners start at zero, target residuals
    are zero, and commands are clipped to the plant's abstract [-1, 1] bounds.

    Each outer round probes internal hyperedges with noise, fits local models,
    and solves bounded updates from the current command. Solutions are applied
    together after all block solves. The implementation executes blocks serially;
    effective probe rounds estimate ideal simultaneous block probing. The outer
    loop stops on noiseless global MSE <= cfg.target_mse or cfg.outer_rounds.
    Boundary-only polishing then targets cut edges for cfg.polishing_rounds,
    retaining the candidate with the best noiseless global MSE in each round.

    Returns MSE histories, per-block diagnostics, effort counts, timing, and trace
    rows. No final tuner vector is included. Exact plant evaluations used for
    diagnostics and polishing selection are not counted as noisy hardware probes.
    The CLI/suite handles export of this returned data.
    """
    _seed_everything(cfg.seed)
    t_start = time.perf_counter()
    rng_probe = np.random.default_rng(int(cfg.seed))
    rng_eval = np.random.default_rng(int(cfg.seed + 9999))
    label_pretty = method_label.replace("_", " ")
    log_section(f"Mesh case ({label_pretty})")
    metrics = MetricCounters()

    mesh_trace_rows: List[Dict[str, Any]] = []

    # Stage 1: build weighted hypergraph + toy plant
    log("Stage 1) build weighted hypergraph")
    t_build0 = time.perf_counter()
    hg = build_toy_mesh_hypergraph(cfg.mesh_size, seed=cfg.seed)
    plant = build_toy_mesh_plant(hg, seed=cfg.seed + 101)
    t_build_s = float(time.perf_counter() - t_build0)
    u_min, u_max = plant.bounds()
    u = np.zeros(hg.n_vertices, dtype=float)
    log_kv("Vertices", hg.n_vertices)
    log_kv("Hyperedges", len(hg.edges))

    def eval_mse(u_eval: np.ndarray) -> float:
        noise_std = float(plant.noise_std)
        plant.noise_std = 0.0
        y = plant.measure(u_eval, rng=rng_eval)
        plant.noise_std = noise_std
        return float(np.mean(y**2))

    def eval_mse_edges(u_eval: np.ndarray, edges_sel: np.ndarray) -> float:
        if edges_sel.size == 0:
            return 0.0
        noise_std = float(plant.noise_std)
        plant.noise_std = 0.0
        y = plant.measure(u_eval, rng=rng_eval)
        plant.noise_std = noise_std
        return float(np.mean(y[np.asarray(edges_sel, dtype=int)] ** 2))

    # Exact noiseless evaluation is available in this synthetic plant. These
    # diagnostics are separate from noisy probes counted as calibration effort.
    mse0 = eval_mse(u)
    u_eval = u.copy()
    mse_curve: List[float] = [mse0]
    mesh_trace_rows.append(
        {
            "stage": "init",
            "block_id": "",
            "polish_round": "",
            "outer_round": 0,
            "iter": 0,
            "tuner_updates": 0,
            "probes_total": metrics.probe_count,
            "probe_rounds_effective": 0,
            "probe_count": metrics.probe_count,
            "hw_write_count": metrics.hw_write_count,
            "solver_iter_count": metrics.solver_iter_count,
            "step_norm": 0.0,
            "res_norm": 0.0,
            "res_mse": 0.0,
            "jacobian_cond": 0.0,
            "mu": 0.0,
            "global_mse": float(mse0),
            "walltime_s": float(time.perf_counter() - t_start),
        }
    )
    log_kv("Initial MSE", f"{mse0:.2e}")

    # Stage 2: balanced k-way partitioning (Eq. 4)
    log("Stage 2) balanced k-way partitioning (Eq. 4)")
    t_part0 = time.perf_counter()
    part_res, partition_solver_used = _partition_with_solver_metadata(
        hg,
        cfg.partitions,
        cfg.balance_eps,
        seed=cfg.seed + 5,
        solver=cfg.partition_solver,
        kahypar_config=cfg.kahypar_config,
    )
    t_partition_s = float(time.perf_counter() - t_part0)
    log_kv("Cut objective", f"{part_res.objective:.3f}")
    log_kv("Cut hyperedges", len(part_res.cut_edges))
    log_kv("Boundary tuners", len(part_res.boundary))
    log_kv("Balance ok", hg.check_balance(part_res.part, cfg.partitions, cfg.balance_eps))
    step_solver = _resolve_step_solver(cfg.opt_solver)
    opt_solver_used = _resolve_opt_solver_used(cfg.opt_solver)

    # Precompute internal edges per block (these are the per-block targets).
    blocks: List[np.ndarray] = [np.where(part_res.part == i)[0] for i in range(cfg.partitions)]
    edges_internal: List[np.ndarray] = []
    for i in range(cfg.partitions):
        block_vertex_set = set(int(v) for v in blocks[i])
        internal = [ei for ei, e in enumerate(hg.edges) if all(int(v) in block_vertex_set for v in e.pins)]
        edges_internal.append(np.array(internal, dtype=int))
    boundary_set = set(int(v) for v in part_res.boundary)
    block_boundary_counts: List[int] = []
    block_boundary_fracs: List[float] = []
    for i in range(cfg.partitions):
        verts = blocks[i]
        if verts.size:
            boundary_count = sum(1 for v in verts if int(v) in boundary_set)
            boundary_frac = boundary_count / float(verts.size)
        else:
            boundary_count = 0
            boundary_frac = 0.0
        block_boundary_counts.append(int(boundary_count))
        block_boundary_fracs.append(float(boundary_frac))

    outer_rounds_cfg = max(1, int(getattr(cfg, "outer_rounds", 1)))
    # Model/optimizer constants act in abstract mesh command and residual units.
    surrogate_lambda = 1e-3
    target_val_mse = 5e-3
    gn_mu = 1e-3
    gn_iters = 20
    cond_threshold = 1e6
    max_slew = 0.05 * np.ones(hg.n_vertices, dtype=float)
    probe_time_total_s = 0.0
    fit_time_total_s = 0.0
    solve_time_total_s = 0.0
    t_stage3_s = 0.0
    t_stage4_s = 0.0
    probe_rounds_effective_total = 0
    probe_rounds_by_round: List[int] = []
    probe_rounds_polish: List[int] = []
    probes_per_block_total = [0 for _ in range(cfg.partitions)]
    probes_per_block_by_round: List[List[int]] = []
    block_diagnostics: List[Dict[str, Any]] = []
    outer_round_summaries: List[Dict[str, Any]] = []
    mse_after_rounds: List[float] = []
    outer_completed = -1

    for outer in range(outer_rounds_cfg):
        log(f"Outer round {outer + 1}/{outer_rounds_cfg}")
        # Stage 3: per-block surrogate training (Eqs. 5–6)
        log("Stage 3) per-block surrogate training (Eqs. 5–6)")
        t_stage3_0 = time.perf_counter()
        block_models: List[BlockModel] = []
        probes_this_round = [0 for _ in range(cfg.partitions)]
        for i in range(cfg.partitions):
            verts_idx: NDArray[np.int_] = np.asarray(blocks[i], dtype=int)
            edges_i: NDArray[np.int_] = np.asarray(edges_internal[i], dtype=int)
            if edges_i.size == 0 or verts_idx.size == 0:
                continue

            z0 = u[verts_idx].copy()
            max_cross_terms = int(np.clip(4 * verts_idx.size, 64, 256))
            cross_terms = cross_terms_from_internal_edges(verts_idx, edges_i, hg, max_terms=max_cross_terms)
            patterns_seed_base = cfg.seed + 1000 + i + 100 * outer
            fit_seed_base = cfg.seed + 2000 + i + 100 * outer
            fit_attempt = 0

            def run_fit_once(
                *,
                min_samples: Optional[int] = None,
                initial_trust_radius: Optional[float] = None,
            ) -> Tuple[PolyRidgeSurrogate, SurrogateFitReport, float, float]:
                nonlocal fit_attempt
                sampler_time_s = [0.0]
                pattern_seed = patterns_seed_base + 1000 * fit_attempt

                def sampler(trust_radius: float, n_samples: int) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
                    t0 = time.perf_counter()
                    patterns = _orthogonal_sign_patterns(n_samples, verts_idx.size, seed=pattern_seed)
                    Z = np.zeros((n_samples, verts_idx.size), dtype=float)
                    Y = np.zeros((n_samples, edges_i.size), dtype=float)
                    for k in range(n_samples):
                        u_k = u.copy()
                        du = trust_radius * patterns[k]
                        u_k[verts_idx] = np.clip(u[verts_idx] + du, u_min[verts_idx], u_max[verts_idx])
                        z = u_k[verts_idx]
                        y = plant.measure(u_k, rng=rng_probe)[edges_i]
                        Z[k] = z
                        Y[k] = y
                    sampler_time_s[0] += float(time.perf_counter() - t0)
                    return Z, Y, edges_i

                t_block0 = time.perf_counter()
                surrogate_local, report_local = fit_surrogate_with_trust_region(
                    sampler,
                    z0=z0,
                    lam=surrogate_lambda,
                    target_val_mse=target_val_mse,
                    seed=fit_seed_base + fit_attempt,
                    cross_terms=cross_terms,
                    initial_trust_radius=initial_trust_radius if initial_trust_radius is not None else 0.20,
                    min_samples=min_samples,
                )
                fit_attempt += 1
                block_total_s = float(time.perf_counter() - t_block0)
                block_probe_s = float(sampler_time_s[0])
                block_fit_s = max(0.0, block_total_s - block_probe_s)
                return surrogate_local, report_local, block_probe_s, block_fit_s

            block_probe_s_total = 0.0
            block_fit_s_total = 0.0
            probes_used = 0
            cond_before: Optional[float] = None
            cond_after: Optional[float] = None
            cond_refit = False

            surrogate, report, block_probe_s, block_fit_s = run_fit_once()
            block_probe_s_total += block_probe_s
            block_fit_s_total += block_fit_s
            probes_used += int(report.total_samples)
            metrics.record_probes(report.total_samples, time_s=block_probe_s)

            J0 = surrogate.jacobian(z0)[:, : verts_idx.size]
            cond_before = _jacobian_condition_number(J0)
            cond_after = cond_before

            if cond_before > cond_threshold:
                cond_refit = True
                retry_samples = max(int(report.n_samples * 2), int(report.total_samples))
                surrogate, report, block_probe_s, block_fit_s = run_fit_once(
                    min_samples=retry_samples,
                    initial_trust_radius=0.5 * report.trust_radius,
                )
                block_probe_s_total += block_probe_s
                block_fit_s_total += block_fit_s
                probes_used += int(report.total_samples)
                metrics.record_probes(report.total_samples, time_s=block_probe_s)

                J0 = surrogate.jacobian(z0)[:, : verts_idx.size]
                cond_after = _jacobian_condition_number(J0)

            probes_this_round[i] = int(probes_used)
            probes_per_block_total[i] += int(probes_used)
            probe_time_total_s += block_probe_s_total
            fit_time_total_s += block_fit_s_total
            block_diag = {
                "outer_round": int(outer),
                "block_id": int(i),
                "n_vertices": int(verts_idx.size),
                "n_edges_internal": int(edges_i.size),
                "boundary_count": int(block_boundary_counts[i]),
                "boundary_frac": float(block_boundary_fracs[i]),
                "probes_total": int(probes_used),
                "surrogate_val_mse": float(report.val_mse),
                "trust_radius": float(report.trust_radius),
                "attempts": int(report.attempts),
                "n_features": int(report.n_features),
                "cross_terms": int(report.cross_terms),
                "jacobian_cond": float(cond_after),
                "jacobian_cond_before": float(cond_before if cond_before is not None else 0.0),
                "cond_threshold": float(cond_threshold),
                "cond_refit": bool(cond_refit),
                "probe_time_s": float(block_probe_s_total),
                "fit_time_s": float(block_fit_s_total),
            }
            block_diagnostics.append(block_diag)
            block_models.append(
                BlockModel(
                    block_id=i,
                    vertices=verts_idx,
                    edges_internal=edges_i,
                    surrogate=surrogate,
                    report=report,
                    jacobian_cond=float(cond_after if cond_after is not None else 0.0),
                )
            )

        log_kv("Blocks trained", len(block_models))
        if block_models:
            log_kv("Median J cond", f"{np.median([b.jacobian_cond for b in block_models]):.2e}")
        t_stage3_s += float(time.perf_counter() - t_stage3_0)
        probes_per_block_by_round.append([int(x) for x in probes_this_round])
        probe_rounds_this_round = int(max(probes_this_round)) if probes_this_round else 0
        probe_rounds_effective_total += probe_rounds_this_round
        probe_rounds_by_round.append(probe_rounds_this_round)

        # Stage 4: per-block local optimization (Gauss–Newton with slew/bounds).
        log("Stage 4) per-block local optimization")
        t_stage4_0 = time.perf_counter()
        u_block_solutions: Dict[int, np.ndarray] = {}
        for bm in sorted(block_models, key=lambda b: int(b.block_id)):
            verts = bm.vertices
            y_target = np.zeros(bm.edges_internal.size, dtype=float)

            def predict_u(u_block: np.ndarray) -> np.ndarray:
                return bm.surrogate.predict(u_block)

            def jac_u(u_block: np.ndarray) -> np.ndarray:
                return bm.surrogate.jacobian(u_block)[:, : u_block.size]

            verts_idx = verts
            u0_block = u[verts].copy()
            t_solve0 = time.perf_counter()

            def _cb_block(**kw: Any) -> None:
                nonlocal u_eval
                it = int(kw["it"])
                z_next = np.asarray(kw["z_next"], dtype=float)
                dz = np.asarray(kw["dz"], dtype=float)
                r = np.asarray(kw["r"], dtype=float)
                J = np.asarray(kw["J"], dtype=float)
                mu_val = float(kw["mu"])
                iter_count = int(metrics.solver_iter_count)

                u_eval[verts] = z_next
                global_mse = eval_mse(u_eval)
                mse_curve.append(float(global_mse))

                mesh_trace_rows.append(
                    {
                        "stage": "block",
                        "block_id": int(bm.block_id),
                        "outer_round": int(outer),
                        "polish_round": "",
                        "iter": int(it),
                        "tuner_updates": iter_count,
                        "probes_total": int(metrics.probe_count),
                        "probe_rounds_effective": int(probe_rounds_effective_total),
                        "probe_count": int(metrics.probe_count),
                        "hw_write_count": int(metrics.hw_write_count),
                        "solver_iter_count": iter_count,
                        "step_norm": float(np.linalg.norm(dz)),
                        "res_norm": float(np.linalg.norm(r)),
                        "res_mse": float(np.mean(r**2)) if r.size else 0.0,
                        "jacobian_cond": float(_jacobian_condition_number(J)),
                        "mu": float(mu_val),
                        "global_mse": float(global_mse),
                        "walltime_s": float(time.perf_counter() - t_start),
                    }
                )

            u_opt, it_used, _ = gauss_newton_solve(
                predict_u,
                jac_u,
                u0_block,
                y_target,
                u_min[verts],
                u_max[verts],
                max_slew[verts],
                trust_radius=bm.report.trust_radius,
                mu=gn_mu,
                iters=gn_iters,
                step_solver=step_solver,
                callback=_cb_block,
                metrics=metrics,
            )
            solve_time_s = float(time.perf_counter() - t_solve0)
            solve_time_total_s += solve_time_s
            metrics.solve_time_s += solve_time_s
            u_block_solutions[int(bm.block_id)] = u_opt
            u_eval[verts] = u_opt
            for block_diag in reversed(block_diagnostics):
                if block_diag.get("block_id") == int(bm.block_id) and block_diag.get("outer_round") == int(outer):
                    block_diag["gn_iters"] = int(it_used)
                    block_diag["solve_time_s"] = float(solve_time_s)
                    break

        t_stage4_s += float(time.perf_counter() - t_stage4_0)

        # Apply per-block solutions (hardware writes counted once per block).
        u_new = u.copy()
        for bm in block_models:
            if bm.block_id in u_block_solutions:
                u_prev_block = u_new[bm.vertices].copy()
                u_next_block = np.asarray(u_block_solutions[bm.block_id], dtype=float)
                changed = int(np.count_nonzero(np.abs(u_next_block - u_prev_block) > 1e-12))
                u_new[bm.vertices] = u_next_block
                metrics.record_hw_write(element_touches=changed)
        u = u_new
        u_eval = u.copy()
        mse_blocks = eval_mse(u)
        mse_after_rounds.append(float(mse_blocks))
        outer_round_summaries.append(
            {
                "outer_round": int(outer),
                "mse_after_blocks": float(mse_blocks),
                "probe_count": int(metrics.probe_count),
                "probe_rounds_effective": int(probe_rounds_this_round),
                "hw_write_count": int(metrics.hw_write_count),
                "solver_iter_count": int(metrics.solver_iter_count),
            }
        )
        mesh_trace_rows.append(
            {
                "stage": "outer_apply",
                "block_id": "",
                "polish_round": "",
                "outer_round": int(outer),
                "iter": 0,
                "tuner_updates": int(metrics.solver_iter_count),
                "probes_total": int(metrics.probe_count),
                "probe_rounds_effective": int(probe_rounds_effective_total),
                "probe_count": int(metrics.probe_count),
                "hw_write_count": int(metrics.hw_write_count),
                "solver_iter_count": int(metrics.solver_iter_count),
                "step_norm": 0.0,
                "res_norm": 0.0,
                "res_mse": 0.0,
                "jacobian_cond": 0.0,
                "mu": 0.0,
                "global_mse": float(mse_blocks),
                "walltime_s": float(time.perf_counter() - t_start),
            }
        )
        log_kv(f"MSE after round {outer + 1}", f"{mse_blocks:.2e}")
        outer_completed = outer
        if mse_blocks <= float(cfg.target_mse):
            log("Target MSE reached; stopping outer loop early.")
            break

    # Stage 5: boundary-only polishing after the outer block-apply rounds.
    log("Stage 5) parallel apply + boundary-only polishing")

    cut_edges: NDArray[np.int_] = np.array(part_res.cut_edges, dtype=int)
    boundary: NDArray[np.int_] = np.array(sorted(part_res.boundary), dtype=int)
    boundary_idx: NDArray[np.int_] = boundary
    internal_edge_union = (
        np.unique(np.concatenate([arr for arr in edges_internal if arr.size > 0]))
        if any(arr.size > 0 for arr in edges_internal)
        else np.array([], dtype=int)
    )
    polish_rounds = int(cfg.polishing_rounds)
    polish_probe_time_s = 0.0
    polish_fit_time_s = 0.0
    polish_solve_time_s = 0.0
    mse_cut_before_polish = eval_mse_edges(u_eval, cut_edges)
    mse_internal_before_polish = eval_mse_edges(u_eval, internal_edge_union)
    log_kv("MSE (cut edges, pre-polish)", f"{mse_cut_before_polish:.2e}")
    log_kv("MSE (internal edges, pre-polish)", f"{mse_internal_before_polish:.2e}")
    if polish_rounds > 0 and cut_edges.size > 0 and boundary.size > 0:
        for r in range(polish_rounds):
            z0_b = u[boundary_idx].copy()
            max_cross_terms_b = int(np.clip(4 * boundary_idx.size, 64, 256))
            cross_terms_b = cross_terms_from_internal_edges(boundary_idx, cut_edges, hg, max_terms=max_cross_terms_b)
            probe_rounds_used = 0
            cond_b_before: Optional[float] = None
            cond_b_after: Optional[float] = None

            def run_polish_fit(
                *,
                seed_offset: int = 0,
                min_samples: Optional[int] = None,
                initial_trust_radius: Optional[float] = None,
            ) -> Tuple[PolyRidgeSurrogate, SurrogateFitReport, float, float]:
                sampler_time_s = [0.0]
                pattern_seed = cfg.seed + 3000 + r + seed_offset

                def sampler_b(trust_radius: float, n_samples: int) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
                    t0 = time.perf_counter()
                    patterns = _orthogonal_sign_patterns(n_samples, boundary_idx.size, seed=pattern_seed)
                    Z = np.zeros((n_samples, boundary_idx.size), dtype=float)
                    Y = np.zeros((n_samples, cut_edges.size), dtype=float)
                    for k in range(n_samples):
                        u_k = u.copy()
                        du = trust_radius * patterns[k]
                        u_k[boundary_idx] = np.clip(u[boundary_idx] + du, u_min[boundary_idx], u_max[boundary_idx])
                        Z[k] = u_k[boundary_idx]
                        Y[k] = plant.measure(u_k, rng=rng_probe)[cut_edges]
                    sampler_time_s[0] += float(time.perf_counter() - t0)
                    return Z, Y, cut_edges

                t_fit0 = time.perf_counter()
                surrogate_local, report_local = fit_surrogate_with_trust_region(
                    sampler_b,
                    z0=z0_b,
                    lam=surrogate_lambda,
                    target_val_mse=target_val_mse,
                    seed=cfg.seed + 4000 + r + seed_offset,
                    cross_terms=cross_terms_b,
                    initial_trust_radius=initial_trust_radius if initial_trust_radius is not None else 0.20,
                    min_samples=min_samples,
                )
                fit_total_s = float(time.perf_counter() - t_fit0)
                probe_s = float(sampler_time_s[0])
                fit_s = max(0.0, fit_total_s - probe_s)
                return surrogate_local, report_local, probe_s, fit_s

            surrogate_b, report_b, probe_s, fit_s = run_polish_fit()
            probe_rounds_used += int(report_b.total_samples)
            polish_probe_time_s += probe_s
            polish_fit_time_s += fit_s
            metrics.record_probes(report_b.total_samples, time_s=probe_s)

            J_b0 = surrogate_b.jacobian(z0_b)[:, : boundary.size]
            cond_b_before = _jacobian_condition_number(J_b0)
            cond_b_after = cond_b_before

            if cond_b_before > cond_threshold:
                retry_samples_b = max(int(report_b.n_samples * 2), int(report_b.total_samples))
                surrogate_b, report_b, probe_s, fit_s = run_polish_fit(
                    seed_offset=100,
                    min_samples=retry_samples_b,
                    initial_trust_radius=0.5 * report_b.trust_radius,
                )
                probe_rounds_used += int(report_b.total_samples)
                polish_probe_time_s += probe_s
                polish_fit_time_s += fit_s
                metrics.record_probes(report_b.total_samples, time_s=probe_s)

                J_b0 = surrogate_b.jacobian(z0_b)[:, : boundary.size]
                cond_b_after = _jacobian_condition_number(J_b0)

            probe_rounds_polish.append(int(probe_rounds_used))
            probe_rounds_effective_total += int(probe_rounds_used)
            y_target_b = np.zeros(cut_edges.size, dtype=float)

            def predict_b(u_b: np.ndarray) -> np.ndarray:
                return surrogate_b.predict(u_b)

            def jac_b(u_b: np.ndarray) -> np.ndarray:
                return surrogate_b.jacobian(u_b)[:, : u_b.size]

            u0_b = u[boundary_idx].copy()
            best_mse_b = eval_mse(u_eval)
            best_u_b = u0_b.copy()
            t_solve0 = time.perf_counter()

            def _cb_polish(**kw: Any) -> None:
                nonlocal u_eval, best_mse_b, best_u_b
                it = int(kw["it"])
                z_next = np.asarray(kw["z_next"], dtype=float)
                dz = np.asarray(kw["dz"], dtype=float)
                rvec = np.asarray(kw["r"], dtype=float)
                Jmat = np.asarray(kw["J"], dtype=float)
                mu_val = float(kw["mu"])
                iter_count = int(metrics.solver_iter_count)

                u_eval[boundary_idx] = z_next
                global_mse = eval_mse(u_eval)
                mse_curve.append(float(global_mse))
                if global_mse < best_mse_b:
                    best_mse_b = float(global_mse)
                    best_u_b = z_next.copy()

                mesh_trace_rows.append(
                    {
                        "stage": "polish",
                        "block_id": "",
                        "polish_round": int(r),
                        "outer_round": int(outer_completed if outer_completed >= 0 else outer_rounds_cfg - 1),
                        "iter": int(it),
                        "tuner_updates": iter_count,
                        "probes_total": int(metrics.probe_count),
                        "probe_rounds_effective": int(probe_rounds_effective_total),
                        "probe_count": int(metrics.probe_count),
                        "hw_write_count": int(metrics.hw_write_count),
                        "solver_iter_count": iter_count,
                        "step_norm": float(np.linalg.norm(dz)),
                        "res_norm": float(np.linalg.norm(rvec)),
                        "res_mse": float(np.mean(rvec**2)) if rvec.size else 0.0,
                        "jacobian_cond": float(_jacobian_condition_number(Jmat)),
                        "mu": float(mu_val),
                        "global_mse": float(global_mse),
                        "walltime_s": float(time.perf_counter() - t_start),
                    }
                )

            u_opt_b, it_used_b, _ = gauss_newton_solve(
                predict_b,
                jac_b,
                u0_b,
                y_target_b,
                u_min[boundary_idx],
                u_max[boundary_idx],
                max_slew[boundary_idx],
                trust_radius=report_b.trust_radius,
                mu=gn_mu,
                iters=gn_iters,
                step_solver=step_solver,
                callback=_cb_polish,
                metrics=metrics,
            )
            # Select using noiseless global plant MSE, including internal edges.
            # This oracle evaluation is available only in the synthetic model.
            u_opt_b = best_u_b
            boundary_prev = u[boundary_idx].copy()
            u[boundary_idx] = u_opt_b
            u_eval[boundary_idx] = u_opt_b
            solve_dt = float(time.perf_counter() - t_solve0)
            polish_solve_time_s += solve_dt
            metrics.solve_time_s += solve_dt
            changed = int(np.count_nonzero(np.abs(u_opt_b - boundary_prev) > 1e-12))
            metrics.record_hw_write(element_touches=changed)

    mse_cut_after_polish = eval_mse_edges(u_eval, cut_edges)
    mse_internal_after_polish = eval_mse_edges(u_eval, internal_edge_union)
    log_kv("MSE (cut edges, post-polish)", f"{mse_cut_after_polish:.2e}")
    log_kv("MSE (internal edges, post-polish)", f"{mse_internal_after_polish:.2e}")

    mse_final = eval_mse(u)
    walltime_s = float(time.perf_counter() - t_start)
    effort = summarize_effort(
        metrics,
        probe_rounds_effective=int(probe_rounds_effective_total),
        n_entities=hg.n_vertices,
        walltime_s=walltime_s,
    )
    probe_count = int(effort["probe_count"])
    hw_write_count = int(effort["hw_write_count"])
    hw_element_touch_count = int(effort["hw_element_touch_count"])
    solver_iters = int(effort["solver_iter_count"])

    total_edge_weight = float(sum(float(e.weight) for e in hg.edges))
    cut_weight = float(sum(float(hg.edges[ei].weight) for ei in part_res.cut_edges))
    internal_edges = int(sum(int(arr.size) for arr in edges_internal))
    block_sizes = [int(b.size) for b in blocks]
    block_w = part_res.block_weights.astype(float).reshape(-1)
    block_weight_stats = {
        "min": float(np.min(block_w)) if block_w.size else 0.0,
        "max": float(np.max(block_w)) if block_w.size else 0.0,
        "mean": float(np.mean(block_w)) if block_w.size else 0.0,
        "std": float(np.std(block_w)) if block_w.size else 0.0,
    }

    block_diag_list = sorted(
        block_diagnostics, key=lambda d: (int(d.get("outer_round", 0)), int(d.get("block_id", 0)))
    )
    block_total_times = [
        float(d.get("probe_time_s", 0.0)) + float(d.get("fit_time_s", 0.0)) + float(d.get("solve_time_s", 0.0))
        for d in block_diag_list
    ]
    polish_total_time_s = float(polish_probe_time_s + polish_fit_time_s + polish_solve_time_s)
    time_sequential_est_s = float(
        t_build_s + t_partition_s + sum(block_total_times) + polish_total_time_s
    )
    # This estimate uses one maximum across all block/outer-round records;
    # it is not a measured parallel runtime or a sum of per-round maxima.
    time_parallel_equivalent_s = float(
        t_build_s
        + t_partition_s
        + (max(block_total_times) if block_total_times else 0.0)
        + polish_total_time_s
    )

    result = {
        "N": int(cfg.mesh_size),
        "k": int(cfg.partitions),
        "method": str(method_label),
        "outer_rounds_configured": int(outer_rounds_cfg),
        "outer_rounds_run": int(len(mse_after_rounds)),
        "outer_round_summaries": outer_round_summaries,
        "probes_per_block": [int(x) for x in probes_per_block_total],
        "probes_per_block_by_round": [[int(x) for x in row] for row in probes_per_block_by_round],
        "probe_count": probe_count,
        "probe_rounds_effective": int(probe_rounds_effective_total),
        "probe_rounds_by_round": [int(x) for x in probe_rounds_by_round],
        "probe_rounds_polish": [int(x) for x in probe_rounds_polish],
        "hw_write_count": hw_write_count,
        "hw_commit_count": hw_write_count,
        "hw_element_touch_count": hw_element_touch_count,
        "solver_iter_count": solver_iters,
        "total_probes": probe_count,
        "tuner_updates": solver_iters,
        "mse_final": float(mse_final),
        "mse_curve": [float(x) for x in mse_curve],
        "walltime": float(walltime_s),
        "probes_per_tuner": float(effort["probes_per_tuner"]),
        "hw_writes_per_tuner": float(effort["hw_writes_per_tuner"]),
        "hw_element_touches_per_tuner": float(effort["hw_element_touches_per_tuner"]),
        "seconds_per_probe": float(effort["seconds_per_probe"]),
        "seconds_per_solver_iter": float(effort["seconds_per_solver_iter"]),
        "probes_per_second": float(effort["probes_per_second"]),
        "mesh_trace_rows": [dict(row) for row in mesh_trace_rows],
        "mesh_size": cfg.mesh_size,
        "partitions": cfg.partitions,
        "balance_eps": cfg.balance_eps,
        "vertices": hg.n_vertices,
        "hyperedges": len(hg.edges),
        "cut_objective": part_res.objective,
        "cut_hyperedges": int(cut_edges.size),
        "cut_weight": float(cut_weight),
        "cut_weight_fraction": float(cut_weight / total_edge_weight) if total_edge_weight > 0.0 else 0.0,
        "boundary_tuners": int(boundary.size),
        "boundary_fraction": float(boundary.size / hg.n_vertices) if hg.n_vertices > 0 else 0.0,
        "block_sizes": [int(x) for x in block_sizes],
        "block_boundary_counts": [int(x) for x in block_boundary_counts],
        "block_boundary_fracs": [float(x) for x in block_boundary_fracs],
        "block_weight_stats": block_weight_stats,
        "edges_internal": int(internal_edges),
        "edges_internal_fraction": float(internal_edges / len(hg.edges)) if hg.edges else 0.0,
        "polishing_rounds": polish_rounds,
        "partition_solver_requested": str(cfg.partition_solver),
        "partition_solver_used": str(partition_solver_used),
        "opt_solver_requested": str(cfg.opt_solver),
        "opt_solver_used": str(opt_solver_used),
        "iterations": solver_iters,
        "initial_mse": mse0,
        "mse_after_blocks": float(mse_after_rounds[-1] if mse_after_rounds else mse0),
        "mse_after_rounds": [float(x) for x in mse_after_rounds],
        "mse_cut_edges_before_polish": float(mse_cut_before_polish),
        "mse_cut_edges_after_polish": float(mse_cut_after_polish),
        "mse_internal_edges_before_polish": float(mse_internal_before_polish),
        "mse_internal_edges_after_polish": float(mse_internal_after_polish),
        "final_mse": mse_final,
        "target_mse": cfg.target_mse,
        "blocks": block_diag_list,
        "timing_s": {
            "build_s": float(t_build_s),
            "partition_s": float(t_partition_s),
            "probe_s": float(probe_time_total_s),
            "fit_s": float(fit_time_total_s),
            "solve_s": float(solve_time_total_s),
            "stage3_s": float(t_stage3_s),
            "stage4_s": float(t_stage4_s),
            "polish_probe_s": float(polish_probe_time_s),
            "polish_fit_s": float(polish_fit_time_s),
            "polish_solve_s": float(polish_solve_time_s),
            "sequential_est_s": float(time_sequential_est_s),
            "parallel_equivalent_s": float(time_parallel_equivalent_s),
        },
        "effort": effort,
        "physics": {"lam0_nm": phys.lam0_nm, "n_eff": phys.n_eff},
    }

    log_kv("MSE after blocks", f"{result['mse_after_blocks']:.2e}")
    log_kv("Final MSE", f"{result['mse_final']:.2e}")
    log_kv("Probes (total)", result["probe_count"])
    log_kv("Probe rounds (eff)", result["probe_rounds_effective"])
    log_kv("HW writes", result["hw_write_count"])
    log_kv("Solver iterations", result["solver_iter_count"])
    log_kv("Walltime (s)", f"{result['walltime']:.3f}")
    return result
