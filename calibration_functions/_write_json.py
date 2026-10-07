"""_write_json extracted from the calibration experiment runner."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from typing import Dict
import json

from ._jsonable import _jsonable


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(_jsonable(payload), fh, indent=2, sort_keys=True)
        fh.write("\n")
