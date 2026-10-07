"""build_toy_mesh_hypergraph extracted from the calibration experiment runner."""

from __future__ import annotations

from typing import List
import numpy as np

from .models import Hyperedge
from .models import Hypergraph


def build_toy_mesh_hypergraph(mesh_size: int, *, seed: int) -> Hypergraph:
    """
    Stage 1: build weighted hypergraph (toy stand-in).

    Vertices: mesh_size x mesh_size grid of tuners.
    Hyperedges: 2x2 patches (4-way) + L-shaped triplets (3-way) with weights.
    """
    mesh_size = int(mesh_size)
    if mesh_size < 2:
        raise ValueError("mesh_size must be >= 2")
    rng = np.random.default_rng(int(seed))

    def vid(i: int, j: int) -> int:
        return i * mesh_size + j

    n_vertices = mesh_size * mesh_size
    v_weights = 1.0 + 0.25 * rng.random(n_vertices)

    edges: List[Hyperedge] = []
    # 4-way patch hyperedges
    for i in range(mesh_size - 1):
        for j in range(mesh_size - 1):
            pins = (vid(i, j), vid(i + 1, j), vid(i, j + 1), vid(i + 1, j + 1))
            weight = 0.5 + 1.5 * float(rng.random())
            edges.append(Hyperedge(pins=pins, weight=weight))
    # 3-way L-shape hyperedges (adds additional multi-way couplings)
    for i in range(mesh_size - 1):
        for j in range(mesh_size - 1):
            pins = (vid(i, j), vid(i + 1, j), vid(i, j + 1))
            weight = 0.25 + 0.75 * float(rng.random())
            edges.append(Hyperedge(pins=pins, weight=weight))

    return Hypergraph(n_vertices=n_vertices, edges=edges, v_weights=v_weights.astype(float))
