"""Generation integration tests."""

import pytest

from wod_chargen.core.data_loader import load_json_cached
from wod_chargen.games.lotn_v5.generator import generate_character
from wod_chargen.games.lotn_v5.merits_flaws import max_trait_rating
from wod_chargen.games.lotn_v5.archetypes import load_all_archetypes
from wod_chargen.games.lotn_v5.disciplines import power_by_id
from tests.support.fixtures import load_venue, opts as _opts


def _venue():
    return load_venue()


def test_user_selected_predator():
    result = generate_character(
        42,
        _opts(predator="farmer"),
        _venue(),
    )
    assert result.character["predator"] == "farmer"


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
    ctype = character.get("character_type", "vampire")
    assert all(0 <= v <= 5 for v in character["attributes"].values())
    assert all(0 <= v <= 5 for v in character["skills"].values())
    for entry in character["backgrounds"]:
        assert 1 <= entry["dots"] <= 3
    assert all(0 <= v <= discipline_cap for v in character["disciplines"].values())
    for merit_id, rating in character["merits"].items():
        cap = max_trait_rating(merit_id, "merit")
        if cap:
            assert 0 < rating <= cap
    for flaw_id, rating in character["flaws"].items():
        cap = max_trait_rating(flaw_id, "flaw")
        if cap:
            assert 0 < rating <= cap
    assert all(0 <= v <= 3 for v in character["loresheets"].values())
    assert len(character["loresheets"]) <= 1, "pocket book allows one loresheet per character"
    assert all(0 <= v <= formula_cap for v in character["thin_blood_formulas"].values())
    assert not character.get("ghoul_powers"), "ghoul XP powers belong in discipline_powers"
    for disc_id, rating in character.get("disciplines", {}).items():
        picks = character.get("discipline_powers", {}).get(disc_id, {})
        assert "1" in picks, f"missing primary power {disc_id}"
        power = power_by_id(picks["1"])
        assert power is not None
        if character["character_type"] != "ghoul":
            for level in range(1, int(rating) + 1):
                assert str(level) in picks, f"missing power {disc_id}@{level}"
                level_power = power_by_id(picks[str(level)])
                assert level_power is not None
                assert int(level_power["level"]) == level
    if character["character_type"] == "vampire":
        meta = character.get("generation_meta") or {}
        bp_cap = meta.get("max_blood_potency", 3)
        assert character["blood_potency"] <= bp_cap


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
    _assert_caps(result.character, discipline_cap=1)


@pytest.mark.parametrize("seed", range(20))
def test_thin_blood_ratings_respect_caps(seed: int):
    result = generate_character(
        seed,
        _opts(type="thin_blood", arch="alchemist", sub="distiller"),
        _venue(),
    )
    _assert_caps(result.character, discipline_cap=5, formula_cap=3)


def test_creation_backgrounds_assign_seven_dots():
    """Seven free pool dots are fully allocated (connections, modifiers, or unplaced)."""
    for seed in range(30):
        result = generate_character(seed, _opts(), _venue())
        pool = result.character["background_meta"]["creation_pool"]
        spent = pool["connection"] + pool["modifier"] + pool.get("unplaced", 0)
        assert spent == pool["total"], f"seed {seed}"


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
    for prefix in ("Attribute", "Skill"):
        names = [
            _trait_from_log(entry.message)
            for entry in result.creation_log
            if entry.phase == "base" and entry.message.startswith(prefix)
        ]
        assert len(names) == len(set(names)), f"{prefix} reused across pool: {names}"


@pytest.mark.parametrize("seed", range(50))
def test_creation_traits_never_reused(seed: int):
    result = generate_character(seed, _opts(), _venue())
    for prefix in ("Attribute", "Skill"):
        names = [
            _trait_from_log(entry.message)
            for entry in result.creation_log
            if entry.phase == "base" and entry.message.startswith(prefix)
        ]
        assert len(names) == len(set(names)), f"seed {seed} {prefix}: {names}"


def _creation_log_category(message: str) -> int:
    if message.startswith("Attribute"):
        return 0
    if message.startswith("Skill"):
        return 1
    if message.startswith("Discipline"):
        return 2
    if message.startswith(("Background", "Creation pool")):
        return 3
    return 99


def test_creation_log_ordered_by_category_then_rating():
    """Within each category, higher pool tiers are assigned before lower ones."""
    result = generate_character(42, _opts(), _venue())
    by_category: dict[int, list[int]] = {}
    category_sequence: list[int] = []
    for entry in result.creation_log:
        if entry.phase != "base" or entry.message.startswith("Predator"):
            continue
        cat = _creation_log_category(entry.message)
        if cat == 99:
            continue
        if not category_sequence or category_sequence[-1] != cat:
            category_sequence.append(cat)
        pool_rating = entry.detail.get("pool_rating")
        if pool_rating is not None:
            by_category.setdefault(cat, []).append(int(pool_rating))

    assert category_sequence == sorted(category_sequence)
    for cat, tiers in by_category.items():
        assert tiers == sorted(tiers, reverse=True), f"category {cat}: {tiers}"


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
