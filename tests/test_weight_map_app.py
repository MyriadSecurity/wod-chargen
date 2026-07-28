"""Weight map app unit tests (no browser, bounded retries)."""

from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

import pytest

from tests.support.pyscript_stubs import install_pyscript_stubs


def _fresh_weight_map_module():
    install_pyscript_stubs()
    for name in list(sys.modules):
        if name.startswith("app."):
            sys.modules.pop(name, None)
    return importlib.import_module("app.weight_map")


@pytest.fixture
def stubs():
    handle = install_pyscript_stubs()
    handle.window.d3 = object()
    handle.window.renderWeightMap = lambda container, payload: True
    handle.window.weightMapAssetsReady = lambda: True
    return handle


def _find_canvas(root):
    def walk(node):
        if getattr(node, "id", "") == "weight-map-canvas":
            return node
        for child in getattr(node, "children", []):
            found = walk(child)
            if found is not None:
                return found
        return None

    return walk(root)


def test_weight_map_mount_predator_lens(stubs):
    mod = _fresh_weight_map_module()
    stubs.window.location.hash = "#weights?game=lotn_v5&lens=predator&mode=overview"
    app = mod.WeightMapApp(stubs.elements["app-root"])
    app.mount()
    assert app.state["lens"] == "predator"
    assert _find_canvas(stubs.elements["app-root"]) is not None


def test_weight_map_parse_lens_and_id(stubs):
    mod = _fresh_weight_map_module()
    stubs.window.location.hash = "#weights?game=lotn_v5&lens=clan&mode=profile&id=tremere"
    app = mod.WeightMapApp(stubs.elements["app-root"])
    assert app.state["lens"] == "clan"
    assert app.state["mode"] == "profile"
    assert app.state["id"] == "tremere"


def test_weight_map_render_stops_after_max_attempts(stubs):
    mod = _fresh_weight_map_module()
    stubs.window.weightMapAssetsReady = lambda: False
    stubs.window.location.hash = "#weights?game=lotn_v5"
    root = stubs.elements["app-root"]
    app = mod.WeightMapApp(root)
    app._render_attempts = mod._MAX_RENDER_ATTEMPTS
    canvas = stubs.document.createElement("div")
    app._draw(canvas)
    assert "Could not load" in canvas.children[0].innerText


def test_main_reuses_weight_app_on_hash_update(stubs):
    from pathlib import Path

    install_pyscript_stubs()
    stubs.window.d3 = object()
    stubs.window.renderWeightMap = lambda container, payload: True
    stubs.window.weightMapAssetsReady = lambda: True
    stubs.window.location.hash = "#weights?game=lotn_v5&lens=archetype&mode=overview"

    source = (Path(__file__).resolve().parents[1] / "app/main.py").read_text(encoding="utf-8")
    lines = source.rstrip().splitlines()
    if lines[-1].strip() == "main()":
        source = "\n".join(lines[:-1]) + "\n"
    ns: dict = {"__name__": "app.main"}
    exec(compile(source, "app/main.py", "exec"), ns)  # noqa: S102
    ns["main"]()
    first = ns["_weight_app"]
    assert first is not None

    stubs.window.location.hash = "#weights?game=lotn_v5&lens=predator&mode=profile&id=alleycat"
    ns["_mount_app"]()
    assert ns["_weight_app"] is first
    assert first.state["lens"] == "predator"
    assert first.state["id"] == "alleycat"


def test_tree_payload_json_serializable():
    from app.weight_map_data import build_tree
    from app.weight_map_data_spi import build_tree as build_spi_tree

    for lens in ("archetype", "predator", "clan", "catalog", "category", "combo"):
        tree = build_tree(lens, "overview")
        json.dumps(tree)
    json.dumps(build_tree("predator", "profile", id="bagger"))
    json.dumps(
        build_tree(
            "combo",
            "profile",
            arch="enforcer",
            sub="brawler",
            predator="farmer",
            clan="brujah",
            type="vampire",
        )
    )
    for lens in ("archetype", "division", "faction", "affinity", "catalog", "combo"):
        json.dumps(build_spi_tree(lens, "overview"))


def test_spi_division_profile_tolerates_lotn_leftover_id():
    from app.weight_map_data_spi import build_tree

    tree = build_tree("division", "profile", id="brujah")
    assert tree["name"] == "Adventure"
    assert tree["children"]


def test_spi_overview_nodes_are_navigable():
    from app.weight_map_data_spi import build_tree

    for lens in ("archetype", "division", "faction", "affinity"):
        tree = build_tree(lens, "overview")
        assert tree["children"]
        for child in tree["children"]:
            assert child.get("nav") is True
            assert child.get("lens") == lens
            assert child.get("id")


def test_spi_affinity_profile_ranks_archetypes():
    from app.weight_map_data_spi import build_tree

    tree = build_tree("affinity", "profile", id="mage")
    assert "Mage" in tree["name"]
    assert len(tree["children"]) >= 8
    assert tree["children"][0].get("nav") is True


def test_spi_combo_overview_is_hint_not_silent_merge():
    from app.weight_map_data_spi import build_tree

    tree = build_tree("combo", "overview")
    assert "How to use" in {c["name"] for c in tree["children"]}


def test_spi_weight_map_resets_invalid_ids(stubs):
    mod = _fresh_weight_map_module()
    stubs.window.location.hash = "#weights?game=spi&lens=division&mode=profile&id=brujah"
    app = mod.WeightMapApp(stubs.elements["app-root"])
    assert app.state["lens"] == "division"
    assert app.state["id"] != "brujah"
    assert app.state["id"] in {o["id"] for o in app._data().picker_for_lens("division")}
    tree = app._data().build_tree(app.state["lens"], app.state["mode"], **app._tree_params())
    assert tree.get("children")
