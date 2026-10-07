"""balanced_kway_hypergraph_partition extracted from the calibration experiment runner."""

from __future__ import annotations

from typing import List
from typing import Optional
import numpy as np

from .models import Hypergraph
from .models import PartitionResult


def balanced_kway_hypergraph_partition(
    hg: Hypergraph,
    k: int,
    eps: float,
    *,
    seed: int,
    max_passes: int = 20,
) -> PartitionResult:
    """Greedily reduce the weighted connectivity cut using single-vertex moves.

    The objective is sum_e weight[e] * (number_of_blocks[e] - 1). Initialization
    fills blocks in vertex order; seeded permutations determine refinement order.
    Moves must strictly decrease the objective and respect the destination weight
    limit (1 + eps) * total_weight / k. Refinement stops after max_passes or when
    no improving move remains.

    Returns assignments, objective, cut edges, boundary vertices, and block weights.
    This heuristic does not guarantee a globally optimal or balanced result:
    initial packing can exceed the limit, especially in the final block. Inspect
    hg.check_balance(result.part, k, eps) for each chosen graph/configuration.
    """
    k = int(k)
    if k <= 0:
        raise ValueError("k must be >= 1")
    if hg.n_vertices <= 0:
        raise ValueError("hypergraph must have >= 1 vertex")
    if hg.v_weights.shape != (hg.n_vertices,):
        raise ValueError("v_weights must be shape (n_vertices,)")

    rng = np.random.default_rng(int(seed))
    total_w = float(hg.v_weights.sum())
    limit = (1.0 + float(eps)) * (total_w / float(k))

    # Index-order packing preserves locality in the grid numbering. The last
    # block receives all remaining vertices, so feasibility must be checked later.
    part = -np.ones(hg.n_vertices, dtype=int)
    block_w = np.zeros(k, dtype=float)
    b = 0
    for v in range(hg.n_vertices):
        wv = float(hg.v_weights[v])
        if b < k - 1 and block_w[b] + wv > limit:
            b += 1
        part[v] = b
        block_w[b] += wv

    # Precompute incidence and per-edge block counts for fast deltas.
    edges_of_v: List[List[int]] = [[] for _ in range(hg.n_vertices)]
    for ei, e in enumerate(hg.edges):
        for v in e.pins:
            edges_of_v[int(v)].append(ei)

    edge_counts = np.zeros((len(hg.edges), k), dtype=int)
    for ei, e in enumerate(hg.edges):
        for v in e.pins:
            edge_counts[ei, part[int(v)]] += 1

    def _edge_lambda(ei: int) -> int:
        return int(np.count_nonzero(edge_counts[ei]))

    weights_e = np.array([float(e.weight) for e in hg.edges], dtype=float)
    lambdas = np.array([_edge_lambda(ei) for ei in range(len(hg.edges))], dtype=int)
    objective = float(np.sum(weights_e * (lambdas - 1)))

    def _delta_move(v: int, a: int, b: int) -> float:
        delta = 0.0
        for ei in edges_of_v[v]:
            ca = edge_counts[ei, a]
            cb = edge_counts[ei, b]
            lam_before = lambdas[ei]
            lam_after = lam_before
            if ca == 1:
                lam_after -= 1
            if cb == 0:
                lam_after += 1
            delta += weights_e[ei] * (lam_after - lam_before)
        return float(delta)

    # Local refinement: single-vertex moves that improve objective while keeping balance.
    for _ in range(int(max_passes)):
        improved = False
        for v in rng.permutation(hg.n_vertices):
            a = int(part[v])
            wv = float(hg.v_weights[v])
            best_b: Optional[int] = None
            best_delta = 0.0
            for b in range(k):
                if b == a:
                    continue
                if block_w[b] + wv > limit:
                    continue
                delta = _delta_move(int(v), a, b)
                if delta < best_delta:
                    best_delta = delta
                    best_b = b
            if best_b is None:
                continue

            b = int(best_b)
            part[v] = b
            block_w[a] -= wv
            block_w[b] += wv
            for ei in edges_of_v[int(v)]:
                edge_counts[ei, a] -= 1
                edge_counts[ei, b] += 1
                lambdas[ei] = _edge_lambda(ei)
            objective += best_delta
            improved = True

        if not improved:
            break

    cut_edges = hg.cut_hyperedges(part)
    boundary = hg.boundary_vertices(part)
    return PartitionResult(
        part=part,
        objective=float(objective),
        cut_edges=cut_edges,
        boundary=boundary,
        block_weights=block_w.copy(),
    )
