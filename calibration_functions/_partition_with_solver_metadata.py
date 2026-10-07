"""_partition_with_solver_metadata extracted from the calibration experiment runner."""

from __future__ import annotations

from pathlib import Path
from typing import Optional
from typing import Tuple

from ._kahypar_partition import _kahypar_partition
from .balanced_kway_hypergraph_partition import balanced_kway_hypergraph_partition
from .log import log
from .models import Hypergraph
from .models import PartitionResult


def _partition_with_solver_metadata(
    hg: Hypergraph,
    k: int,
    eps: float,
    *,
    seed: int,
    solver: str,
    kahypar_config: Optional[Path],
) -> Tuple[PartitionResult, str]:
    solver_norm = str(solver or "").strip().lower()
    if solver_norm in ("", "heuristic", "default", "balanced"):
        return balanced_kway_hypergraph_partition(hg, k, eps, seed=seed), "heuristic"
    if solver_norm == "kahypar":
        return _kahypar_partition(hg, k, eps, seed=seed, config_path=kahypar_config), "kahypar"
    if solver_norm == "auto":
        try:
            return _kahypar_partition(hg, k, eps, seed=seed, config_path=kahypar_config), "kahypar"
        except Exception as exc:  # pragma: no cover - optional dependency/fallback path
            log(f"[partition] falling back to heuristic: {exc}", force=True)
            return balanced_kway_hypergraph_partition(hg, k, eps, seed=seed), "heuristic"
    raise ValueError(f"Unknown partition solver: {solver}")
