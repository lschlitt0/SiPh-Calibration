"""_git_commit_hash extracted from the calibration experiment runner."""

from __future__ import annotations

from pathlib import Path
from typing import Optional
import subprocess


def _git_commit_hash(repo_dir: Path) -> Optional[str]:
    try:
        out = subprocess.check_output(
            ["git", "-C", str(repo_dir), "rev-parse", "HEAD"],
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except Exception:
        return None
    return out or None
