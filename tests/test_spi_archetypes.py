"""SPI archetype + subtype loader and merge tests."""

from __future__ import annotations

from wod_chargen.games.spi.archetypes import (
    clear_archetype_caches,
    default_sub_id,
    effective_profile,
    get_archetype,
    resolve_sub_id,
)
from wod_chargen.games.spi.generator import generate_character
from wod_chargen.games.spi.sheet_model import build_sheet_model
from wod_chargen.venues import load_venue


def setup_function() -> None:
    clear_archetype_caches()


def test_default_sub_is_first_listed():
    assert default_sub_id("investigator") == "detective"
    assert resolve_sub_id("guardian", {}) == "bodyguard"
    assert resolve_sub_id("shadow", {"sub": "any"}) == "infiltrator"
    assert resolve_sub_id("diplomat", {"sub": "handler"}) == "handler"


def test_effective_profile_applies_additive_deltas():
    base = get_archetype("investigator")
    merged = effective_profile("investigator", "forensic")
    assert merged["sub_id"] == "forensic"
    # forensic adds science +0.4 on skill_biases
    assert merged["skill_biases"]["science"] == float(base.get("skill_biases", {}).get("science", 1.0)) + 0.4
    assert merged["skill_biases"]["investigation"] == float(
        base.get("skill_biases", {}).get("investigation", 1.0)
    ) + 0.3


def test_generate_persists_sub_and_sheet_shows_it():
    venue = load_venue("fixed_35")
    result = generate_character(
        11,
        {
            "archetype": "guardian",
            "sub": "tactical",
            "division": "defense",
            "faction": "humanity_first",
            "affinity": "vampire",
        },
        venue,
    )
    assert result.character["archetype"] == "guardian"
    assert result.character["sub_archetype"] == "tactical"
    sheet = build_sheet_model(result)
    labels = {m.label: m.value for m in sheet.header.meta}
    assert labels["Archetype"] == "Guardian"
    assert labels["Subtype"] == "Tactical"


def test_seed_stable_with_subtype():
    venue = load_venue("fixed_35")
    opts = {"archetype": "scholar", "sub": "archivist", "affinity": "mage"}
    a = generate_character(5, opts, venue)
    b = generate_character(5, opts, venue)
    assert a.character == b.character
