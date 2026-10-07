from __future__ import annotations

from ._support import CAL

# Root unittest classes bind this function; avoid duplicate pytest collection.
__test__ = False


def test_pick_ring_result_prefers_requested_cross_talk(self) -> None:
    """Select the requested coupling case rather than the first sweep entry."""
    results = [
        {"cross_talk_level": 0.0, "settle_ms": 5000.0},
        {"cross_talk_level": 0.06, "settle_ms": 2881.0},
    ]

    picked = CAL.pick_ring_result(results, preferred_ct=0.06)

    self.assertIsNotNone(picked)
    self.assertAlmostEqual(float(picked["cross_talk_level"]), 0.06)
    self.assertAlmostEqual(float(picked["settle_ms"]), 2881.0)
