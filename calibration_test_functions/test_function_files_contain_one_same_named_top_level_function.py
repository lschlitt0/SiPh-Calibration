from __future__ import annotations

import ast
from ._support import FUNCTION_DIRECTORY
from ._support import SUPPORT_MODULES

# Root unittest classes bind this function; avoid duplicate pytest collection.
__test__ = False


def test_function_files_contain_one_same_named_top_level_function(self) -> None:
    """Keep methods in models and closures inside their owning functions."""
    for path in sorted(FUNCTION_DIRECTORY.glob("*.py")):
        with self.subTest(module=path.stem):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            functions = [node for node in tree.body if isinstance(node, ast.FunctionDef)]
            classes = [node for node in tree.body if isinstance(node, ast.ClassDef)]
            if path.stem in SUPPORT_MODULES:
                self.assertEqual(functions, [])
                if path.stem == "models":
                    self.assertTrue(classes)
                else:
                    self.assertEqual(classes, [])
            else:
                self.assertEqual([node.name for node in functions], [path.stem])
                self.assertEqual(classes, [])
