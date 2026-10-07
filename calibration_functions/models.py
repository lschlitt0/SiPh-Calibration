"""Shared calibration configurations, plant models, and result containers."""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from numpy.typing import NDArray
from pathlib import Path
from typing import Dict
from typing import List
from typing import Optional
from typing import Sequence
from typing import Set
from typing import TextIO
from typing import Tuple
import math
import numpy as np

from .settings import RESULTS_DIR


class TeeStream:
    def __init__(self, *streams: TextIO) -> None:
        self._streams = streams

    def write(self, data: str) -> int:
        for stream in self._streams:
            stream.write(data)
        return len(data)

    def flush(self) -> None:
        for stream in self._streams:
            stream.flush()

    def isatty(self) -> bool:
        return any(getattr(stream, "isatty", lambda: False)() for stream in self._streams)

    @property
    def encoding(self) -> str:
        for stream in self._streams:
            enc = getattr(stream, "encoding", None)
            if enc:
                return enc
        return "utf-8"


@dataclass
class PhysicsParams:
    """Descriptive device constants retained with experiment results.

    Wavelength is in nm, lengths in um, dndT in K^-1, and responsivity in A/W;
    n_eff is dimensionless. These fields do not enter the toy plant equations.
    Changing them alone does not change the simulated calibration dynamics.
    """

    lam0_nm: float = 1550.0
    n_eff: float = 2.40
    L_ps_um: float = 200.0
    L_ring_um: float = 2.0 * math.pi * 10.0
    dndT: float = 1.8e-4
    pd_responsivity_A_per_W: float = 0.9


@dataclass
class CalibrationConfig:
    """Experiment settings shared by the CLI and callable workflows.

    mesh_size is the side length of an N-by-N tuner grid; partitions is the
    number of mesh blocks. ring_cross_talk and balance_eps are dimensionless.
    drift_K is a temperature increment in K. target_mse is the mean squared
    mesh residual in abstract model units, evaluated without probe noise.
    Tune-and-check step and gain act on abstract mesh commands. Ring gains,
    sample rates, actuator bounds, and thermal coefficients are local constants
    inside the two simulate_ring_* functions. seed controls seeded random draws.
    """
    mesh_size: int = 16
    ring_count: int = 8
    ring_cross_talk: float = 0.06
    ring_cross_talk_sweep: Optional[str] = "0,0.03,0.06,0.10,0.15"
    partitions: int = 4
    partition_solver: str = "auto"
    kahypar_config: Optional[Path] = None
    balance_eps: float = 0.05
    polishing_rounds: int = 2
    outer_rounds: int = 2
    opt_solver: str = "auto"
    mesh_baselines: str = "dfc,global,tunecheck"
    ring_baselines: str = "parallel,scan"
    tune_check_rounds: int = 3
    tune_check_subset: float = 0.3
    tune_check_step: float = 0.05
    tune_check_lr: float = 0.5
    drift_K: float = 0.5
    target_mse: float = 1e-4
    seed: int = 7
    sweep: Optional[str] = None
    results_dir: Path = field(default=RESULTS_DIR)


@dataclass
class MetricCounters:
    """Count simulated probes, command commits, element changes, and solver steps.

    These are accounting conventions rather than hardware measurements. A mesh
    probe samples a complete residual vector, while ring probes count individual
    ring samples. One mesh block commit may touch many elements. Time fields are
    seconds: mesh routines record compute durations; ring routines assign the
    simulated horizon to probe/solve time. Cross-method rates require this context.
    """

    probe_count: int = 0
    hw_write_count: int = 0
    hw_element_touch_count: int = 0
    solver_iter_count: int = 0
    probe_time_s: float = 0.0
    solve_time_s: float = 0.0

    def record_probes(self, n: int, *, time_s: float = 0.0) -> None:
        self.probe_count += int(n)
        self.probe_time_s += float(max(0.0, time_s))

    def record_hw_write(self, n: int = 1, *, element_touches: Optional[int] = None) -> None:
        self.hw_write_count += int(n)
        if element_touches is None:
            element_touches = int(n)
        self.hw_element_touch_count += int(max(0, element_touches))

    def record_solver_iters(self, n: int, *, time_s: float = 0.0) -> None:
        self.solver_iter_count += int(n)
        self.solve_time_s += float(max(0.0, time_s))

    def derived(self, n_tuners: int, walltime_s: float) -> Dict[str, float]:
        n_tuners = max(1, int(n_tuners))
        walltime_s = float(max(1e-9, walltime_s))
        return {
            "probes_per_tuner": float(self.probe_count) / float(n_tuners),
            "hw_writes_per_tuner": float(self.hw_write_count) / float(n_tuners),
            "hw_element_touches_per_tuner": float(self.hw_element_touch_count) / float(n_tuners),
            "seconds_per_probe": float(self.probe_time_s) / float(max(1, self.probe_count)),
            "seconds_per_solver_iter": float(self.solve_time_s) / float(max(1, self.solver_iter_count)),
            "probes_per_second": float(self.probe_count) / walltime_s,
        }


