"""Generation and Blood Potency assignment tests."""

from wod_chargen.core.data_loader import load_json_cached
from wod_chargen.games.lotn_v5.generation import (
    apply_mandatory_blood_potency,
    assign_generation_and_blood_potency,
    pick_generation_number,
)
from wod_chargen.games.lotn_v5.generator import generate_character
from wod_chargen.core.rng import SeededRng
from tests.support.fixtures import load_venue, opts as _opts


def _venue():
    return load_venue()


def test_vampire_generation_varies_across_seeds():
    generations = {
        generate_character(seed, _opts(), _venue()).character["generation"]
        for seed in range(100)
    }
    assert len(set(generations)) > 1
    assert all(9 <= g <= 13 for g in generations)


def test_explicit_generation_option():
    result = generate_character(1, _opts(generation=11), _venue())
    assert result.character["generation"] == 11
    assert result.character["generation_meta"]["max_blood_potency"] == 4


def test_ninth_generation_mandatory_blood_potency():
    result = generate_character(1, _opts(generation=9), _venue())
    assert result.character["generation"] == 9
    assert result.character["blood_potency"] >= 2
    mandatory = [e for e in result.xp_log if e.source == "mandatory"]
    assert mandatory
    assert mandatory[0].category == "blood_potency"
    assert mandatory[0].cost == 20


def test_thin_blood_generation_range():
    generations = {
        generate_character(
            seed,
            _opts(type="thin_blood", arch="alchemist", sub="distiller"),
            _venue(),
        ).character["generation"]
        for seed in range(50)
    }
    assert all(14 <= g <= 16 for g in generations)
    assert len(set(generations)) > 1


def test_ghoul_has_no_generation_meta():
    result = generate_character(
        3,
        _opts(type="ghoul", domitor_clan="tremere", arch="shadow", sub="spy"),
        _venue(),
    )
    assert result.character["blood_potency"] == 0
    assert "generation_meta" not in result.character


def test_blood_potency_cap_follows_generation():
    result = generate_character(5, _opts(generation=10), _venue())
    cap = result.character["generation_meta"]["max_blood_potency"]
    assert cap == 4
    assert result.character["blood_potency"] <= cap


def test_pick_generation_respects_venue_bounds():
    rng = SeededRng(99)
    creation = load_json_cached("wod_chargen.games.lotn_v5.data", "creation.json")
    venue = _venue()
    for _ in range(50):
        gen = pick_generation_number(rng, "vampire", venue, creation)
        assert venue["house_rules"]["min_generation"] <= gen <= venue["house_rules"]["max_generation"]


def test_generation_below_venue_minimum_rejected():
    import pytest

    with pytest.raises(ValueError, match="not allowed"):
        generate_character(1, _opts(generation=8), _venue())


def test_apply_mandatory_blood_potency_shortfall():
    char = {
        "generation": 9,
        "blood_potency": 1,
        "generation_meta": {"min_blood_potency": 2, "label": "9th Generation"},
    }
    costs = load_json_cached("wod_chargen.games.lotn_v5.data", "costs.json")
    remaining, xp_entries, logs = apply_mandatory_blood_potency(char, costs, budget=5)
    assert remaining == 5
    assert char["blood_potency"] == 1
    assert not xp_entries
    assert any("shortfall" in (e.detail or {}) for e in logs)


def test_mandatory_blood_potency_only_for_ninth_gen_pcs():
    """9th is the PC floor at MES; only eligible gen with min BP 2."""
    result = generate_character(1, _opts(generation=9), _venue())
    mandatory = [e for e in result.xp_log if e.source == "mandatory"]
    assert mandatory
    assert mandatory[0].cost == 20

    result = generate_character(1, _opts(generation=10), _venue())
    assert not [e for e in result.xp_log if e.source == "mandatory"]


def test_no_mandatory_when_starting_meets_minimum():
    char = {
        "generation": 12,
        "blood_potency": 1,
        "generation_meta": {"min_blood_potency": 1, "label": "12th Generation"},
    }
    costs = load_json_cached("wod_chargen.games.lotn_v5.data", "costs.json")
    remaining, xp_entries, logs = apply_mandatory_blood_potency(char, costs, budget=185)
    assert remaining == 185
    assert not xp_entries
    assert not logs
