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


def _find_by_class(root, class_name: str):
    """Depth-first search for first element whose className contains class_name."""
    if class_name in getattr(root, "className", ""):
        return root
    for child in getattr(root, "children", []):
        found = _find_by_class(child, class_name)
        if found is not None:
            return found
    return None


def _find_all_by_class(root, class_name: str) -> list:
    found = []
    if class_name in getattr(root, "className", ""):
        found.append(root)
    for child in getattr(root, "children", []):
        found.extend(_find_all_by_class(child, class_name))
    return found


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
    assert app.state["phase"] == "landing"
    assert root.children
    assert any(child.children for child in root.children)


def test_wizard_generate_vampire(stubs):
    wizard = _fresh_wizard_module()
    app = wizard.WizardApp(stubs.elements["app-root"])
    app.state["phase"] = "build"
    app.state["unlocked_through"] = "generate"
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
    app.state["phase"] = "results"
    app.mount()
    assert app.state["result"] is not None
    assert stubs.elements["app-root"].children


def test_wizard_results_include_logs_for_print(stubs):
    wizard = _fresh_wizard_module()
    app = wizard.WizardApp(stubs.elements["app-root"])
    app._generate()
    app.state["phase"] = "results"
    app.state["tab"] = "sheet"
    app.mount()
    root = stubs.elements["app-root"]
    log_panel = _find_by_class(root, "results-log-panel")
    xp_panel = _find_by_class(root, "results-xp-panel")
    recreate_panel = _find_by_class(root, "results-recreate-panel")
    assert log_panel is not None
    assert xp_panel is not None
    assert recreate_panel is not None
    log_body = _find_by_class(log_panel, "results-log-body")
    xp_body = _find_by_class(xp_panel, "results-log-body")
    recreate_body = _find_by_class(recreate_panel, "results-recreate-body")
    assert log_body is not None and ("[base]" in log_body.innerText or log_body.children)
    assert xp_body is not None and "Purchases" in xp_body.innerText
    assert recreate_body is not None
    assert "Share link:" in recreate_body.innerText
    assert "seed=" in recreate_body.innerText


def test_print_styles_include_all_results_sections():
    css = (ROOT / "static" / "theme.css").read_text(encoding="utf-8")
    assert ".results-print-root .results-tab-hidden" in css
    assert ".results-log-panel" in css
    assert ".results-recreate-panel" in css


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
    assert app.state["phase"] == "results"


def test_wizard_full_random_vampire(stubs):
    wizard = _fresh_wizard_module()
    app = wizard.WizardApp(stubs.elements["app-root"])
    app.state["phase"] = "build"
    app.state["full_random"] = True
    app._apply_full_random("vampire")
    app._generate()
    assert app.state["error"] is None, app.state.get("error")
    assert app.state["result"] is not None
    char = app.state["result"].character
    assert char["character_type"] == "vampire"
    assert char.get("clan")
    assert char.get("archetype")
    assert char.get("sub_archetype")
    assert app.state.get("predator")


def test_wizard_full_random_ghoul(stubs):
    wizard = _fresh_wizard_module()
    app = wizard.WizardApp(stubs.elements["app-root"])
    app.state["full_random"] = True
    app._apply_full_random("ghoul")
    app._generate()
    assert app.state["error"] is None, app.state.get("error")
    assert app.state["result"] is not None
    char = app.state["result"].character
    assert char["character_type"] == "ghoul"
    assert char.get("domitor_clan")
    assert not app.state.get("predator")


def test_wizard_custom_xp_generation(stubs):
    wizard = _fresh_wizard_module()
    app = wizard.WizardApp(stubs.elements["app-root"])
    app.state["venue"] = "custom_xp"
    app.state["xp_custom"] = "120"
    app._generate()
    assert app.state["error"] is None, app.state.get("error")
    assert app.state["result"] is not None
    assert app.state["result"].xp_budget == 120


def test_wizard_finish_step_scrolls_and_collapses(stubs):
    wizard = _fresh_wizard_module()
    app = wizard.WizardApp(stubs.elements["app-root"])
    app.state["phase"] = "build"
    app.state["unlocked_through"] = "venue"
    app._finish_step("venue")
    assert app.state["unlocked_through"] == "type"
    assert app.state["scroll_to_step"] == "type"
    assert app.state["expanded_sections"] == []
    assert app._is_section_collapsed("venue")
    assert not app._is_section_collapsed("type")


def test_wizard_step_summary_venue_custom_xp(stubs):
    wizard = _fresh_wizard_module()
    app = wizard.WizardApp(stubs.elements["app-root"])
    app.state["venue"] = "custom_xp"
    app.state["xp_custom"] = "150"
    assert app._step_summary("venue") == "150 XP"


def test_wizard_expanded_section_reopens(stubs):
    wizard = _fresh_wizard_module()
    app = wizard.WizardApp(stubs.elements["app-root"])
    app.state["unlocked_through"] = "faction"
    assert app._is_section_collapsed("venue")
    app.state["expanded_sections"] = ["venue"]
    assert not app._is_section_collapsed("venue")


def test_wizard_reset_to_landing(stubs):
    wizard = _fresh_wizard_module()
    app = wizard.WizardApp(stubs.elements["app-root"])
    app.state["phase"] = "results"
    app.state["result"] = object()
    app._reset_to_landing()
    assert app.state["phase"] == "landing"
    assert app.state["result"] is None
    assert app.state["scroll_to_step"] is None
    assert app.state["expanded_sections"] == []
    assert stubs.window.history.replace_calls


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
