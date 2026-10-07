from __future__ import annotations

from unittest.mock import patch
import importlib.util
import sys
from ._support import FUNCTION_DIRECTORY
from ._support import REPOSITORY_ROOT
from ._support import SUPPORT_MODULES

# Root unittest classes bind this function; avoid duplicate pytest collection.
__test__ = False


def test_legacy_alias_and_direct_imports_share_definitions(self) -> None:
    """The old facade must expose the actual functions and model classes."""
    spec = importlib.util.spec_from_file_location(
        "calibration_layout_alias", REPOSITORY_ROOT / "Calibration_v3.py"
    )
    self.assertIsNotNone(spec)
    self.assertIsNotNone(spec.loader)
    facade = importlib.util.module_from_spec(spec)
    with patch.dict(sys.modules, {spec.name: facade}):
        spec.loader.exec_module(facade)
        for path in sorted(FUNCTION_DIRECTORY.glob("*.py")):
            if path.stem in SUPPORT_MODULES:
                continue
            with self.subTest(function=path.stem):
                module = importlib.import_module(f"calibration_functions.{path.stem}")
                function = getattr(module, path.stem)
                self.assertIs(getattr(facade, path.stem), function)
                self.assertEqual(function.__module__, module.__name__)
        models = importlib.import_module("calibration_functions.models")
        for name, value in vars(models).items():
            if isinstance(value, type) and value.__module__ == models.__name__:
                with self.subTest(model=name):
                    self.assertIs(getattr(facade, name), value)
