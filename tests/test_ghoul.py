"""Ghoul per-power XP picks and sheet metadata."""

import pytest

from wod_chargen.core.data_loader import load_json_cached
from wod_chargen.games.lotn_v5.disciplines import enumerate_ghoul_power_candidates, power_by_id
from wod_chargen.games.lotn_v5.generator import generate_character


def _venue():
    return load_json_cached("wod_chargen.venues", "custom_xp.json")


def _opts(**kwargs):
    base = {
        "type": "ghoul",
        "domitor_clan": "tremere",
        "arch": "shadow",
        "sub": "spy",
        "xp": "200",
    }
    base.update(kwargs)
    return base


def test_ghoul_has_no_generation_field():
    result = generate_character(42, _opts(), _venue())
    assert "generation" not in result.character
    assert result.character.get("blood_potency") == 0


def test_ghoul_power_xp_uses_level_one_power_ids():
    result = generate_character(88, _opts(), _venue())
    ghoul_powers = result.character.get("ghoul_powers", {})
    assert ghoul_powers, "expected ghoul power XP purchases"
    for power_id in ghoul_powers:
        power = power_by_id(power_id)
        assert power is not None, f"unknown ghoul power id: {power_id}"
        assert int(power["level"]) == 1
        assert power_id not in ("potence", "celerity", "dominate", "auspex", "blood_sorcery")


def test_ghoul_power_candidates_exclude_creation_picks():
    result = generate_character(12, _opts(xp="0"), _venue())
    char = result.character
    owned = set()
    for picks in char.get("discipline_powers", {}).values():
        owned.update(picks.values())
    candidates = enumerate_ghoul_power_candidates(char)
    candidate_ids = {p["id"] for p in candidates}
    assert not candidate_ids & owned


@pytest.mark.parametrize("seed", range(20))
def test_ghoul_power_candidates_from_domitor_pool(seed: int):
    result = generate_character(seed, _opts(xp="0"), _venue())
    char = result.character
    pool = {"auspex", "blood_sorcery", "dominate"}
    for power in enumerate_ghoul_power_candidates(char):
        assert power["discipline_id"] in pool
