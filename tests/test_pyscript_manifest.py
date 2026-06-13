"""PyScript packaging checks — catch missing browser runtime files early."""

from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from generate_pyscript_config import (  # noqa: E402
    collect_pyscript_paths,
    compute_cache_version,
    parse_pyscript_toml,
    render_pyscript_toml,
)

APP_ROOT = ROOT / "app"


def _module_to_path(module: str) -> str:
    return module.replace(".", "/") + ".py"


def _iter_app_imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("app."):
            imports.add(node.module)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith("app."):
                    imports.add(alias.name)
    return imports


def _collect_app_import_closure(entry: Path) -> set[str]:
    """All app.* modules reachable from an entrypoint via static import analysis."""
    seen: set[str] = set()
    queue = [_module_to_path("app.main")]
    while queue:
        rel = queue.pop()
        if rel in seen:
            continue
        seen.add(rel)
        path = ROOT / rel
        assert path.is_file(), f"Missing app module file: {rel}"
        for module in _iter_app_imports(path):
            dep = _module_to_path(module)
            if dep not in seen:
                queue.append(dep)
    return seen


def test_pyscript_toml_matches_filesystem():
    required = collect_pyscript_paths(ROOT)
    manifest = parse_pyscript_toml(ROOT / "pyscript.toml")
    missing = required - manifest
    extra = manifest - required
    assert not missing, (
        "pyscript.toml is missing runtime files. "
        f"Add: {sorted(missing)}. Run: python3 scripts/generate_pyscript_config.py"
    )
    assert not extra, (
        "pyscript.toml lists files that no longer exist. "
        f"Remove: {sorted(extra)}. Run: python3 scripts/generate_pyscript_config.py"
    )


def test_pyscript_toml_is_current():
    required = collect_pyscript_paths(ROOT)
    cache_version = compute_cache_version(ROOT, required)
    expected = render_pyscript_toml(required, cache_version)
    actual = (ROOT / "pyscript.toml").read_text(encoding="utf-8")
    assert actual == expected, "pyscript.toml is stale. Run: python3 scripts/generate_pyscript_config.py"


def test_app_entrypoint_imports_are_packaged():
    packaged = parse_pyscript_toml(ROOT / "pyscript.toml")
    for rel in _collect_app_import_closure(APP_ROOT / "main.py"):
        assert rel in packaged, f"{rel} is imported by the app but missing from pyscript.toml"


def test_wizard_imports_sheet_module():
    wizard = APP_ROOT / "wizard.py"
    imports = _iter_app_imports(wizard)
    assert "app.components.sheet" in imports
    assert "app/components/sheet.py" in parse_pyscript_toml(ROOT / "pyscript.toml")
