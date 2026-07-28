"""SPI generator and sheet model tests."""

from __future__ import annotations

from wod_chargen.games.registry import get_game
from wod_chargen.games.spi.generator import generate_character
from wod_chargen.games.spi.sheet_model import build_sheet_model
from wod_chargen.venues import load_venue

AFFINITY_TYPES = ("ghost", "spirit", "mage", "fae", "vampire")


def test_get_game_spi():
    system = get_game("spi")
    assert system.id == "spi"
    assert len(system.get_division_options()) == 5
    assert len(system.get_faction_options()) == 5
    assert len(system.get_archetypes()) == 8
    assert system.get_affinity_options()[0]["id"] == "any"


def test_generate_fixed_35_seed_stable():
    venue = load_venue("fixed_35")
    opts = {
        "division": "defense",
        "faction": "humanity_first",
        "archetype": "guardian",
        "affinity": "vampire",
        "multi_affinity": False,
    }
    a = generate_character(42, opts, venue)
    b = generate_character(42, opts, venue)
    assert a.character == b.character
    assert a.xp_budget == 35
    assert a.xp_remaining >= 0
    assert a.xp_spent + a.xp_remaining == a.xp_budget
    assert a.character["division_status"] == 1
    assert a.character["affinities"]["vampire"] >= 1
    assert sum(1 for v in a.character["affinities"].values() if v > 0) == 1
    assert a.character["attributes"]["presence"] >= 1
    assert "weaponry" in a.character["skills"]
    assert a.character["virtue"]
    assert a.character["vice"]


def test_multi_affinity_off_keeps_single_track():
    venue = load_venue("fixed_35")
    result = generate_character(
        7,
        {
            "archetype": "occultist",
            "affinity": "mage",
            "multi_affinity": False,
        },
        venue,
    )
    raised = [k for k, v in result.character["affinities"].items() if int(v) > 0]
    assert raised == ["mage"]


def test_multi_affinity_on_can_raise_secondary():
    venue = load_venue("fixed_35")
    # High XP so secondary affinity is affordable
    venue_custom = load_venue("spi_custom_xp")
    found_multi = False
    for seed in range(50):
        result = generate_character(
            seed,
            {
                "archetype": "occultist",
                "affinity": "mage",
                "multi_affinity": True,
                "xp": "200",
            },
            venue_custom,
        )
        raised = sum(1 for v in result.character["affinities"].values() if int(v) > 0)
        if raised >= 2:
            found_multi = True
            break
    assert found_multi, "expected at least one seed to buy a second Affinity with multi on"


def test_integrity_respects_top_two_affinities():
    venue = load_venue("spi_custom_xp")
    result = generate_character(
        3,
        {"archetype": "occultist", "affinity": "mage", "multi_affinity": True, "xp": "80"},
        venue,
    )
    vals = sorted((int(v) for v in result.character["affinities"].values()), reverse=True)
    max_int = 11 - sum(vals[:2])
    assert result.character["advantages"]["max_integrity"] == max(1, max_int)
    assert result.character["integrity"] <= result.character["advantages"]["max_integrity"]


def test_sheet_model_builds():
    venue = load_venue("fixed_35")
    result = generate_character(1, {"archetype": "investigator"}, venue)
    sheet = build_sheet_model(result)
    assert sheet.attributes.title == "Attributes"
    assert len(sheet.attributes.columns) == 3
    assert sheet.header.meta[0].label == "Division"
    labels = {m.label for m in sheet.advantages}
    assert "Health" in labels
    assert "Max Integrity" in labels


def test_system_generate_via_facade():
    system = get_game("spi")
    venue = load_venue("mes_spi")
    result = system.generate(9, {"approval": "2026-01", "archetype": "scholar"}, venue)
    assert result.game_id == "spi"
    assert result.xp_budget == 35
    sheet = system.build_sheet_model(result)
    assert sheet.affinities.title == "Affinities"
