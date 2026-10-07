"""_discover_paper_root_dir extracted from the calibration experiment runner."""

from __future__ import annotations

from pathlib import Path


def _discover_paper_root_dir(project_root: Path) -> Path:
    """Locate the live manuscript folder after repo reorganizations."""
    candidates = [project_root / "Paper_Calibration", project_root]
    for candidate in candidates:
        if (candidate / "calibrationPaper_v5.tex").exists() and (candidate / "data").is_dir():
            return candidate.resolve()
    return (project_root / "Paper_Calibration").resolve()
