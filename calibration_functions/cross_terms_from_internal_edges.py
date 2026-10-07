"""cross_terms_from_internal_edges extracted from the calibration experiment runner."""

from __future__ import annotations

from numpy.typing import NDArray
from typing import List
from typing import Optional
from typing import Sequence
from typing import Set
from typing import Tuple
from typing import Union
import numpy as np

from .models import Hypergraph


def cross_terms_from_internal_edges(
    block_vertices: Union[Sequence[int], NDArray[np.int_]],
    internal_edge_ids: Union[Sequence[int], NDArray[np.int_]],
    hg: Hypergraph,
    *,
    max_terms: Optional[int] = None,
) -> List[Tuple[int, int]]:
    """
    Build cross terms aligned to the block’s true couplings:
      - include all unique pin pairs appearing together on an internal hyperedge
      - map global vertex ids to block-local indices
      - cap to at most max_terms features (deterministic order)
    """
    block_vertices_arr = np.asarray(block_vertices, dtype=int).reshape(-1)
    internal_edge_ids_arr = np.asarray(internal_edge_ids, dtype=int).reshape(-1)
    local = {int(v): idx for idx, v in enumerate(block_vertices_arr)}
    pairs: Set[Tuple[int, int]] = set()
    for ei in internal_edge_ids_arr:
        e = hg.edges[int(ei)]
        pins = [local[int(v)] for v in e.pins if int(v) in local]
        for a in range(len(pins)):
            for b in range(a + 1, len(pins)):
                i, j = pins[a], pins[b]
                pairs.add((min(i, j), max(i, j)))
    pairs_sorted = sorted(pairs)
    if max_terms is not None and len(pairs_sorted) > int(max_terms):
        return pairs_sorted[: int(max_terms)]
    return pairs_sorted
