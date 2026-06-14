"""App boot path — catches import and mount failures before opening a browser."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest

from tests.support.pyscript_stubs import install_pyscript_stubs

ROOT = Path(__file__).resolve().parent.parent


def _load_main_module():
    """Load app/main.py without executing the trailing main() call."""
    install_pyscript_stubs()
    source = (ROOT / "app" / "main.py").read_text(encoding="utf-8")
    lines = source.rstrip().splitlines()
    if lines and lines[-1].strip() == "main()":
        source = "\n".join(lines[:-1]) + "\n"
    namespace: dict = {"__name__": "app.main", "__file__": str(ROOT / "app" / "main.py")}
    exec(compile(source, "app/main.py", "exec"), namespace)  # noqa: S102
    return namespace


def _fresh_wizard_module():
    """Import app.wizard after stubs; drop cached module when re-stubbing."""
    install_pyscript_stubs()
    sys.modules.pop("app.wizard", None)
    sys.modules.pop("app.components.footer", None)
    sys.modules.pop("app.components.sheet", None)
    return importlib.import_module("app.wizard")


@pytest.fixture
def stubs():
    return install_pyscript_stubs()


def test_main_boot_hides_loading_overlay(stubs):
    main_ns = _load_main_module()
    main_ns["main"]()
    overlay = stubs.elements["loading-overlay"]
    assert overlay.classList.contains("hidden")
    assert stubs.elements["py-error"].classList.contains("hidden")
    assert stubs.elements["app-root"].children


def test_wizard_app_mounts_game_step(stubs):
    wizard = _fresh_wizard_module()
    root = stubs.elements["app-root"]
    app = wizard.WizardApp(root)
    app.mount()
    assert app.state["step"] == "game"
    assert root.children
    assert any(child.children for child in root.children)


def test_wizard_generate_vampire(stubs):
    wizard = _fresh_wizard_module()
    app = wizard.WizardApp(stubs.elements["app-root"])
    app.state["step"] = "generate"
    app.state["seed"] = 0  # buys loresheet + exercises apply_loresheet_benefits
    app.state["clan"] = "brujah"
    app.state["arch"] = "enforcer"
    app.state["sub"] = "brawler"
    app._generate()
    assert app.state["error"] is None, app.state.get("error")
    assert app.state["result"] is not None
    assert app.state["result"].seed == app.state["seed"]
    assert app.state["result"].character.get("loresheets"), "seed 0 should purchase a loresheet"


def test_wizard_results_view_renders_sheet(stubs):
    wizard = _fresh_wizard_module()
    app = wizard.WizardApp(stubs.elements["app-root"])
    app._generate()
    app.state["step"] = "results"
    app.mount()
    assert app.state["result"] is not None
    assert stubs.elements["app-root"].children


def test_wizard_share_sync_uses_null_state(stubs):
    wizard = _fresh_wizard_module()
    app = wizard.WizardApp(stubs.elements["app-root"])
    app._generate()
    calls = stubs.window.history.replace_calls
    assert calls, "replaceState should run after successful generation"
    state, _title, url = calls[-1]
    assert state is None
    assert "seed=" in url


def test_wizard_parse_url_regenerates_character(stubs):
    wizard = _fresh_wizard_module()
    stubs.window.location.search = (
        "?schema=0.1&seed=424242&game=lotn_v5&venue=mes_end_to_dawn"
        "&type=vampire&clan=brujah&arch=diplomat&sub=silver_tongue&approval=2026-06"
    )
    app = wizard.WizardApp(stubs.elements["app-root"])
    assert app.state["seed"] == 424242
    assert app.state["result"] is not None
    assert app.state["step"] == "results"


def test_wizard_stale_share_url_recovers(stubs):
    wizard = _fresh_wizard_module()
    stubs.window.location.search = (
        "?schema=0.1&seed=1&game=lotn_v5&venue=mes_end_to_dawn"
        "&type=vampire&arch=deleted_arch&sub=missing_sub"
    )
    app = wizard.WizardApp(stubs.elements["app-root"])
    assert app.state["result"] is not None
    assert app.state["error"] is None


@pytest.mark.parametrize(
    "character_type",
    ["vampire", "ghoul", "thin_blood"],
)
def test_wizard_generate_all_character_types(stubs, character_type):
    wizard = _fresh_wizard_module()
    app = wizard.WizardApp(stubs.elements["app-root"])
    app.state["type"] = character_type
    if character_type == "ghoul":
        app.state["domitor_clan"] = "tremere"
    app._validate_selection()
    app._generate()
    assert app.state["error"] is None, app.state.get("error")
    assert app.state["result"] is not None
    assert app.state["result"].options["type"] == character_type
