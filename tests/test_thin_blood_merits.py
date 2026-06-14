"""Thin-blood merit/flaw pairs — separate from standard merits and flaws."""

import pytest

from wod_chargen.core.costs import lookup_cost
from wod_chargen.core.data_loader import load_json_cached
from wod_chargen.games.lotn_v5.generator import generate_character
from wod_chargen.games.lotn_v5.thin_blood_merits import has_thin_blood_alchemist
from tests.support.fixtures import load_venue, thin_blood_opts as _opts


def _venue():
    return load_venue("custom_xp")


def _tb_merit_flaw_counts(char: dict) -> tuple[int, int]:
    return len(char.get("thin_blood_merits", {})), len(char.get("thin_blood_flaws", {}))


def test_thin_blood_alchemist_grants_formula_and_tba():
    result = generate_character(1, _opts(), _venue())
    char = result.character
    assert char["thin_blood_merits"].get("thin_blood_alchemist")
    assert has_thin_blood_alchemist(char)
    assert char["disciplines"].get("thin_blood_alchemy", 0) >= 1
    assert char.get("thin_blood_formulas")
    assert not char.get("merits", {}).get("thin_blood_alchemist")


def test_discipline_affinity_grants_discipline_once():
    result = generate_character(13, _opts(), _venue())
    char = result.character
    assert char["thin_blood_merits"].get("discipline_affinity") == 1
    affinity = char["discipline_meta"]["affinity_discipline"]
    assert affinity != "thin_blood_alchemy"
    assert char["disciplines"].get(affinity, 0) >= 1
    assert char["thin_blood_flaws"]


def test_discipline_affinity_xp_uses_out_of_clan_cost():
    costs = load_json_cached("wod_chargen.games.lotn_v5.data", "costs.json")
    result = generate_character(13, _opts(), _venue())
    affinity = result.character["discipline_meta"]["affinity_discipline"]
    purchases = [
        e for e in result.xp_log if e.category == "discipline" and e.item == affinity
    ]
    assert purchases
    for entry in purchases:
        expected = lookup_cost(costs, "discipline_out_of_clan", new_level=entry.new_level)
        assert entry.cost == expected


def test_without_alchemist_no_tba_at_creation():
    result = generate_character(11, _opts(xp="0"), _venue())
    char = result.character
    assert not has_thin_blood_alchemist(char)
    assert char["disciplines"].get("thin_blood_alchemy", 0) == 0


def test_thin_blood_creation_takes_up_to_three_pairs():
    counts = []
    for seed in range(100):
        result = generate_character(seed, _opts(xp="0"), _venue())
        merits, flaws = _tb_merit_flaw_counts(result.character)
        counts.append(merits)
        assert merits == flaws
        assert 1 <= merits <= 3
    assert sum(1 for c in counts if c >= 2) >= 90
    assert sum(1 for c in counts if c == 3) >= 80


def test_thin_blood_high_xp_still_caps_at_three_pairs():
    counts = []
    for seed in range(50):
        result = generate_character(seed, _opts(), _venue())
        merits, _ = _tb_merit_flaw_counts(result.character)
        counts.append(merits)
        assert merits <= 3
    assert max(counts) == 3


@pytest.mark.parametrize("seed", range(15))
def test_resonance_discipline_stays_one_dot(seed: int):
    result = generate_character(seed, _opts(), _venue())
    char = result.character
    meta = char.get("discipline_meta") or {}
    resonance = meta.get("resonance_discipline")
    if not resonance:
        return
    assert meta.get("resonance_rating", 1) == 1
    resonance_xp = [
        e for e in result.xp_log if e.category == "discipline" and e.item == resonance
    ]
    assert not resonance_xp, f"seed {seed} spent XP on resonance discipline"


def test_thin_blood_disciplines_can_exceed_two_dots():
    """Affinity and TBA use the standard discipline cap (5), not a thin-blood 2-dot limit."""
    found = False
    for seed in range(200):
        result = generate_character(seed, _opts(), _venue())
        char = result.character
        meta = char.get("discipline_meta") or {}
        affinity = meta.get("affinity_discipline")
        tba = char["disciplines"].get("thin_blood_alchemy", 0)
        aff = char["disciplines"].get(affinity, 0) if affinity else 0
        if tba > 2 or aff > 2:
            found = True
            break
    assert found, "expected at least one seed to raise affinity or TBA above 2 dots with 300 XP"


