from __future__ import annotations

from pathlib import Path
import tempfile
from ._support import CAL

# Root unittest classes bind this function; avoid duplicate pytest collection.
__test__ = False


def test_discover_paper_root_dir_prefers_nested_manuscript_folder(self) -> None:
    """Preserve the legacy manuscript-discovery helper's search order."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        nested_paper = project_root / "Paper_Calibration"
        (nested_paper / "data").mkdir(parents=True)
        (nested_paper / "calibrationPaper_v5.tex").write_text("% test\n", encoding="utf-8")

        discovered = CAL._discover_paper_root_dir(project_root)

    self.assertEqual(discovered, nested_paper.resolve())
