"""Merits and flaws catalog and creation trade tests."""

from __future__ import annotations

from wod_chargen.core.data_loader import load_json_cached
from wod_chargen.core.rng import SeededRng
from wod_chargen.games.lotn_v5.generator import generate_character
from wod_chargen.games.lotn_v5.backgrounds import background_defs
from wod_chargen.games.lotn_v5.merits_flaws import (
    MeritFlawCreationLedger,
    apply_trait_dots,
    effective_max_dots,
    max_trait_rating,
    run_merit_flaw_creation,
    trait_eligible,
    trait_increment,
    traits_for_type,
    xp_merit_purchase_cost,
)
from wod_chargen.games.lotn_v5.archetypes import effective_profile
from tests.support.fixtures import load_venue, opts as _opts


def _venue():
    return load_venue()


def test_trait_increment_rated_and_fixed():
    bond = next(m for m in traits_for_type("merit", "vampire") if m["id"] == "bond_resistance")
    assert trait_increment(bond, 0) == (1, 1)
    assert trait_increment(bond, 3) is None

    iron = next(m for m in traits_for_type("merit", "vampire") if m["id"] == "iron_gullet")
    assert trait_increment(iron, 0) == (3, 3)
    assert trait_increment(iron, 3) is None


def test_merit_flaw_creation_respects_cap():
    rng = SeededRng(12345)
    char = {"merits": {}, "flaws": {}}
    profile = effective_profile("diplomat", "silver_tongue", "vampire")
    lines, ledger = run_merit_flaw_creation(rng, char, profile, "vampire")
    assert ledger.merit_from_trade <= ledger.free_merit_cap
    assert ledger.merit_from_trade <= ledger.flaw_credit
    if ledger.merit_from_trade:
        assert any("flaw trade" in line.lower() for line in lines)


def test_generate_character_merits_within_catalog_caps():
    result = generate_character(4242, _opts(), _venue())
    for merit_id, rating in result.character["merits"].items():
        assert 0 < rating <= max_trait_rating(merit_id, "merit")
    for flaw_id, rating in result.character["flaws"].items():
        assert 0 < rating <= max_trait_rating(flaw_id, "flaw")


def test_xp_iron_gullet_costs_nine():
    iron = next(m for m in traits_for_type("merit", "vampire") if m["id"] == "iron_gullet")
    costs = load_json_cached("wod_chargen.games.lotn_v5.data", "costs.json")
    assert xp_merit_purchase_cost(iron, 0, costs) == 9


def test_merit_flaw_meta_recorded():
    result = generate_character(99, _opts(), _venue())
    meta = result.character.get("merit_flaw_meta", {})
    assert "flaw_credit" in meta
    assert "merit_from_trade" in meta
    assert meta["merit_from_trade"] <= MeritFlawCreationLedger().free_merit_cap


def test_merits_flaws_catalog_has_descriptions():
    catalog = load_json_cached("wod_chargen.games.lotn_v5.data", "merits_flaws.json")
    for kind in ("merits", "flaws"):
        for entry in catalog[kind]:
            assert entry.get("description"), f"{kind} {entry['id']} missing description"
            assert len(entry["description"]) >= 20


def _char(**kwargs):
    base = {
        "character_type": "vampire",
        "clan": "brujah",
        "generation": 13,
        "blood_potency": 1,
        "attributes": {"stamina": 2},
        "backgrounds": [],
        "merits": {},
        "flaws": {},
    }
    base.update(kwargs)
    return base


def test_cobbler_requires_mask_dots():
    cobbler = next(m for m in traits_for_type("merit", "vampire") if m["id"] == "cobbler")
    bare = _char()
    masked = _char(backgrounds=[{"type": "mask", "dots": 2, "label": "cover"}])
    assert not trait_eligible(cobbler, "merit", bare)
    assert trait_eligible(cobbler, "merit", masked)


def test_zeroed_and_known_blankbody_mutually_exclusive():
    zeroed = next(m for m in traits_for_type("merit", "vampire") if m["id"] == "zeroed")
    blank = next(f for f in traits_for_type("flaw", "vampire") if f["id"] == "known_blankbody")
    masked = _char(
        backgrounds=[{"type": "mask", "dots": 3, "label": "cover"}],
        flaws={"known_blankbody": 4},
    )
    assert not trait_eligible(zeroed, "merit", masked)
    assert not apply_trait_dots(masked.setdefault("merits", {}), "zeroed", "merit", 2, masked)


def test_unbondable_blocks_bonding_flaws():
    unbondable = next(m for m in traits_for_type("merit", "vampire") if m["id"] == "unbondable")
    long_bond = next(f for f in traits_for_type("flaw", "vampire") if f["id"] == "long_bond")
    char = _char(merits={"unbondable": 5})
    assert not trait_eligible(long_bond, "flaw", char)
    assert not trait_eligible(unbondable, "merit", _char(flaws={"long_bond": 2}))


def test_unbondable_not_xp_eligible():
    unbondable = next(m for m in traits_for_type("merit", "vampire") if m["id"] == "unbondable")
    assert not trait_eligible(unbondable, "merit", _char(), phase="xp")


def test_poor_blocks_resources_and_caps_haven():
    from wod_chargen.games.lotn_v5.backgrounds import can_add_dot, can_add_modifier_dot

    char = _char(
        flaws={"poor": 2},
        backgrounds=[{"type": "haven", "dots": 1, "advantages": [], "disadvantages": []}],
    )
    assert not can_add_dot(char["backgrounds"], "resources", background_defs()["resources"], char)
    assert not can_add_dot(char["backgrounds"], "haven", background_defs()["haven"], char)
    entry = char["backgrounds"][0]
    garage = next(m for m in background_defs()["haven"]["advantages"] if m["id"] == "garage")
    assert not can_add_modifier_dot(entry, garage, "advantage", char)


def test_enemy_one_per_sphere():
    from wod_chargen.games.lotn_v5.merits_flaws import apply_enemy_flaw, trait_eligible, traits_for_type

    enemy = next(f for f in traits_for_type("flaw", "vampire") if f["id"] == "enemy")
    char = _char()
    profile = effective_profile("diplomat", "silver_tongue", "vampire")
    added, key1 = apply_enemy_flaw(SeededRng(1), char, profile, 2)
    assert added == 2
    assert key1 and key1.startswith("enemy:")
    sphere1 = key1.split(":", 1)[1]
    added2, key2 = apply_enemy_flaw(SeededRng(2), char, profile, 1)
    assert added2 == 1
    assert key2 != key1
    assert key2.split(":", 1)[1] != sphere1
    from wod_chargen.games.lotn_v5.backgrounds import sphere_defs

    char2 = _char()
    for sphere in sphere_defs():
        char2["flaws"][f"enemy:{sphere['id']}"] = 3
    assert not trait_eligible(enemy, "flaw", char2)


def test_low_pain_threshold_scales_with_health():
    entry = next(f for f in traits_for_type("flaw", "vampire") if f["id"] == "low_pain_threshold")
    char = _char(attributes={"stamina": 2})
    assert effective_max_dots(entry, "flaw", char) == 2
    assert max_trait_rating("low_pain_threshold", "flaw", char) == 2
