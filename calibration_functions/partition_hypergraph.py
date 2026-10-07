"""partition_hypergraph extracted from the calibration experiment runner."""

from __future__ import annotations

from pathlib import Path
from typing import Optional
import os

from ._kahypar_partition import _kahypar_partition
from .balanced_kway_hypergraph_partition import balanced_kway_hypergraph_partition
from .log import log
from .models import Hypergraph
from .models import PartitionResult


def partition_hypergraph(
    hg: Hypergraph,
    k: int,
    eps: float,
    *,
    seed: int,
    solver: str,
    kahypar_config: Optional[Path],
) -> PartitionResult:
    """Dispatch partitioning; auto logs external-solver failures and uses the heuristic."""
    solver_norm = str(solver or "").strip().lower()
    kahypar_cfg = kahypar_config
    if kahypar_cfg is None:
        env_cfg = os.getenv("KAHYPAR_CONFIG")
        if env_cfg:
            kahypar_cfg = Path(env_cfg)
    if solver_norm in ("", "heuristic", "default", "balanced"):
        return balanced_kway_hypergraph_partition(hg, k, eps, seed=seed)
    if solver_norm == "kahypar":
        return _kahypar_partition(hg, k, eps, seed=seed, config_path=kahypar_cfg)
    if solver_norm == "auto":
        try:
            return _kahypar_partition(hg, k, eps, seed=seed, config_path=kahypar_cfg)
        except Exception as exc:  # pragma: no cover - fallback path
            log(f"[partition] falling back to heuristic: {exc}", force=True)
            return balanced_kway_hypergraph_partition(hg, k, eps, seed=seed)
    raise ValueError(f"Unknown partition solver: {solver}")
