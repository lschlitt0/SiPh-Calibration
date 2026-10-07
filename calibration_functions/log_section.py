"""log_section extracted from the calibration experiment runner."""

from __future__ import annotations

from .log import log


def log_section(title: str) -> None:
    line = "─" * max(0, 76 - len(title))
    log(f"{title} {line}", force=True)
