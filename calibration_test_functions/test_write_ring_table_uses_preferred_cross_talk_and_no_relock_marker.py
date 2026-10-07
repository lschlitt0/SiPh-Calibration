from __future__ import annotations

from pathlib import Path
import tempfile
from ._support import CAL

# Root unittest classes bind this function; avoid duplicate pytest collection.
__test__ = False


def test_write_ring_table_uses_preferred_cross_talk_and_no_relock_marker(self) -> None:
    """Show nonsettling runs as exceeding the simulated control horizon."""
    ring_results = {
        "parallel": [
            {
                "cross_talk_level": 0.0,
                "settle_ms": 111.0,
                "settled_all": True,
                "peak_pm": 1.0,
                "rms_pm": 0.100,
                "probe_count": 10,
            },
            {
                "cross_talk_level": 0.06,
                "settle_ms": 2881.0,
                "settled_all": True,
                "peak_pm": 6.96,
                "rms_pm": 0.015,
                "probe_count": 40000,
            },
        ],
        "scan": {
            "cross_talk_level": 0.06,
            "settle_ms": 5000.0,
            "settled_all": False,
            "control_horizon_s": 5.0,
            "peak_pm": 16.0,
            "rms_pm": 8.054,
            "probe_count": 40000,
        },
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        run_dir = Path(tmpdir)
        CAL.write_ring_table(run_dir, ring_results, preferred_ct=0.06)
        table_text = (run_dir / "table_ring.tex").read_text(encoding="utf-8")

    self.assertIn("parallel & 2881.00 & 6.96 & 0.015 & 40000", table_text)
    self.assertNotIn("parallel & 111.00", table_text)
    self.assertIn("scan & >5000 & 16.00 & 8.054 & 40000", table_text)
