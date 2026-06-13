"""Ensure engine never imports pyscript."""

from __future__ import annotations

import ast
import pkgutil
from pathlib import Path

import wod_chargen


def _iter_py_files(root: Path):
    for path in root.rglob("*.py"):
        if path.name == "__init__.py" or path.suffix == ".py":
            yield path


def test_engine_does_not_import_pyscript():
    pkg_root = Path(wod_chargen.__file__).parent
    banned = {"pyscript", "js", "pyodide"}
    for path in _iter_py_files(pkg_root):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert alias.name.split(".")[0] not in banned, f"{path}: imports {alias.name}"
            elif isinstance(node, ast.ImportFrom) and node.module:
                assert node.module.split(".")[0] not in banned, f"{path}: imports from {node.module}"
