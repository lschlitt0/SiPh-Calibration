"""_mtkahypar_initializer extracted from the calibration experiment runner."""

from __future__ import annotations

from typing import Any
from typing import Optional
import os


_MTK_INITIALIZER: Optional[Any] = None


def _mtkahypar_initializer() -> Any:
    """Initialize the optional shared partitioner with environment-selected threads."""
    global _MTK_INITIALIZER
    if _MTK_INITIALIZER is not None:
        return _MTK_INITIALIZER
    import mtkahypar

    threads_env = os.getenv("KAHYPAR_THREADS") or os.getenv("MTKAHYPAR_THREADS")
    try:
        threads = int(threads_env) if threads_env else int(os.cpu_count() or 1)
    except Exception:
        threads = 1
    _MTK_INITIALIZER = mtkahypar.initialize(max(1, threads))
    return _MTK_INITIALIZER
