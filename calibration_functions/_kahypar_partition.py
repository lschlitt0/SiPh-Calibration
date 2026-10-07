"""_kahypar_partition extracted from the calibration experiment runner."""

from __future__ import annotations

from pathlib import Path
from typing import List
from typing import Optional
import numpy as np

from ._mtkahypar_partition import _mtkahypar_partition
from .models import Hypergraph
from .models import PartitionResult


def _kahypar_partition(
    hg: Hypergraph,
    k: int,
    eps: float,
    *,
    seed: int,
    config_path: Optional[Path],
    weight_scale: int = 1000,
) -> PartitionResult:
    """Partition with Mt-KaHyPar if importable, otherwise KaHyPar and an INI file.

    Floating node/edge weights are rounded after weight_scale multiplication and
    clamped to at least one for the external solver. Reported objective and block
    weights are recomputed using the original floating weights.
    """
    try:
        import mtkahypar
    except Exception:
        mtkahypar = None

    if mtkahypar is not None:
        return _mtkahypar_partition(hg, k, eps, seed=seed, weight_scale=weight_scale)

    try:
        import kahypar
    except Exception as exc:  # pragma: no cover - optional dependency
        raise RuntimeError(f"kahypar import failed: {exc}") from exc

    if config_path is None:
        raise ValueError("kahypar requires a config path")
    cfg_path = Path(config_path)
    if not cfg_path.exists():
        raise FileNotFoundError(f"kahypar config not found: {cfg_path}")

    hyperedges: List[int] = []
    hyperedge_indices: List[int] = [0]
    for e in hg.edges:
        pins = [int(v) for v in e.pins]
        hyperedges.extend(pins)
        hyperedge_indices.append(len(hyperedges))

    scale = max(1, int(weight_scale))
    edge_weights = [max(1, int(round(float(e.weight) * scale))) for e in hg.edges]
    node_weights = [max(1, int(round(float(w) * scale))) for w in hg.v_weights.tolist()]

    k = int(k)
    hypergraph = kahypar.Hypergraph(
        hg.n_vertices,
        len(hg.edges),
        hyperedge_indices,
        hyperedges,
        k,
        edge_weights,
        node_weights,
    )
    context = kahypar.Context()
    context.loadINIconfiguration(str(cfg_path))
    context.setK(k)
    context.setEpsilon(float(eps))
    context.setSeed(int(seed))
    kahypar.partition(hypergraph, context)

    part = np.array([int(hypergraph.blockID(v)) for v in range(hg.n_vertices)], dtype=int)
    if part.shape != (hg.n_vertices,):
        raise RuntimeError("kahypar returned invalid partition")

    cut_edges = hg.cut_hyperedges(part)
    boundary = hg.boundary_vertices(part)
    block_w = np.zeros(k, dtype=float)
    for i in range(k):
        block_w[i] = float(hg.v_weights[part == i].sum())
    objective = hg.connectivity_cut(part)
    return PartitionResult(
        part=part,
        objective=float(objective),
        cut_edges=cut_edges,
        boundary=boundary,
        block_weights=block_w,
    )
