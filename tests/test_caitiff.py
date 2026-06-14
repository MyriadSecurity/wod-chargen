"""Caitiff discipline pool and XP pricing."""

import pytest

from wod_chargen.core.costs import lookup_cost
from wod_chargen.core.data_loader import load_json_cached
from wod_chargen.games.lotn_v5.disciplines import caitiff_discipline_pool, discipline_pool_for_char
from wod_chargen.games.lotn_v5.generator import generate_character


def _venue():
    return load_json_cached("wod_chargen.venues", "custom_xp.json")


def _opts(**kwargs):
    base = {
        "type": "vampire",
        "clan": "caitiff",
        "arch": "diplomat",
        "sub": "silver_tongue",
        "xp": "500",
    }
    base.update(kwargs)
    return base


def test_caitiff_discipline_pool_excludes_thin_blood_alchemy():
    pool = caitiff_discipline_pool()
    assert "thin_blood_alchemy" not in pool
    assert len(pool) >= 10


def test_discipline_pool_for_caitiff_character():
    char = {"clan": "caitiff", "character_type": "vampire"}
    assert discipline_pool_for_char(char, "vampire") == caitiff_discipline_pool()


def test_caitiff_creation_three_distinct_disciplines():
    result = generate_character(42, _opts(xp="0"), _venue())
    char = result.character
    assert char["clan"] == "caitiff"
    discs = char["disciplines"]
    assert len(discs) == 3
    assert len(set(discs)) == 3
    ratings = sorted(discs.values(), reverse=True)
    assert ratings == [2, 1, 1]
    for disc_id, rating in discs.items():
        picks = char["discipline_powers"][disc_id]
        for level in range(1, rating + 1):
            assert str(level) in picks
            power = char["discipline_powers"][disc_id][str(level)]
            assert power


@pytest.mark.parametrize("seed", range(20))
def test_caitiff_ratings_respect_caps(seed: int):
    result = generate_character(seed, _opts(), _venue())
    char = result.character
    assert char["disciplines"]
    assert all(0 <= v <= 5 for v in char["disciplines"].values())
    assert len(char["disciplines"]) >= 1


def test_caitiff_discipline_xp_uses_six_times_multiplier():
    costs = load_json_cached("wod_chargen.games.lotn_v5.data", "costs.json")
    result = generate_character(77, _opts(), _venue())
    disc_purchases = [e for e in result.xp_log if e.category == "discipline"]
    assert disc_purchases, "expected at least one discipline XP purchase"
    for entry in disc_purchases:
        new_level = entry.new_level
        expected = lookup_cost(costs, "discipline_caitiff", new_level=new_level)
        assert entry.cost == expected


def test_caitiff_xp_only_deepens_creation_disciplines():
    venue = load_json_cached("wod_chargen.venues", "mes_end_to_dawn.json")
    opts = {
        "type": "vampire",
        "clan": "caitiff",
        "arch": "diplomat",
        "sub": "silver_tongue",
        "approval": "2026-06",
    }
    for seed in range(50):
        creation = generate_character(seed, {**opts, "xp": "0"}, venue)
        full = generate_character(seed, opts, venue)
        assert set(full.character["disciplines"]) == set(creation.character["disciplines"])
        assert len(full.character["disciplines"]) == 3
