"""_format_sci_tex extracted from the calibration experiment runner."""

from __future__ import annotations

from typing import Any
import numpy as np


def _format_sci_tex(value: Any) -> str:
    val = float(value)
    if not np.isfinite(val):
        return "$\\mathrm{nan}$"
    if val == 0.0:
        return "$0$"
    mantissa, exponent = f"{val:.2e}".split("e")
    return f"${mantissa}\\times10^{{{int(exponent)}}}$"