def test_thin_blood_xp_prioritizes_disciplines():
    from wod_chargen.core.xp_strategy import macro_for_spend_group
    from wod_chargen.games.lotn_v5.thin_blood_merits import (
        has_merit_driven_disciplines,
        has_thin_blood_alchemist,
        has_discipline_affinity,
    )

    venue = load_venue()
    opts = {
        "type": "thin_blood",
        "arch": "alchemist",
        "sub": "distiller",
        "approval": "2026-06",
    }
    merit_macro = 0
    merit_total = 0
    both_disc = 0
    both_n = 0
    for seed in range(80):
        result = generate_character(seed, opts, venue)
        char = result.character
        if not has_merit_driven_disciplines(char):
            continue
        spent = sum(e.cost for e in result.xp_log if e.cost > 0)
        macro = sum(
            e.cost
            for e in result.xp_log
            if e.cost > 0 and macro_for_spend_group(e.spend_group) == "disciplines"
        )
        merit_macro += macro
        merit_total += spent
        if has_thin_blood_alchemist(char) and has_discipline_affinity(char):
            both_n += 1
            both_disc += sum(e.cost for e in result.xp_log if e.category == "discipline")
    assert merit_total > 0
    assert merit_macro / merit_total >= 0.10
    assert both_n >= 10
    assert both_disc / both_n >= 14


def test_control_seed_without_discipline_affinity():
    result = generate_character(4, _opts(xp="0"), _venue())
    assert not result.character["thin_blood_merits"].get("discipline_affinity")
    assert "affinity_discipline" not in (result.character.get("discipline_meta") or {})


def test_all_thin_bloods_have_resonance_discipline():
    from wod_chargen.games.lotn_v5.clan_discipline_adapt import char_clan_pool

    for seed in range(30):
        result = generate_character(seed, _opts(xp="0"), _venue())
        char = result.character
        meta = char.get("discipline_meta") or {}
        resonance = meta.get("resonance_discipline")
        assert resonance, f"seed {seed} missing resonance discipline"
        assert char["disciplines"].get(resonance, 0) >= 1
        assert char.get("discipline_powers", {}).get(resonance, {}).get("1")
        assert resonance not in char_clan_pool(char)


def test_resonance_discipline_reproducible():
    a = generate_character(42, _opts(xp="0"), _venue())
    b = generate_character(42, _opts(xp="0"), _venue())
    assert a.character["discipline_meta"]["resonance_discipline"] == b.character["discipline_meta"]["resonance_discipline"]


def test_thin_blood_merit_chars_do_not_always_max_disciplines():
    venue = load_venue()
    opts = {
        "type": "thin_blood",
        "arch": "alchemist",
        "sub": "distiller",
        "approval": "2026-06",
    }
    maxed = 0
    checked = 0
    for seed in range(120):
        result = generate_character(seed, opts, venue)
        char = result.character
        if not has_thin_blood_alchemist(char):
            continue
        checked += 1
        if char["disciplines"].get("thin_blood_alchemy", 0) >= 5:
            maxed += 1
    assert checked >= 50
    assert maxed / checked < 0.65


def test_thin_blood_xp_budget_accounts_correctly():
    venue = load_venue()
    opts = {
        "type": "thin_blood",
        "arch": "alchemist",
        "sub": "distiller",
        "predator": "extortionist",
        "approval": "2026-06",
    }
    result = generate_character(90672, opts, venue)
    assert result.xp_budget == 185
    assert result.xp_spent + result.xp_remaining == result.xp_budget
    assert result.xp_spent == sum(e.cost for e in result.xp_log)
    assert not any(e.source.endswith(":merit_discipline") for e in result.xp_log)


def test_seed_712885_mes_thin_blood_max_three_pairs():
    venue = load_venue()
    opts = {
        "type": "thin_blood",
        "arch": "alchemist",
        "sub": "distiller",
        "predator": "extortionist",
        "approval": "2026-06",
    }
    result = generate_character(712885, opts, venue)
    merits, flaws = _tb_merit_flaw_counts(result.character)
    assert merits == flaws
    assert merits <= 3
    validation = [
        e.message for e in result.creation_log if e.phase == "validation" and "Thin-Blood" in e.message
    ]
    assert not validation
