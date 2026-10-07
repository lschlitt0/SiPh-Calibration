from __future__ import annotations

from ._support import CAL

# Root unittest classes bind this function; avoid duplicate pytest collection.
__test__ = False


def test_ring_probe_rounds_match_trace_length(self) -> None:
    """Count ring readouts separately from simultaneous sampling rounds."""
    cfg = CAL.CalibrationConfig(ring_count=4, ring_cross_talk=0.06, ring_cross_talk_sweep=None, seed=7)
    phys = CAL.PhysicsParams()

    parallel = CAL.simulate_ring_bank(cfg, phys, capture_traces=False)
    scan = CAL.simulate_ring_scan(cfg, phys, capture_traces=False)

    for result in (parallel, scan):
        trace_len = int(result["trace_len"])
        rings = int(result["rings"])
        self.assertEqual(int(result["probe_count"]), rings * trace_len)
        self.assertEqual(int(result["probe_rounds_effective"]), trace_len)
    self.assertEqual(parallel["controller_family"], "incremental PI-family")
    self.assertEqual(scan["controller_family"], "sequential scan-and-retune")
