"""Ghoul per-power XP picks and sheet metadata."""

import pytest

from wod_chargen.core.data_loader import load_json_cached
from wod_chargen.games.lotn_v5.disciplines import (
    discipline_power_ids_for_track,
    enumerate_ghoul_power_candidates,
    ghoul_domitor_discipline_pool,
    owned_power_ids,
    power_by_id,
    powers_for_level,
)
from wod_chargen.games.lotn_v5.generator import generate_character
from tests.support.fixtures import CUSTOM_XP_VENUE, ghoul_opts as _opts, load_venue


def _venue():
    return load_venue(CUSTOM_XP_VENUE)


def test_ghoul_has_no_generation_field():
    result = generate_character(42, _opts(), _venue())
    assert "generation" not in result.character
    assert result.character.get("blood_potency") == 0


def test_ghoul_power_xp_uses_level_one_power_ids():
    result = generate_character(88, _opts(), _venue())
    char = result.character
    assert not char.get("ghoul_powers"), "XP powers should live under discipline_powers"
    extras = [
        pid
        for disc_id in char.get("discipline_powers", {})
        for pid in discipline_power_ids_for_track(char, disc_id)
    ]
    assert len(extras) >= 3, "expected ghoul power XP purchases"
    for power_id in extras:
        power = power_by_id(power_id)
        assert power is not None, f"unknown ghoul power id: {power_id}"
        assert int(power["level"]) == 1
        assert power_id not in ("potence", "celerity", "dominate", "auspex", "blood_sorcery")


def test_ghoul_power_candidates_exclude_creation_picks():
    result = generate_character(12, _opts(xp="0"), _venue())
    char = result.character
    owned = owned_power_ids(char)
    candidates = enumerate_ghoul_power_candidates(char)
    candidate_ids = {p["id"] for p in candidates}
    assert not candidate_ids & owned


def test_ghoul_discipline_ratings_stay_at_one():
    result = generate_character(42, _opts(), _venue())
    for rating in result.character["disciplines"].values():
        assert rating == 1


def test_ghoul_xp_never_buys_discipline_dots_or_rituals():
    result = generate_character(88, _opts(), _venue())
    assert not any(e.category == "discipline" for e in result.xp_log)
    assert not any(e.category in ("ritual", "ceremony") for e in result.xp_log)


def test_ghoul_merit_pool_excludes_kindred_categories():
    from wod_chargen.games.lotn_v5.merits_flaws import traits_for_type

    ghoul_merits = {e["id"] for e in traits_for_type("merit", "ghoul")}
    ghoul_flaws = {e["id"] for e in traits_for_type("flaw", "ghoul")}
    assert "blood_empathy" in ghoul_merits
    assert "bloodhound" in ghoul_merits
    assert "weak_stomach" in ghoul_flaws
    assert "bond_resistance" not in ghoul_merits
    assert "zeroed" not in ghoul_merits
    assert "thin_blood_alchemist" not in ghoul_merits
    assert "iron_gullet" not in ghoul_merits
    assert "viscosity" not in ghoul_merits
    assert "farmer" not in ghoul_flaws
    assert "prey_exclusion" not in ghoul_flaws
    assert "calm_heart" not in ghoul_merits
    assert "eat_food" not in ghoul_merits


_FORBIDDEN_GHOUL_TRAITS = {
    "farmer",
    "methuselah_s_thirst",
    "organovore",
    "prey_exclusion",
    "iron_gullet",
    "viscosity",
    "calm_heart",
    "bestial_temper",
    "eat_food",
}


@pytest.mark.parametrize("seed", range(100))
def test_ghoul_never_gets_kindred_feeding_or_frenzy_traits(seed: int):
    result = generate_character(seed, _opts(), _venue())
    assigned = set()
    for bucket in ("merits", "flaws", "thin_blood_merits", "thin_blood_flaws"):
        assigned |= {k.split(":")[0] for k in result.character.get(bucket, {})}
    assert not assigned & _FORBIDDEN_GHOUL_TRAITS, f"seed {seed}: {assigned & _FORBIDDEN_GHOUL_TRAITS}"


@pytest.mark.parametrize("seed", range(20))
def test_ghoul_power_candidates_from_domitor_pool(seed: int):
    result = generate_character(seed, _opts(xp="0"), _venue())
    char = result.character
    pool = set(ghoul_domitor_discipline_pool(char))
    assert pool, "expected domitor discipline pool"
    for power in enumerate_ghoul_power_candidates(char):
        assert power["discipline_id"] in pool


def test_caitiff_domitor_ghoul_uses_three_disciplines_not_full_catalog():
    result = generate_character(
        539689,
        _opts(domitor_clan="caitiff", arch="occultist", sub="ritualist"),
        _venue(),
    )
    char = result.character
    domitor_pool = char.get("domitor_disciplines") or []
    assert len(domitor_pool) == 3

    owned = owned_power_ids(char)
    max_pool_powers = sum(len(powers_for_level(d, 1)) for d in domitor_pool)
    assert len(owned) <= max_pool_powers
    for power_id in owned:
        assert power_by_id(power_id)["discipline_id"] in domitor_pool

    assert not char.get("ghoul_powers"), "powers must not duplicate in ghoul_powers bucket"


@pytest.mark.parametrize("seed", range(20))
def test_ghoul_powers_only_in_discipline_powers(seed: int):
    result = generate_character(
        seed,
        _opts(domitor_clan="caitiff", arch="occultist", sub="ritualist"),
        _venue(),
    )
    assert not result.character.get("ghoul_powers")
