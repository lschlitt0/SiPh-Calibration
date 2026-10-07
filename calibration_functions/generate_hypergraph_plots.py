"""generate_hypergraph_plots extracted from the calibration experiment runner."""

from __future__ import annotations

from pathlib import Path

from ._mesh_vertex_positions import _mesh_vertex_positions
from ._plot_hypergraph import _plot_hypergraph
from ._ring_vertex_positions import _ring_vertex_positions
from .build_ring_hypergraph import build_ring_hypergraph
from .build_toy_mesh_hypergraph import build_toy_mesh_hypergraph
from .log import log
from .models import CalibrationConfig
from .partition_hypergraph import partition_hypergraph


def generate_hypergraph_plots(
    run_dir: Path,
    cfg: CalibrationConfig,
    *,
    include_mesh: bool = True,
    include_rings: bool = True,
) -> None:
    """Regenerate and partition model graphs for optional diagnostic PNG exports.

    The ring graph is a coupling visualization; it is not used by the ring
    controllers. Repartitioning may differ from a prior external-solver run.
    """
    if not include_mesh and not include_rings:
        return
    try:
        import matplotlib.pyplot as plt
    except Exception as exc:  # pragma: no cover - plotting optional
        log(f"[plot] skipping hypergraph plots (matplotlib unavailable: {exc})", force=True)
        return

    if include_mesh:
        try:
            hg_mesh = build_toy_mesh_hypergraph(cfg.mesh_size, seed=cfg.seed)
            part_mesh = partition_hypergraph(
                hg_mesh,
                cfg.partitions,
                cfg.balance_eps,
                seed=cfg.seed + 5,
                solver=cfg.partition_solver,
                kahypar_config=cfg.kahypar_config,
            )
            pos_mesh = _mesh_vertex_positions(cfg.mesh_size)
            title = f"Mesh hypergraph (N={cfg.mesh_size}, k={cfg.partitions})"
            _plot_hypergraph(
                hg_mesh,
                part_mesh.part,
                pos_mesh,
                run_dir / "fig_mesh_hypergraph.png",
                title,
                plt=plt,
                boundary=part_mesh.boundary,
            )
        except Exception as exc:
            log(f"[plot] mesh hypergraph failed: {exc}", force=True)

    if include_rings:
        try:
            hg_ring = build_ring_hypergraph(cfg.ring_count, cfg.ring_cross_talk)
            k_ring = max(1, min(int(cfg.partitions), int(hg_ring.n_vertices)))
            part_ring = partition_hypergraph(
                hg_ring,
                k_ring,
                cfg.balance_eps,
                seed=cfg.seed + 11,
                solver=cfg.partition_solver,
                kahypar_config=cfg.kahypar_config,
            )
            pos_ring = _ring_vertex_positions(hg_ring.n_vertices)
            title = (
                f"Ring cross-talk hypergraph (Nr={hg_ring.n_vertices}, k={k_ring}, "
                f"ct={cfg.ring_cross_talk:.2f})"
            )
            _plot_hypergraph(
                hg_ring,
                part_ring.part,
                pos_ring,
                run_dir / "fig_ring_hypergraph.png",
                title,
                plt=plt,
                boundary=part_ring.boundary,
            )
        except Exception as exc:
            log(f"[plot] ring hypergraph failed: {exc}", force=True)
