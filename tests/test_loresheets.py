"""Loresheet catalog, eligibility, and weight tests."""

from __future__ import annotations

from wod_chargen.games.lotn_v5.loresheets import (
    apply_loresheet_benefits,
    is_loresheet_eligible,
    load_loresheets,
    resolve_loresheet_bias,
)
from wod_chargen.core.rng import SeededRng
from wod_chargen.games.lotn_v5.archetypes import effective_profile


def test_loresheet_catalog_complete():
    data = load_loresheets()
    assert len(data["loresheets"]) == 24
    assert data["rules"]["max_per_character"] == 1
    for spec in data["loresheets"]:
        assert spec.get("description")
        assert len(spec["levels"]) == 3


def test_clan_restriction_blocks_wrong_clan():
    char = {"character_type": "vampire", "clan": "ventrue", "loresheets": {}}
    assert is_loresheet_eligible("descendant_of_tyler", char) is False
    assert is_loresheet_eligible("descendant_of_hardestadt", char) is True


def test_one_loresheet_rule():
    char = {
        "character_type": "vampire",
        "clan": "brujah",
        "loresheets": {"descendant_of_tyler": 1},
    }
    assert is_loresheet_eligible("descendant_of_tyler", char) is True
    assert is_loresheet_eligible("anarch_revolt", char) is False


def test_brujah_tyler_bias_beats_ventrue_hardestadt():
    profile = effective_profile("enforcer", "brawler", "vampire")
    brujah = {"character_type": "vampire", "clan": "brujah", "loresheets": {}}
    ventrue = {"character_type": "vampire", "clan": "ventrue", "loresheets": {}}
    tyler = resolve_loresheet_bias("descendant_of_tyler", profile, brujah)
    hardestadt = resolve_loresheet_bias("descendant_of_hardestadt", profile, ventrue)
    assert tyler > hardestadt


def test_loresheet_packages_apply_mechanical_benefits():
    profile = effective_profile("enforcer", "brawler", "vampire")
    rng = SeededRng(42)
    char = {
        "character_type": "vampire",
        "clan": "brujah",
        "loresheets": {"descendant_of_tyler": 1},
        "backgrounds": [],
        "skills": {},
        "merits": {},
    }
    caps = {"background": 3, "blood_potency": 3}
    lines = apply_loresheet_benefits(char, rng, profile, caps=caps)
    assert lines
    assert char.get("loresheet_meta", {}).get("package_applied") is True
    total_bg = sum(int(e.get("dots", 0)) for e in char["backgrounds"])
    assert total_bg >= 3


def test_firstlight_grants_mask_and_zeroed():
    profile = effective_profile("investigator", "detective", "vampire")
    rng = SeededRng(7)
    char = {
        "character_type": "vampire",
        "clan": "nosferatu",
        "loresheets": {"firstlight": 1},
        "backgrounds": [],
        "skills": {},
        "merits": {},
    }
    caps = {"background": 3, "blood_potency": 3}
    apply_loresheet_benefits(char, rng, profile, caps=caps)
    mask = [e for e in char["backgrounds"] if e.get("type") == "mask"]
    assert mask and mask[0]["dots"] >= 3
    assert char["merits"].get("zeroed", 0) >= 1


def test_firstlight_zeroed_log_matches_character_rating():
    """Loresheet merit log must not add a stray bullet before the rating display."""
    from wod_chargen.games.lotn_v5.generator import generate_character
    from wod_chargen.venues import load_venue

    opts = {
        "type": "vampire",
        "clan": "caitiff",
        "arch": "shadow",
        "sub": "infiltrator",
        "predator": "graverobber",
        "approval": "2026-06",
    }
    venue = load_venue("mes_end_to_dawn")
    result = None
    for seed in range(80):
        candidate = generate_character(seed, opts, venue)
        if "firstlight" not in candidate.character.get("loresheets", {}):
            continue
        if candidate.character.get("merits", {}).get("zeroed") != 2:
            continue
        result = candidate
        break
    assert result is not None, "expected firstlight + Zeroed •• within 80 seeds"
    zeroed = int(result.character["merits"]["zeroed"])
    assert zeroed == 2
    zeroed_logs = [e.message for e in result.creation_log if "Merit Zeroed" in e.message]
    assert len(zeroed_logs) == 1
    assert zeroed_logs[0].endswith(f"→ {'•' * zeroed}")
