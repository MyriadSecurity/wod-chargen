"""Background entry model tests."""

from __future__ import annotations

import pytest

from wod_chargen.core.data_loader import load_json_cached
from wod_chargen.core.rng import SeededRng
from wod_chargen.games.lotn_v5.backgrounds import (
    BackgroundCreationLedger,
    assign_background_dots,
    background_defs,
    can_add_modifier_dot,
    empty_backgrounds,
    level_label,
    run_background_creation,
    set_modifier_rating,
    total_background_dots,
    total_modifier_dots,
    validate_creation_modifier_accounting,
    validate_full_modifier_accounting,
)
from wod_chargen.games.lotn_v5.archetypes import effective_profile
from wod_chargen.games.lotn_v5.generator import generate_character


def _venue():
    return load_json_cached("wod_chargen.venues", "mes_end_to_dawn.json")


def _opts(**kwargs):
    base = {
        "type": "vampire",
        "clan": "brujah",
        "arch": "diplomat",
        "sub": "silver_tongue",
        "approval": "2026-06",
    }
    base.update(kwargs)
    return base


def test_background_catalog_has_levels_and_modifiers():
    defs = background_defs()
    assert "allies" in defs
    assert len(defs["allies"]["levels"]) == 3
    assert defs["allies"]["advantages"]
    assert defs["resources"]["levels"][2]["summary"].startswith("$")


def test_assign_background_dots_creates_sub_items():
    profile = effective_profile("diplomat", "silver_tongue", "vampire")
    entries = empty_backgrounds()
    lines = assign_background_dots(SeededRng(1), entries, 7, profile)
    assert len(lines) == 7
    assert total_background_dots(entries) == 7
    assert all(1 <= e["dots"] <= 3 for e in entries)
    assert all(e.get("name") for e in entries)


def test_creation_pool_accounting():
    profile = effective_profile("diplomat", "silver_tongue", "vampire")
    entries = empty_backgrounds()
    _, ledger = run_background_creation(SeededRng(99), entries, 7, profile)
    assert ledger.pool_spent == 7
    validate_creation_modifier_accounting(entries, ledger)


def test_modifier_advantages_funded_by_pool_or_disadv_trade():
    profile = effective_profile("diplomat", "silver_tongue", "vampire")
    for seed in range(40):
        entries = empty_backgrounds()
        _, ledger = run_background_creation(SeededRng(seed), entries, 7, profile)
        validate_creation_modifier_accounting(entries, ledger)
        total_adv = total_modifier_dots(entries, "advantage")
        assert total_adv == ledger.pool_spent_modifier + ledger.adv_from_disadv_granted


def test_disadvantages_grant_matched_modifier_advantages():
    profile = effective_profile("diplomat", "silver_tongue", "vampire")
    entries = empty_backgrounds()
    lines, ledger = run_background_creation(SeededRng(5), entries, 4, profile)
    if ledger.disadv_dots_added:
        assert ledger.adv_from_disadv_granted <= ledger.disadv_trade_credit()
        assert any("disadvantage trade" in line for line in lines) or ledger.adv_from_disadv_granted == 0


def test_requires_dots_gates_modifier():
    entry = {
        "type": "fame",
        "dots": 2,
        "name": "Local fame",
        "advantages": [],
        "disadvantages": [],
    }
    star_power = next(m for m in background_defs()["fame"]["advantages"] if m["id"] == "star_power")
    assert not can_add_modifier_dot(entry, star_power, "advantage")
    entry["dots"] = 3
    assert can_add_modifier_dot(entry, star_power, "advantage")


def test_modifier_ratings_stored_as_dicts():
    entry = {
        "type": "allies",
        "dots": 2,
        "name": "Legal ally",
        "advantages": [],
        "disadvantages": [],
    }
    set_modifier_rating(entry, "reliable", "advantage", 2)
    assert entry["advantages"] == [{"id": "reliable", "dots": 2}]


def test_generated_character_background_entries():
    result = generate_character(42, _opts(), _venue())
    bgs = result.character["backgrounds"]
    assert isinstance(bgs, list)
    assert total_background_dots(bgs) >= 1
    meta = result.character.get("background_meta", {})
    assert meta.get("creation_pool", {}).get("total") == 7
    validate_full_modifier_accounting(bgs, meta)


@pytest.mark.parametrize("seed", range(30))
def test_full_generation_modifier_accounting(seed: int):
    result = generate_character(seed, _opts(), _venue())
    validate_full_modifier_accounting(
        result.character["backgrounds"],
        result.character.get("background_meta", {}),
    )


def test_background_creation_log_pool_size():
    result = generate_character(42, _opts(), _venue())
    pool = result.character["background_meta"]["creation_pool"]
    assert pool["connection"] + pool["modifier"] + pool.get("unplaced", 0) == pool["total"]


def test_merits_are_separate_from_background_modifiers():
    result = generate_character(42, _opts(), _venue())
    assert "merits" in result.character
    assert isinstance(result.character["merits"], dict)
    for entry in result.character["backgrounds"]:
        for mod in entry.get("advantages", []):
            assert isinstance(mod, dict)
            assert "id" in mod
