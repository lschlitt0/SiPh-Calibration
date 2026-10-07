from __future__ import annotations

from types import ModuleType
from unittest.mock import Mock
from unittest.mock import patch
import importlib.util
import os
import sys

# Root unittest classes bind this function; avoid duplicate pytest collection.
__test__ = False


def test_optional_partitioner_initializer_is_cached(self) -> None:
    """The initializer cache must belong to the module that updates it."""
    module = importlib.import_module("calibration_functions._mtkahypar_initializer")
    initialized = object()
    stub = ModuleType("mtkahypar")
    stub.initialize = Mock(return_value=initialized)
    with patch.object(module, "_MTK_INITIALIZER", None):
        with patch.dict(sys.modules, {"mtkahypar": stub}):
            with patch.dict(os.environ, {"KAHYPAR_THREADS": "2", "MTKAHYPAR_THREADS": "4"}):
                first = module._mtkahypar_initializer()
                second = module._mtkahypar_initializer()
    self.assertIs(first, initialized)
    self.assertIs(second, initialized)
    stub.initialize.assert_called_once_with(2)
