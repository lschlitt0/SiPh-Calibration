"""_mtkahypar_partition extracted from the calibration experiment runner."""

from __future__ import annotations

import numpy as np

from ._mtkahypar_initializer import _mtkahypar_initializer
from ._mtkahypar_preset import _mtkahypar_preset
from .models import Hypergraph
from .models import PartitionResult


def _mtkahypar_partition(
    hg: Hypergraph,
    k: int,
    eps: float,
    *,
    seed: int,
    weight_scale: int = 1000,
) -> PartitionResult:
    import mtkahypar

    mtk = _mtkahypar_initializer()
    context = mtk.context_from_preset(_mtkahypar_preset())
    context.set_partitioning_parameters(int(k), float(eps), mtkahypar.Objective.KM1)
    mtkahypar.set_seed(int(seed))
    context.logging = False

    scale = max(1, int(weight_scale))
    hyperedges = [[int(v) for v in e.pins] for e in hg.edges]
    edge_weights = [max(1, int(round(float(e.weight) * scale))) for e in hg.edges]
    node_weights = [max(1, int(round(float(w) * scale))) for w in hg.v_weights.tolist()]

    hypergraph = mtk.create_hypergraph(
        context,
        int(hg.n_vertices),
        int(len(hg.edges)),
        hyperedges,
        node_weights,
        edge_weights,
    )
    partitioned = hypergraph.partition(context)

    part = np.array([int(partitioned.block_id(v)) for v in range(hg.n_vertices)], dtype=int)
    if part.shape != (hg.n_vertices,):
        raise RuntimeError("mtkahypar returned invalid partition")

    cut_edges = hg.cut_hyperedges(part)
    boundary = hg.boundary_vertices(part)
    block_w = np.zeros(int(k), dtype=float)
    for i in range(int(k)):
        block_w[i] = float(hg.v_weights[part == i].sum())
    objective = hg.connectivity_cut(part)
    return PartitionResult(
        part=part,
        objective=float(objective),
        cut_edges=cut_edges,
        boundary=boundary,
        block_weights=block_w,
    )
