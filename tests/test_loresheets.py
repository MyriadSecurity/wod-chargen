"""Loresheet catalog, eligibility, and weight tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from wod_chargen.core.data_loader import load_json_cached
from wod_chargen.games.lotn_v5.loresheets import (
    apply_loresheet_benefits,
    is_loresheet_eligible,
    loresheet_by_id,
    load_loresheets,
    resolve_loresheet_bias,
)
from wod_chargen.core.rng import SeededRng
from wod_chargen.games.lotn_v5.archetypes import effective_profile, load_all_archetypes
from wod_chargen.games.lotn_v5.generator import generate_character

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "wod_chargen/games/lotn_v5/data"


def test_pocket_book_loresheet_count():
    data = load_loresheets()
    assert len(data["loresheets"]) == 24
    assert data["rules"]["max_per_character"] == 1


def test_fixed_ids_from_mes_import():
    ids = set(loresheet_by_id())
    assert "descendant_of_hardestadt" in ids
    assert "descendant_of_xaviar" in ids
    assert "decendant_of_hardestadt" not in ids
    assert "descendant_of_xavier" not in ids


def test_all_archetypes_have_loresheet_biases():
    themes = json.loads((DATA / "loresheet_themes.json").read_text())
    theme_ids = set(themes["loresheets"])
    for arch_id in load_all_archetypes():
        raw = json.loads((DATA / "archetypes" / f"{arch_id}.json").read_text())
        bias_ids = set(raw.get("loresheet_biases", {}))
        assert bias_ids == theme_ids, arch_id


def test_clans_have_loresheet_biases():
    clans = load_json_cached("wod_chargen.games.lotn_v5.data", "clans.json")
    for clan_id, clan in clans.items():
        if clan_id == "thin_blood":
            continue
        assert "loresheet_biases" in clan
        assert isinstance(clan["loresheet_biases"], dict)


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


def test_vampire_at_most_one_loresheet_in_generation():
    venue = load_json_cached("wod_chargen.venues", "mes_end_to_dawn.json")
    for seed in range(40):
        char = generate_character(
            seed,
            {"type": "vampire", "clan": "brujah", "arch": "enforcer", "sub": "brawler", "approval": "2026-06"},
            venue,
        ).character
        assert len(char["loresheets"]) <= 1


@pytest.mark.parametrize("ls_id", sorted(loresheet_by_id()))
def test_loresheet_has_description_and_levels(ls_id: str):
    spec = loresheet_by_id()[ls_id]
    assert spec.get("description")
    assert len(spec["levels"]) == 3


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


def test_generated_characters_apply_loresheet_packages():
    venue = load_json_cached("wod_chargen.venues", "mes_end_to_dawn.json")
    found = False
    for seed in range(200):
        result = generate_character(
            seed,
            {
                "type": "vampire",
                "clan": "brujah",
                "arch": "enforcer",
                "sub": "brawler",
                "approval": "2026-06",
            },
            venue,
        )
        char = result.character
        if not char.get("loresheets"):
            continue
        found = True
        meta = char.get("loresheet_meta") or {}
        assert meta.get("id") in char["loresheets"]
        if meta.get("package_applied"):
            assert any(
                getattr(e, "phase", None) == "loresheet" for e in result.creation_log
            ) or char["backgrounds"] or char.get("merits")
            break
    assert found, "expected at least one generated character with a loresheet"
