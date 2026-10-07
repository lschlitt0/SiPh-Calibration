"""build_toy_mesh_plant extracted from the calibration experiment runner."""

from __future__ import annotations

from typing import List
import numpy as np

from .models import Hypergraph
from .models import ToyMeshPlant


def build_toy_mesh_plant(hg: Hypergraph, *, seed: int) -> ToyMeshPlant:
    """Draw seeded target commands and polynomial coupling coefficients for hg.

    The quadratic matrices are symmetrized but not constrained to be positive
    definite. The resulting calibration residual problem need not be convex.
    """
    rng = np.random.default_rng(int(seed))
    u_star = rng.uniform(-0.4, 0.4, size=hg.n_vertices).astype(float)

    lin: List[np.ndarray] = []
    quad: List[np.ndarray] = []
    temp_gain = rng.uniform(-0.05, 0.05, size=len(hg.edges)).astype(float)
    for e in hg.edges:
        m = len(e.pins)
        lin.append(rng.normal(scale=1.0, size=m).astype(float))
        Q = rng.normal(scale=0.25, size=(m, m)).astype(float)
        Q = 0.5 * (Q + Q.T)
        quad.append(Q)

    return ToyMeshPlant(
        hg=hg,
        u_star=u_star,
        lin=lin,
        quad=quad,
        temp_gain=temp_gain,
        noise_std=1e-3,
    )
