"""fit_surrogate_with_trust_region extracted from the calibration experiment runner."""

from __future__ import annotations

from typing import Callable
from typing import List
from typing import Optional
from typing import Tuple
import numpy as np

from ._default_cross_terms import _default_cross_terms
from .models import PolyRidgeSurrogate
from .models import SurrogateFitReport


def fit_surrogate_with_trust_region(
    sampler: Callable[[float, int], Tuple[np.ndarray, np.ndarray, np.ndarray]],
    *,
    z0: np.ndarray,
    lam: float,
    target_val_mse: float,
    seed: int,
    max_retries: int = 4,
    cross_terms: Optional[List[Tuple[int, int]]] = None,
    initial_trust_radius: float = 0.20,
    min_samples: Optional[int] = None,
) -> Tuple[PolyRidgeSurrogate, SurrogateFitReport]:
    """Fit and validate local ridge models from a caller-supplied probing function.

    sampler(radius, n_samples) returns Z (K, m), Y (K, p), and edge identifiers
    (unused here). Mesh callers use clipped Hadamard-coded command perturbations.
    Each attempt reserves max(1, floor(0.2*K)) shuffled samples for validation.
    Supplied nonempty cross terms are active initially; otherwise adjacent cross
    terms can be added after the first failed affine fit. Further retries halve
    the radius and increase requested samples.

    Returns (surrogate, report), stopping at target_val_mse or max_retries.
    If no attempt meets the target, the lowest-validation-MSE model is returned
    without a failure flag; callers must compare report.val_mse with the target.
    The held-out MSE is a fit diagnostic, not a prediction uncertainty bound.
    """
    rng = np.random.default_rng(int(seed))
    trust_radius = float(initial_trust_radius)
    base_samples = max(16, 4 * int(z0.size))
    if min_samples is not None:
        base_samples = max(base_samples, int(min_samples))
    n_samples = int(base_samples)
    provided_cross_terms = list(cross_terms) if cross_terms else None
    use_cross_terms = bool(provided_cross_terms)
    total_samples = 0

    best: Optional[Tuple[PolyRidgeSurrogate, SurrogateFitReport]] = None
    for attempt in range(int(max_retries)):
        Z, Y, _ = sampler(trust_radius, n_samples)
        if Z.shape[0] < 4:
            raise ValueError("sampler must return >= 4 samples")
        total_samples += int(Z.shape[0])

        perm = rng.permutation(Z.shape[0])
        Z = Z[perm]
        Y = Y[perm]
        n_val = max(1, int(0.2 * Z.shape[0]))
        Z_tr, Y_tr = Z[n_val:], Y[n_val:]
        Z_va, Y_va = Z[:n_val], Y[:n_val]

        cross_terms_sel = (
            provided_cross_terms if provided_cross_terms is not None else _default_cross_terms(int(z0.size))
        )
        cross_terms_active = cross_terms_sel if use_cross_terms else []
        surrogate = PolyRidgeSurrogate(cross_terms=cross_terms_active, lam=float(lam))
        surrogate.fit(Z_tr, Y_tr, z0=z0)
        pred = np.vstack([surrogate.predict(Z_va[i]) for i in range(Z_va.shape[0])])
        val_mse = float(np.mean((pred - Y_va) ** 2))
        nfeat = 1 + int(z0.size) + len(cross_terms_active)
        report = SurrogateFitReport(
            val_mse=val_mse,
            trust_radius=float(trust_radius),
            n_samples=int(Z.shape[0]),
            total_samples=int(total_samples),
            attempts=int(attempt + 1),
            n_features=int(nfeat),
            cross_terms=len(cross_terms_active),
        )

        if best is None or val_mse < best[1].val_mse:
            best = (surrogate, report)

        if val_mse <= float(target_val_mse):
            return surrogate, report

        if not use_cross_terms and cross_terms_sel:
            use_cross_terms = True
        else:
            trust_radius *= 0.5
            n_samples = int(max(base_samples, 1.5 * n_samples, float(min_samples) if min_samples is not None else 0.0))

    assert best is not None
    surrogate_best, report_best = best
    report_best = SurrogateFitReport(
        val_mse=report_best.val_mse,
        trust_radius=report_best.trust_radius,
        n_samples=report_best.n_samples,
        total_samples=int(total_samples),
        attempts=int(max_retries),
        n_features=report_best.n_features,
        cross_terms=report_best.cross_terms,
    )
    return surrogate_best, report_best
