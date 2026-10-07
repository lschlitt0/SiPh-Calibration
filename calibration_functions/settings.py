"""Import-time verbosity and repository-relative output locations."""

from __future__ import annotations

from pathlib import Path
import os

from ._env_bool import _env_bool


VERBOSE = _env_bool("CAL_VERBOSE", True)


# Resolve paths beside the CLI, not inside the extracted-function directory.
SCRIPT_DIR = Path(__file__).resolve().parents[1]


PROJECT_ROOT_DIR = SCRIPT_DIR


PAPER_ROOT_DIR = SCRIPT_DIR


RESULTS_DIR = Path(os.getenv("CAL_RESULTS_DIR", PAPER_ROOT_DIR / "results")).resolve()


PAPER_DATA_DIR = (RESULTS_DIR / "paper_data").resolve()


# CAL_RESULTS_DIR controls the default and secondary paper exports.
# --results-dir changes the main run destination only.
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
