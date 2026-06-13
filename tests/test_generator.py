"""Generation integration tests."""

import pytest

from wod_chargen.core.data_loader import load_json_cached
from wod_chargen.games.lotn_v5.generator import generate_character
from wod_chargen.games.lotn_v5.archetypes import load_all_archetypes


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


def test_mes_xp_budget_only():
    result = generate_character(42, _opts(), _venue())
    assert result.xp_budget == 185
    assert result.xp_spent <= 185


def test_reproducibility_vampire():
    a = generate_character(999, _opts(), _venue())
    b = generate_character(999, _opts(), _venue())
    assert a.character == b.character
    assert len(a.xp_log) == len(b.xp_log)


def test_ghoul_no_loresheet_purchases():
    result = generate_character(
        7,
        _opts(type="ghoul", domitor_clan="tremere", arch="shadow", sub="spy"),
        _venue(),
    )
    assert all(e.category != "loresheet" for e in result.xp_log)


def test_ghoul_power_flat_cost():
    result = generate_character(
        12345,
        _opts(type="ghoul", domitor_clan="tremere", arch="enforcer", sub="tank"),
        _venue(),
    )
    power_purchases = [e for e in result.xp_log if e.category == "ghoul_power"]
    if power_purchases:
        assert all(e.cost == 10 for e in power_purchases)


def test_thin_blood_alchemist():
    result = generate_character(
        55,
        _opts(type="thin_blood", arch="alchemist", sub="distiller"),
        _venue(),
    )
    assert result.character["blood_potency"] == 0


@pytest.mark.parametrize("arch_id", [p.id for p in load_all_archetypes().values() if p.id != "alchemist"])
def test_reproducibility_per_archetype(arch_id: str):
    profile = load_all_archetypes()[arch_id]
    sub = profile.sub_archetypes[0].id
    opts = _opts(arch=arch_id, sub=sub)
    a = generate_character(1000, opts, _venue())
    b = generate_character(1000, opts, _venue())
    assert a.character == b.character


def _assert_caps(character: dict, *, discipline_cap: int = 5, formula_cap: int = 5) -> None:
    assert all(0 <= v <= 5 for v in character["attributes"].values())
    assert all(0 <= v <= 5 for v in character["skills"].values())
    assert all(0 <= v <= 5 for v in character["backgrounds"].values())
    assert all(0 <= v <= discipline_cap for v in character["disciplines"].values())
    assert all(0 <= v <= 3 for v in character["merits"].values())
    assert all(0 <= v <= 3 for v in character["loresheets"].values())
    assert all(0 <= v <= formula_cap for v in character["thin_blood_formulas"].values())
    assert all(0 <= v <= 1 for v in character["ghoul_powers"].values())
    if character["character_type"] == "vampire":
        assert character["blood_potency"] <= 3


@pytest.mark.parametrize("seed", range(50))
def test_vampire_ratings_respect_caps(seed: int):
    result = generate_character(seed, _opts(), _venue())
    _assert_caps(result.character)


@pytest.mark.parametrize("seed", range(20))
def test_ghoul_ratings_respect_caps(seed: int):
    result = generate_character(
        seed,
        _opts(type="ghoul", domitor_clan="tremere", arch="shadow", sub="spy"),
        _venue(),
    )
    _assert_caps(result.character)


@pytest.mark.parametrize("seed", range(20))
def test_thin_blood_ratings_respect_caps(seed: int):
    result = generate_character(
        seed,
        _opts(type="thin_blood", arch="alchemist", sub="distiller"),
        _venue(),
    )
    _assert_caps(result.character, discipline_cap=2, formula_cap=3)


def test_creation_backgrounds_each_assigned_once():
    """Seven 1-dot background picks each land on a distinct background."""
    for seed in range(50):
        result = generate_character(seed, _opts(), _venue())
        names = [
            _trait_from_log(entry.message)
            for entry in result.creation_log
            if entry.phase == "base" and entry.message.startswith("Background")
        ]
        assert len(names) == len(set(names)), f"seed {seed}: {names}"


def test_creation_log_shows_increment():
    result = generate_character(42, _opts(), _venue())
    skill_logs = [e.message for e in result.creation_log if e.phase == "base" and e.message.startswith("Skill")]
    assert skill_logs
    assert any(" +" in msg and "→" in msg for msg in skill_logs)


def _trait_from_log(message: str) -> str:
    return message.split()[1]


def test_each_creation_trait_assigned_once():
    """LoTN pool rules: one pool chunk per trait — no +4 then later +1 on same skill."""
    result = generate_character(1, _opts(), _venue())
    for prefix in ("Attribute", "Skill", "Background"):
        names = [
            _trait_from_log(entry.message)
            for entry in result.creation_log
            if entry.phase == "base" and entry.message.startswith(prefix)
        ]
        assert len(names) == len(set(names)), f"{prefix} reused across pool: {names}"


@pytest.mark.parametrize("seed", range(50))
def test_creation_traits_never_reused(seed: int):
    result = generate_character(seed, _opts(), _venue())
    for prefix in ("Attribute", "Skill", "Background"):
        names = [
            _trait_from_log(entry.message)
            for entry in result.creation_log
            if entry.phase == "base" and entry.message.startswith(prefix)
        ]
        assert len(names) == len(set(names)), f"seed {seed} {prefix}: {names}"


def test_creation_log_ordered_highest_to_lowest():
    result = generate_character(42, _opts(), _venue())
    tiers: list[int] = []
    for entry in result.creation_log:
        if entry.phase != "base" or entry.message.startswith("Predator"):
            continue
        pool_rating = entry.detail.get("pool_rating")
        if pool_rating is not None:
            tiers.append(int(pool_rating))
    assert tiers
    assert tiers == sorted(tiers, reverse=True)


def test_xp_spend_uses_multiple_categories():
    """Spend reaches multiple categories across seeds (not skills-only)."""
    from collections import Counter

    counts: Counter[str] = Counter()
    for seed in range(30):
        result = generate_character(seed, _opts(), _venue())
        counts.update(entry.category for entry in result.xp_log)
    assert counts["skill"] > 0
    assert counts["attribute"] > 0
    assert counts["background"] > 0
    assert counts["discipline"] > 0


def test_xp_spend_spreads_across_categories_over_seeds():
    """Individual builds may skew; the engine still covers all categories over time."""
    cats: set[str] = set()
    for seed in range(30):
        result = generate_character(seed, _opts(), _venue())
        cats.update(entry.category for entry in result.xp_log)
    assert len(cats) >= 4
