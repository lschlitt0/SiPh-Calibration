"""build_ring_hypergraph extracted from the calibration experiment runner."""

from __future__ import annotations

from typing import List
import numpy as np

from ._ring_cross_talk_matrix import _ring_cross_talk_matrix
from .models import Hyperedge
from .models import Hypergraph


def build_ring_hypergraph(ring_count: int, cross_talk_level: float) -> Hypergraph:
    """
    Build a simple weighted hypergraph from the ring cross-talk model.

    Vertices correspond to rings. Hyperedges are pairwise couplings weighted
    by the cross-talk magnitude.
    """
    n = int(ring_count)
    if n <= 0:
        raise ValueError("ring_count must be >= 1")
    C = _ring_cross_talk_matrix(n, float(cross_talk_level))
    edges: List[Hyperedge] = []
    for i in range(n):
        for j in range(i + 1, n):
            w = float(C[i, j])
            if w <= 0.0:
                continue
            edges.append(Hyperedge(pins=(i, j), weight=w))
    v_weights = np.ones(n, dtype=float)
    return Hypergraph(n_vertices=n, edges=edges, v_weights=v_weights)
