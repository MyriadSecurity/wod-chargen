"""Verify wizard imports match engine exports and served sources are current."""

from __future__ import annotations

import ast
import sys
from pathlib import Path
from urllib.request import urlopen

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from generate_pyscript_config import parse_cache_version  # noqa: E402

WIZARD_SHARE_IMPORTS = {
    "SharePayload",
    "browser_share_url",
    "decode_query",
    "wizard_share_options",
}


def _top_level_defs(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    return {
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.ClassDef))
    }


def test_share_module_exports_wizard_imports():
    defs = _top_level_defs(ROOT / "wod_chargen" / "core" / "share.py")
    missing = WIZARD_SHARE_IMPORTS - defs
    assert not missing, f"share.py missing exports required by wizard: {sorted(missing)}"


def test_served_share_py_contains_wizard_exports(site_base_url: str):
    with urlopen(f"{site_base_url}/wod_chargen/core/share.py", timeout=10) as resp:
        source = resp.read().decode("utf-8")
    for name in WIZARD_SHARE_IMPORTS:
        assert f"def {name}" in source or f"class {name}" in source, name


def test_pyscript_toml_has_cache_version_comment():
    version = parse_cache_version(ROOT / "pyscript.toml")
    assert version, "pyscript.toml should include # cache_version=..."
    text = (ROOT / "pyscript.toml").read_text(encoding="utf-8")
    assert "?v=" not in text.split("[files]", 1)[1], "file paths must not use query strings"


def test_index_html_cache_version_matches_pyscript_toml():
    version = parse_cache_version(ROOT / "pyscript.toml")
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    assert version
    assert f'app/main.py?v={version}' in html
    assert f'pyscript.toml?v={version}' in html
