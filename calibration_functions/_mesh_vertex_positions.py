"""_mesh_vertex_positions extracted from the calibration experiment runner."""

from __future__ import annotations

import numpy as np


def _mesh_vertex_positions(mesh_size: int) -> np.ndarray:
    mesh_size = int(mesh_size)
    positions = np.zeros((mesh_size * mesh_size, 2), dtype=float)
    for i in range(mesh_size):
        for j in range(mesh_size):
            v = i * mesh_size + j
            positions[v] = (float(j), float(mesh_size - 1 - i))
    return positions