@dataclass(frozen=True)
class Hyperedge:
    pins: Sequence[int]  # vertex indices
    weight: float  # w_e(e)


@dataclass
class Hypergraph:
    """
    Minimal weighted hypergraph model for the DfC pipeline.

    Vertices correspond to tuners (or tight tuner groups). Hyperedges model
    multi-way coupling relations. Objective + balance constraints follow Eq. (4).
    """

    n_vertices: int
    edges: List[Hyperedge]
    v_weights: np.ndarray  # w_v(v), shape (n_vertices,)

    def connectivity_cut(self, part: np.ndarray) -> float:
        """
        Paper objective: sum_e w_e(e) * (lambda(e) - 1),
        where lambda(e) is number of blocks spanned by hyperedge e.
        """
        total = 0.0
        for e in self.edges:
            blocks = {int(part[v]) for v in e.pins}
            total += float(e.weight) * (len(blocks) - 1)
        return float(total)

    def cut_hyperedges(self, part: np.ndarray) -> List[int]:
        """Indices of cut hyperedges (lambda(e) > 1)."""
        cut: List[int] = []
        for idx, e in enumerate(self.edges):
            blocks = {int(part[v]) for v in e.pins}
            if len(blocks) > 1:
                cut.append(idx)
        return cut

    def boundary_vertices(self, part: np.ndarray) -> Set[int]:
        """Boundary tuners = vertices incident to any cut hyperedge."""
        boundary: Set[int] = set()
        for e in self.edges:
            blocks = {int(part[v]) for v in e.pins}
            if len(blocks) > 1:
                boundary.update(e.pins)
        return boundary

    def check_balance(self, part: np.ndarray, k: int, eps: float) -> bool:
        """
        Balance constraint:
          sum_{v in B_i} w_v(v) <= (1+eps) * (1/k) * sum_V w_v(v)
        """
        total = float(self.v_weights.sum())
        limit = (1.0 + float(eps)) * (total / float(k))
        for i in range(int(k)):
            if float(self.v_weights[part == i].sum()) > limit:
                return False
        return True


@dataclass
class PartitionResult:
    part: np.ndarray  # (n_vertices,) block id in [0,k)
    objective: float
    cut_edges: List[int]
    boundary: Set[int]
    block_weights: np.ndarray  # (k,)


@dataclass
class PolyRidgeSurrogate:
    """Model residual vectors using centered affine and selected bilinear features.

    The feature vector is [1, z-z0, (z[a]-z0[a])*(z[b]-z0[b])]. Default coupling
    pairs have distinct indices, so squared self terms of the toy plant are not
    included. lam regularizes every coefficient, including the intercept. Inputs
    and outputs retain the sampler's units; no feature standardization is applied.
    """

    cross_terms: List[Tuple[int, int]]
    lam: float
    beta: Optional[np.ndarray] = None  # (n_features, p_outputs)
    z0: Optional[np.ndarray] = None  # center for local model, shape (m,)

    def _features(self, z: np.ndarray) -> np.ndarray:
        assert self.z0 is not None
        dz = (z - self.z0).reshape(-1)
        feats = [np.array([1.0]), dz]
        if self.cross_terms:
            feats.append(np.array([dz[a] * dz[b] for (a, b) in self.cross_terms], dtype=float))
        return np.concatenate(feats, axis=0)

    def fit(self, Z: np.ndarray, Y: np.ndarray, *, z0: np.ndarray) -> None:
        """Fit beta to Z inputs (K, m) and Y residuals (K, p), centered at z0 (m,).

        Solves (X.T @ X + lam * I) beta = X.T @ Y. Normal equations can amplify
        conditioning problems; a positive ridge reduces but does not eliminate this
        risk. Singular solves propagate as NumPy exceptions.
        """
        self.z0 = z0.copy()
        X = np.vstack([self._features(Z[k]) for k in range(Z.shape[0])])  # (K, n_features)
        XtX = X.T @ X
        nfeat = XtX.shape[0]
        self.beta = np.linalg.solve(XtX + float(self.lam) * np.eye(nfeat), X.T @ Y)

    def predict(self, z: np.ndarray) -> np.ndarray:
        """Return the p modeled residuals at one m-component input z."""
        assert self.beta is not None
        x = self._features(z)
        return x @ self.beta

    def jacobian(self, z: np.ndarray) -> np.ndarray:
        """Return the analytic residual Jacobian dF/dz with shape (p, m).

        Entries have output-residual units per input-command unit.
        """
        assert self.beta is not None and self.z0 is not None
        m = int(z.size)
        dz = (z - self.z0).reshape(-1)

        # Feature layout: [1 | dz(0..m-1) | cross_terms]
        p = int(self.beta.shape[1])
        J = np.zeros((p, m), dtype=float)

        # linear part
        lin_start = 1
        lin_end = 1 + m
        W_lin = self.beta[lin_start:lin_end, :]  # (m, p)
        J += W_lin.T  # (p, m)

        # cross terms
        ct_start = lin_end
        for idx, (a, b) in enumerate(self.cross_terms):
            w = self.beta[ct_start + idx, :]  # (p,)
            J[:, a] += w * dz[b]
            J[:, b] += w * dz[a]

        return J


