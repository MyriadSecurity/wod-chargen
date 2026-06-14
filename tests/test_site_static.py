"""Static site integrity — assets, syntax, and HTTP availability."""

from __future__ import annotations

import ast
import compileall
import importlib
import pkgutil
import re
import sys
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import urlopen

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from generate_pyscript_config import collect_pyscript_paths, parse_pyscript_toml  # noqa: E402

LOCAL_PREFIXES = ("app.", "wod_chargen.")
SRC_ATTR_RE = re.compile(r"""(?:src|href)=["']([^"']+)["']""")


def _iter_local_imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            if node.module.split(".")[0] in ("app", "wod_chargen"):
                modules.add(node.module)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".")[0] in ("app", "wod_chargen"):
                    modules.add(alias.name)
    return modules


def _module_to_path(module: str) -> str:
    py_path = ROOT / f"{module.replace('.', '/')}.py"
    if py_path.is_file():
        return py_path.relative_to(ROOT).as_posix()
    init_path = ROOT / module.replace(".", "/") / "__init__.py"
    if init_path.is_file():
        return init_path.relative_to(ROOT).as_posix()
    raise AssertionError(f"No Python file for module: {module}")


def _collect_python_closure(entry_rel: str) -> set[str]:
    seen: set[str] = set()
    queue = [entry_rel]
    while queue:
        rel = queue.pop()
        if rel in seen:
            continue
        seen.add(rel)
        path = ROOT / rel
        assert path.is_file(), f"Missing module file: {rel}"
        for module in _iter_local_imports(path):
            dep = _module_to_path(module)
            if dep not in seen:
                queue.append(dep)
    return seen


def _discover_wod_chargen_modules() -> list[str]:
    import wod_chargen

    prefix = wod_chargen.__name__ + "."
    return sorted(
        module.name
        for module in pkgutil.walk_packages(wod_chargen.__path__, prefix)
        if not module.name.endswith(".tests")
    )


def test_index_html_entrypoints_exist():
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    refs = SRC_ATTR_RE.findall(html)
    assert refs, "index.html should reference local assets"
    for ref in refs:
        if ref.startswith(("http://", "https://", "//", "#", "data:")):
            continue
        path = ref.split("?")[0]
        full = ROOT / path
        assert full.is_file(), f"index.html references missing file: {ref}"


def test_index_html_loads_pyscript_entry():
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    assert 'src="app/main.py' in html
    assert 'config="pyscript.toml' in html
    assert (ROOT / "app" / "main.py").is_file()
    assert (ROOT / "pyscript.toml").is_file()


def test_index_html_requires_secure_context_for_pyscript():
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    assert "crypto.randomUUID" in html
    assert "location.replace" in html


def test_all_app_and_engine_python_compiles():
    targets = [ROOT / "app", ROOT / "wod_chargen"]
    for target in targets:
        ok = compileall.compile_dir(
            target,
            quiet=1,
            legacy=False,
            ddir=str(ROOT),
        )
        assert ok, f"Syntax errors under {target.name}"


def test_wizard_import_closure_files_exist():
    closure = _collect_python_closure("app/wizard.py")
    assert "app/components/sheet.py" in closure
    assert "wod_chargen/games/lotn_v5/generator.py" in closure


def test_import_closure_packaged_in_pyscript_toml():
    packaged = parse_pyscript_toml(ROOT / "pyscript.toml")
    closure = _collect_python_closure("app/wizard.py")
    json_deps = {p for p in packaged if p.endswith(".json")}
    py_closure = {p for p in closure if p.endswith(".py")}
    missing = py_closure - packaged
    assert not missing, f"pyscript.toml missing wizard dependency modules: {sorted(missing)}"
    assert json_deps, "pyscript.toml should list JSON data files"


@pytest.mark.parametrize("module_name", _discover_wod_chargen_modules())
def test_import_wod_chargen_module(module_name: str):
    importlib.import_module(module_name)


def test_static_assets_served_over_http(site_base_url: str):
    paths = {
        "index.html",
        "pyscript.toml",
        "static/theme.css",
        "static/img/dark-pack-logo.png",
        "static/img/dark-pack-favicon-32.png",
    }
    paths |= collect_pyscript_paths(ROOT)
    for rel in sorted(paths):
        url = f"{site_base_url}/{rel}"
        try:
            with urlopen(url, timeout=10) as resp:
                assert resp.status == 200, rel
        except HTTPError as exc:
            pytest.fail(f"{rel} returned HTTP {exc.code}")


def test_main_py_not_using_js_null_import():
    source = (ROOT / "app" / "wizard.py").read_text(encoding="utf-8")
    assert "from js import null" not in source
    assert "replaceState({}," not in source
    assert "replaceState(None," in source
