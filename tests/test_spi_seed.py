"""SPI MES Game XP floor and package seed tests."""

from __future__ import annotations

import json
from pathlib import Path

from wod_chargen.core.data_loader import load_json_cached
from wod_chargen.games.spi.system import SpiSystem
from wod_chargen.venues import load_venue, mes_xp_for_month, resolve_xp_budget

ROOT = Path(__file__).resolve().parents[1]
SPI_DATA = ROOT / "wod_chargen" / "games" / "spi" / "data"


def test_mes_spi_xp_floor_jan_2026():
    chart = load_json_cached("wod_chargen.venues", "mes_spi_xp_chart.json")
    assert mes_xp_for_month("2026-01", chart) == 35


def test_mes_spi_xp_floor_jul_2026():
    chart = load_json_cached("wod_chargen.venues", "mes_spi_xp_chart.json")
    assert mes_xp_for_month("2026-07", chart) == 53


def test_mes_spi_xp_extension_beyond_lookup():
    chart = load_json_cached("wod_chargen.venues", "mes_spi_xp_chart.json")
    # 2027-01 = 35 + 12*3 = 71
    assert mes_xp_for_month("2027-01", chart) == 71


def test_resolve_mes_spi_budget():
    xp, lines = resolve_xp_budget("mes_spi", {"approval": "2026-07"})
    assert xp == 53
    assert any("2026-07" in line for line in lines)


def test_resolve_fixed_35():
    xp, lines = resolve_xp_budget("fixed_35", {})
    assert xp == 35
    assert any("35" in line for line in lines)


def test_catalog_includes_spi_stub():
    catalog = load_json_cached("wod_chargen.games", "catalog.json")
    assert "spi" in catalog
    assert catalog["spi"]["implemented"] is True
    assert catalog["spi"]["under_construction"] is True
    assert catalog["spi"]["maturity"] == "alpha"
    assert "Society" in catalog["spi"]["label"]
    assert "unreliable" in catalog["spi"]["status_note"].lower()


def test_picker_lists_spi_profiles():
    picker = load_json_cached("wod_chargen.venues", "picker.json")
    assert picker["spi"] == ["mes_spi", "fixed_35", "spi_custom_xp"]
    assert load_venue("mes_spi")["game_id"] == "spi"
    assert load_venue("fixed_35")["xp_config"]["total"] == 35


def test_spi_data_json_loads():
    for name in (
        "creation.json",
        "costs.json",
        "attributes.json",
        "skills.json",
        "divisions.json",
        "factions.json",
        "affinity_types.json",
        "affinity_levels.json",
        "advantages.json",
        "wizard_ui.json",
        "character_types.json",
        "merits.json",
    ):
        payload = json.loads((SPI_DATA / name).read_text(encoding="utf-8"))
        assert payload


def test_merits_have_no_codex_blurbs():
    merits = json.loads((SPI_DATA / "merits.json").read_text(encoding="utf-8"))
    assert "codex_enrichment" not in merits
    assert len(merits["merits"]) >= 300
    for entry in merits["merits"]:
        assert "summary" not in entry
        assert "book" not in entry
        assert "summary_source" not in entry
        assert "id" in entry
        assert "label" in entry


def test_merits_are_sanctioned_only():
    """Catalog excludes sheet rows that are not Rules Addendum–sanctioned."""
    merits = json.loads((SPI_DATA / "merits.json").read_text(encoding="utf-8"))
    allow = json.loads((SPI_DATA / "sanctioned_merit_ids.json").read_text(encoding="utf-8"))
    general_ok = set(allow["general_ids"])
    banned_general = {
        "mystery_cult_initiation",
        "boxing",
        "marksmanship",
        "martial_arts",
        "iron_skin",
        "unseen_sense",
        "artifact",
    }
    for entry in merits["merits"]:
        if entry["category"] == "general":
            assert entry["id"] in general_ok
            assert entry["id"] not in banned_general
        else:
            assert entry["category"] == "affinity"
    # Dual-catalog powers: Affinity kept, General twin removed
    by_id = {}
    for entry in merits["merits"]:
        by_id.setdefault(entry["id"], set()).add(entry["category"])
    assert by_id.get("medium") == {"affinity"}
    assert "mystery_cult_initiation" not in by_id


def test_archetype_manifest_has_eight_primaries():
    manifest = json.loads((SPI_DATA / "archetypes" / "_manifest.json").read_text(encoding="utf-8"))
    assert len(manifest["primaries"]) == 8
    subtypes = manifest.get("subtypes") or {}
    for aid in manifest["primaries"]:
        path = SPI_DATA / "archetypes" / f"{aid}.json"
        arch = json.loads(path.read_text(encoding="utf-8"))
        assert arch["id"] == aid
        assert "affinity_biases" in arch
        subs = subtypes.get(aid) or []
        assert len(subs) >= 2
        for sid in subs:
            spath = SPI_DATA / "archetypes" / aid / f"{sid}.json"
            assert spath.exists()
            sub = json.loads(spath.read_text(encoding="utf-8"))
            assert sub["id"] == sid
            assert sub.get("modifiers")


def test_spi_system_wizard_and_venue_picker():
    system = SpiSystem()
    assert system.id == "spi"
    assert system.get_wizard_steps() == [
        "venue",
        "division",
        "faction",
        "archetype",
        "sub_archetype",
        "affinity",
        "generate",
    ]
    copy = system.get_wizard_copy()
    assert "multi_affinity_label" in copy
    assert "sub_archetype_title" in copy
    venues = system.get_venue_picker()
    assert [v["id"] for v in venues] == ["mes_spi", "fixed_35", "spi_custom_xp"]
    assert venues[0]["requires_approval_month"] is True
    assert venues[2]["requires_custom_xp"] is True
    arches = system.get_archetypes()
    assert len(arches) == 8
    assert len(arches[0]["sub_archetypes"]) >= 2
    assert system.get_sub_archetypes("investigator")[0]["id"] == "detective"
