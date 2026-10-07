"""_seed_everything extracted from the calibration experiment runner."""

from __future__ import annotations

import numpy as np
import random


def _seed_everything(seed: int) -> None:
    """Seed the global Python/NumPy RNGs; workflows also create local generators."""
    random.seed(seed)
    np.random.seed(seed % (2**32 - 1))
