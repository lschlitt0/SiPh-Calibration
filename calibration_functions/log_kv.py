"""log_kv extracted from the calibration experiment runner."""

from __future__ import annotations

from typing import Any

from .log import log


def log_kv(key: str, value: Any) -> None:
    log(f"{key:>28}: {value}", force=True)
