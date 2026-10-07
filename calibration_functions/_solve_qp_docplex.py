"""_solve_qp_docplex extracted from the calibration experiment runner."""

from __future__ import annotations

from typing import Any
from typing import List
import numpy as np


def _solve_qp_docplex(
    H: np.ndarray,
    f: np.ndarray,
    lower: np.ndarray,
    upper: np.ndarray,
) -> np.ndarray:
    """Solve min_dz 0.5*dz.T*H*dz + f.T*dz with componentwise step bounds.

    Requires DOcplex and a working CPLEX solve runtime. Missing dependencies or
    an absent solution raise an exception; auto fallback is handled by the caller.
    """
    try:
        from docplex.mp.model import Model
    except Exception as exc:  # pragma: no cover - optional dependency
        raise RuntimeError(f"docplex import failed: {exc}") from exc

    n = int(f.size)
    mdl = Model(name="gn_step")
    dz = [
        mdl.continuous_var(lb=float(lower[i]), ub=float(upper[i]), name=f"dz_{i}")
        for i in range(n)
    ]
    quad_terms: List[Any] = []
    for i in range(n):
        h_ii = float(H[i, i])
        if h_ii != 0.0:
            quad_terms.append(0.5 * h_ii * dz[i] * dz[i])
        for j in range(i + 1, n):
            h_ij = float(H[i, j])
            if h_ij != 0.0:
                quad_terms.append(h_ij * dz[i] * dz[j])
    quad: Any = mdl.sum(quad_terms) if quad_terms else 0.0
    lin: Any = mdl.sum(float(f[i]) * dz[i] for i in range(n))
    mdl.minimize(quad + lin)
    sol = mdl.solve(log_output=False)
    if sol is None:
        raise RuntimeError("docplex returned no solution")
    return np.array([float(sol.get_value(var)) for var in dz], dtype=float)
