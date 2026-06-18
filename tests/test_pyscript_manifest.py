"""PyScript bundle must include every file the browser app imports."""

from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.generate_pyscript_config import (  # noqa: E402
    collect_pyscript_paths,
    parse_pyscript_toml,
)


def _local_imports(module_path: Path) -> set[str]:
    """First-party imports from a Python file (wod_chargen.*, app.*)."""
    tree = ast.parse(module_path.read_text(encoding="utf-8"))
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            if node.module.startswith(("wod_chargen.", "app.")):
                found.add(node.module)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith(("wod_chargen", "app")):
                    found.add(alias.name)
    return found


def _module_to_path(module: str) -> Path | None:
    parts = module.split(".")
    if parts[0] not in ("wod_chargen", "app"):
        return None
    candidate = ROOT.joinpath(*parts)
    if candidate.with_suffix(".py").is_file():
        return candidate.with_suffix(".py")
    if (candidate / "__init__.py").is_file():
        return candidate / "__init__.py"
    return None


def _transitive_closure(entry_modules: list[str]) -> set[str]:
    pending = list(entry_modules)
    seen: set[str] = set()
    py_files: set[str] = set()
    while pending:
        mod = pending.pop()
        if mod in seen:
            continue
        seen.add(mod)
        path = _module_to_path(mod)
        if path is None:
            continue
        rel = path.relative_to(ROOT).as_posix()
        py_files.add(rel)
        for imported in _local_imports(path):
            if imported not in seen:
                pending.append(imported)
    return py_files


def test_pyscript_matches_repo_scan():
    expected = collect_pyscript_paths(ROOT)
    bundled = parse_pyscript_toml(ROOT / "pyscript.toml")
    assert bundled == expected


def test_loresheet_generation_succeeds_with_packages():
    """Seeds that buy loresheets must apply packages (browser failure mode)."""
    from wod_chargen.core.data_loader import load_json_cached
    from wod_chargen.games.lotn_v5.generator import generate_character

    venue = load_json_cached("wod_chargen.venues", "mes_end_to_dawn.json")
    opts = {
        "type": "vampire",
        "clan": "brujah",
        "arch": "enforcer",
        "sub": "brawler",
        "approval": "2026-06",
    }
    found = False
    for seed in range(30):
        result = generate_character(seed, opts, venue)
        if not result.character.get("loresheets"):
            continue
        if result.character.get("loresheet_meta") is None:
            continue
        found = True
        assert any(e.phase == "loresheet" for e in result.creation_log)
        break
    assert found, "expected a seed with loresheet purchase in first 30 tries"
