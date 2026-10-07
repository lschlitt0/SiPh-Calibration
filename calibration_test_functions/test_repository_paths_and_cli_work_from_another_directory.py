from __future__ import annotations

from pathlib import Path
import json
import os
import subprocess
import sys
import tempfile
from ._support import REPOSITORY_ROOT

# Root unittest classes bind this function; avoid duplicate pytest collection.
__test__ = False


def test_repository_paths_and_cli_work_from_another_directory(self) -> None:
    """Extraction must not relocate outputs into the implementation package."""
    with tempfile.TemporaryDirectory() as temporary_directory:
        work_dir = Path(temporary_directory)
        output_dir = work_dir / "outputs"
        env = dict(os.environ, CAL_RESULTS_DIR=str(output_dir), CAL_VERBOSE="0", PYTHONUTF8="1")
        code = (
            "import json, sys; "
            "sys.path.insert(0, sys.argv[1]); "
            "import Calibration_v3 as cal; "
            "print(json.dumps({name: str(getattr(cal, name)) for name in "
            "('SCRIPT_DIR', 'PROJECT_ROOT_DIR', 'PAPER_ROOT_DIR', 'RESULTS_DIR', 'PAPER_DATA_DIR')})); "
            "assert cal.CalibrationConfig().results_dir == cal.RESULTS_DIR; "
            "assert cal.build_arg_parser().parse_args([]).results_dir == cal.RESULTS_DIR"
        )
        result = subprocess.run(
            [sys.executable, "-B", "-c", code, str(REPOSITORY_ROOT)],
            cwd=work_dir, env=env, text=True, encoding="utf-8", capture_output=True, check=True,
        )
        paths = json.loads(result.stdout)
        for key in ("SCRIPT_DIR", "PROJECT_ROOT_DIR", "PAPER_ROOT_DIR"):
            self.assertEqual(Path(paths[key]), REPOSITORY_ROOT)
        self.assertEqual(Path(paths["RESULTS_DIR"]), output_dir)
        self.assertEqual(Path(paths["PAPER_DATA_DIR"]), output_dir / "paper_data")
        help_result = subprocess.run(
            [sys.executable, "-B", str(REPOSITORY_ROOT / "Calibration_v3.py"), "--help"],
            cwd=work_dir, env=env, text=True, encoding="utf-8", capture_output=True, check=True,
        )
        self.assertIn("--results-dir", help_result.stdout)
        self.assertIn("--paper-profile", help_result.stdout)
