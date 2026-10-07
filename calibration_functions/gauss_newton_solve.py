"""gauss_newton_solve extracted from the calibration experiment runner."""

from __future__ import annotations

from typing import Callable
from typing import Optional
from typing import Tuple
import numpy as np

from ._solve_qp_docplex import _solve_qp_docplex
from .models import MetricCounters


def gauss_newton_solve(
    predict: Callable[[np.ndarray], np.ndarray],
    jacobian: Callable[[np.ndarray], np.ndarray],
    z_init: np.ndarray,
    y_target: np.ndarray,
    z_min: np.ndarray,
    z_max: np.ndarray,
    max_slew: np.ndarray,
    *,
    trust_radius: Optional[float] = None,
    mu: float = 1e-3,
    iters: int = 20,
    step_solver: str = "linear",
    callback: Optional[Callable[..., None]] = None,
    metrics: Optional[MetricCounters] = None,
) -> Tuple[np.ndarray, int, float]:
    """Reduce modeled residual norm with damped Gauss-Newton steps.

    predict(z) returns p residuals, jacobian(z) a (p, m) Jacobian, and y_target
    the p-component target. z_init, z_min, z_max, and max_slew have m components
    in command units. max_slew limits changes per iteration, not per second.
    trust_radius restricts an axis-aligned box around the initial command.

    The linear path solves damped normal equations and clips the step; DOcplex
    solves a bounded quadratic subproblem. Up to six trials increase damping
    and shrink the local trust box until a lower modeled residual norm is found.
    Only strictly improving candidates are accepted. Stops on no improvement,
    step norm < 1e-6, residual norm < 1e-12, or iters iterations.

    Returns (z_final, iterations_used, last_step_norm). A zero last_step_norm
    can indicate failure to improve, not achievement of the target. Acceptance
    uses the surrogate, with no independent noisy plant measurement. The caller
    is responsible for consistent shapes, finite inputs, and feasible bounds.
    """
    z = z_init.copy()
    z0 = z_init.copy()
    last_du_norm = float("inf")
    mu_cur = float(mu)
    mu_max = 1e6
    mu_min = 1e-8
    mu_increase = 10.0
    mu_decrease = 0.3
    trust_shrink = 0.5
    max_backtracks = 5
    solver_norm = str(step_solver or "").strip().lower()
    use_docplex = solver_norm in ("docplex", "cplex", "auto")
    for it in range(int(iters)):
        y_hat = predict(z)
        r = (y_hat - y_target).reshape(-1)
        J = jacobian(z)

        res_norm = float(np.linalg.norm(r))
        JTJ = J.T @ J
        grad = J.T @ r
        best_candidate: Optional[Tuple[np.ndarray, np.ndarray, np.ndarray, float, float]] = None
        mu_try = float(mu_cur)
        mu_for_next = float(mu_cur)
        local_trust = None if trust_radius is None else float(trust_radius)

        for backtrack in range(max_backtracks + 1):
            A = JTJ + float(mu_try) * np.eye(J.shape[1])
            du: Optional[np.ndarray] = None
            if use_docplex:
                lower = np.maximum(-max_slew, z_min - z)
                upper = np.minimum(max_slew, z_max - z)
                if local_trust is not None:
                    lower = np.maximum(lower, z0 - float(local_trust) - z)
                    upper = np.minimum(upper, z0 + float(local_trust) - z)
                if np.all(lower <= upper):
                    try:
                        du = _solve_qp_docplex(A, grad, lower, upper)
                    except Exception as exc:  # pragma: no cover - optional dependency
                        if solver_norm in ("docplex", "cplex"):
                            raise RuntimeError(f"docplex solve failed: {exc}") from exc
                        du = None
                elif solver_norm in ("docplex", "cplex"):
                    raise RuntimeError("docplex step bounds are infeasible")
            if du is None:
                rhs = -grad
                du = np.linalg.solve(A, rhs)
                du = np.clip(du, -max_slew, max_slew)
                z_next = z + du
                if local_trust is not None:
                    z_next = np.clip(z_next, z0 - float(local_trust), z0 + float(local_trust))
                z_next = np.clip(z_next, z_min, z_max)
                dz = z_next - z
            else:
                z_next = z + du
                dz = du

            r_next = (predict(z_next) - y_target).reshape(-1)
            res_next = float(np.linalg.norm(r_next))
            if not np.isfinite(res_next):
                res_next = float("inf")
            candidate = (z_next, dz, r_next, res_next, float(mu_try))
            if best_candidate is None or res_next < best_candidate[3]:
                best_candidate = candidate

            if res_next < res_norm:
                mu_for_next = max(mu_min, mu_try * mu_decrease)
                break

            mu_try = min(mu_max, mu_try * mu_increase)
            mu_for_next = mu_try
            local_trust = local_trust * trust_shrink if local_trust is not None else None

        if best_candidate is None:
            return z, it, last_du_norm

        z_next, dz, r_used, res_used, mu_used = best_candidate
        if res_used >= res_norm:
            last_du_norm = 0.0
            return z, it, last_du_norm
        mu_cur = float(min(mu_max, max(mu_min, mu_for_next)))

        if metrics is not None:
            metrics.solver_iter_count += 1

        if callback is not None:
            callback(
                it=int(it),
                z=z.copy(),
                z_next=z_next.copy(),
                dz=dz.copy(),
                r=r.copy(),
                J=J.copy(),
                mu=float(mu_used),
            )

        z = z_next

        last_du_norm = float(np.linalg.norm(dz))
        if last_du_norm < 1e-6 or res_used < 1e-12:
            return z, it + 1, last_du_norm

    return z, int(iters), last_du_norm
