"""log extracted from the calibration experiment runner."""

from __future__ import annotations

import sys

from .settings import VERBOSE


def log(msg: str = "", *, force: bool = False) -> None:
    if VERBOSE or force:
        sys.stdout.write(msg + "\n")
        sys.stdout.flush()
