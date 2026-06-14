"""Strategy reference page unit tests."""

from __future__ import annotations

import importlib
import sys

import pytest

from tests.support.pyscript_stubs import install_pyscript_stubs


def _fresh_strategy_module():
    install_pyscript_stubs()
    for name in list(sys.modules):
        if name.startswith("app."):
            sys.modules.pop(name, None)
    return importlib.import_module("app.strategy_page")


@pytest.fixture
def stubs():
    return install_pyscript_stubs()


def _walk(node):
    yield node
    for child in getattr(node, "children", []):
        yield from _walk(child)


def _find_by_class(root, class_name: str):
    for node in _walk(root):
        classes = (getattr(node, "className", "") or "").split()
        if class_name in classes:
            return node
    return None


def _find_h1(root):
    for node in _walk(root):
        if getattr(node, "tagName", "") == "H1":
            return node
    return None


def test_strategy_page_mount_overview(stubs):
    mod = _fresh_strategy_module()
    stubs.window.location.hash = "#strategy"
    app = mod.StrategyPageApp(stubs.elements["app-root"])
    app.mount()
    h1 = _find_h1(stubs.elements["app-root"])
    assert h1 is not None
    assert "How Characters Are Built" in h1.innerText


def test_strategy_page_tab_hash(stubs):
    mod = _fresh_strategy_module()
    stubs.window.location.hash = "#strategy?tab=xp"
    app = mod.StrategyPageApp(stubs.elements["app-root"])
    assert app.state["tab"] == "xp"
    app.mount()
    body = _find_by_class(stubs.elements["app-root"], "strategy-body")
    assert body is not None
    h2_titles = [
        getattr(n, "innerText", "")
        for n in _walk(body)
        if getattr(n, "tagName", "") == "H2"
    ]
    assert "Choosing XP spends" in h2_titles


def test_strategy_content_covers_all_tabs():
    from app.strategy_content import STRATEGY_TABS, strategy_sections

    sections = strategy_sections()
    for tab_id, _label in STRATEGY_TABS:
        assert tab_id in sections
        assert len(sections[tab_id]) >= 1


def test_main_reuses_strategy_app_on_hash_update(stubs):
    from pathlib import Path

    stubs.window.location.hash = "#strategy?tab=creation"
    source = (Path(__file__).resolve().parents[1] / "app/main.py").read_text(encoding="utf-8")
    lines = source.rstrip().splitlines()
    if lines[-1].strip() == "main()":
        source = "\n".join(lines[:-1]) + "\n"
    ns: dict = {"__name__": "app.main"}
    exec(compile(source, "app/main.py", "exec"), ns)  # noqa: S102
    ns["main"]()
    first = ns["_strategy_app"]
    assert first is not None
    assert first.state["tab"] == "creation"

    stubs.window.location.hash = "#strategy?tab=reference"
    ns["_mount_app"]()
    assert ns["_strategy_app"] is first
    assert first.state["tab"] == "reference"
