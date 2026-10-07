"""_partition_palette extracted from the calibration experiment runner."""

from __future__ import annotations

from typing import Any
from typing import List
from typing import Tuple


def _partition_palette(plt: Any) -> List[Tuple[float, float, float, float]]:
    colors: List[Tuple[float, float, float, float]] = []
    for name in ("tab20", "tab20b", "tab20c"):
        cmap = plt.get_cmap(name)
        if hasattr(cmap, "colors"):
            colors.extend(list(cmap.colors))
        else:
            colors.extend([cmap(i / 9.0) for i in range(10)])
    if not colors:
        colors = [(0.2, 0.2, 0.2, 1.0)]
    return colors