@dataclass
class SurrogateFitReport:
    """Validation error, model size, radius, and probe accounting for a selected fit.

    val_mse is mean squared held-out prediction error. n_samples belongs to the
    selected fit; total_samples includes all retry attempts, including rejected fits.
    """
    val_mse: float
    trust_radius: float
    n_samples: int
    total_samples: int
    attempts: int
    n_features: int
    cross_terms: int


@dataclass
class ToyMeshPlant:
    """Synthetic coupled residual model over an N-by-N tuner graph.

    u and u_star are abstract commands, bounded by u_min/u_max. Each hyperedge
    combines linear and quadratic deviations from u_star with a global mean(u)
    context term and independent Gaussian measurement noise. Residuals have
    abstract model units; the variable temp is not a temperature in K. In general,
    u_star is not a zero-residual solution because the context term remains.
    """
    hg: Hypergraph
    u_star: np.ndarray  # (n_vertices,)
    lin: List[np.ndarray]  # per-edge linear coeffs aligned to pins
    quad: List[np.ndarray]  # per-edge symmetric quadratic coeffs (len(pins), len(pins))
    temp_gain: np.ndarray  # per-edge coupling to global temp/context
    noise_std: float = 1e-3

    u_min: float = -1.0
    u_max: float = 1.0

    def bounds(self) -> Tuple[np.ndarray, np.ndarray]:
        return (
            np.full(self.hg.n_vertices, float(self.u_min), dtype=float),
            np.full(self.hg.n_vertices, float(self.u_max), dtype=float),
        )

    def measure(self, u: np.ndarray, *, rng: np.random.Generator) -> np.ndarray:
        """Return one residual per hyperedge for command vector u (n_vertices,).

        For pins of edge e, d = u[pins] - u_star[pins], and the noiseless response is
        lin[e] @ d + 0.5*d.T @ quad[e] @ d + temp_gain[e]*mean(u). The supplied RNG
        adds noise_std Gaussian noise when enabled. This method does not clip u.
        """
        u = u.reshape(-1)
        du = u - self.u_star
        temp = float(np.mean(u))
        y = np.zeros(len(self.hg.edges), dtype=float)
        for ei, e in enumerate(self.hg.edges):
            pins = np.asarray(e.pins, dtype=int)
            d = du[pins]
            val = float(self.lin[ei] @ d)
            val += 0.5 * float(d.T @ self.quad[ei] @ d)
            val += float(self.temp_gain[ei]) * temp
            if self.noise_std > 0.0:
                val += float(self.noise_std) * float(rng.standard_normal())
            y[ei] = val
        return y


@dataclass
class BlockModel:
    """Local surrogate and diagnostics for one partition's internal hyperedges."""
    block_id: int
    vertices: NDArray[np.int_]  # global vertex ids in this block
    edges_internal: NDArray[np.int_]  # hyperedge indices fully within this block
    surrogate: PolyRidgeSurrogate
    report: SurrogateFitReport
    jacobian_cond: float


@dataclass
class IncrementalPID:
    """Discrete incremental PID state with command slew and saturation limits.

    step uses u_prev + Kp*(e-e_prev) + Ki*e + Kd*((e-e_prev)-de_prev).
    Gains are per controller call: no explicit dt scaling is applied. For ring
    detuning errors in pm, gains map pm to unitless command increments. History
    is updated after clipping, with no separate integral anti-windup state.
    """
    Kp: float
    Ki: float
    Kd: float
    u_min: float
    u_max: float
    du_max: float

    e_prev: float = 0.0
    de_prev: float = 0.0
    u_prev: float = 0.0

    def step(self, e: float) -> float:
        """Update controller history and return the clipped command for signed error e."""
        de = float(e - self.e_prev)
        d2e = float(de - self.de_prev)
        u = self.u_prev + self.Kp * de + self.Ki * float(e) + self.Kd * d2e
        u = float(np.clip(u, self.u_prev - self.du_max, self.u_prev + self.du_max))
        u = float(np.clip(u, self.u_min, self.u_max))
        self.de_prev = de
        self.e_prev = float(e)
        self.u_prev = u
        return u
