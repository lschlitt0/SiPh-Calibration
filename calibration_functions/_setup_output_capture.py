"""_setup_output_capture extracted from the calibration experiment runner."""

from __future__ import annotations

from pathlib import Path
from typing import Optional
from typing import TextIO
from typing import Tuple
import sys

from .models import TeeStream


def _setup_output_capture(log_path: Path) -> Tuple[Optional[TextIO], TextIO, TextIO]:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_fh = log_path.open("w", encoding="utf-8")
    stdout_orig = sys.stdout
    stderr_orig = sys.stderr
    sys.stdout = TeeStream(stdout_orig, log_fh)
    sys.stderr = TeeStream(stderr_orig, log_fh)
    return log_fh, stdout_orig, stderr_orig
