"""Cross-cutting archetype weight validation and seed smoke tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from wod_chargen.games.lotn_v5.archetypes import effective_profile, load_all_archetypes
from wod_chargen.core.data_loader import load_json_cached
from wod_chargen.games.lotn_v5.generator import generate_character
from wod_chargen.games.lotn_v5.trait_biases import resolve_trait_bias
from tests.support.fixtures import load_venue, opts

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "wod_chargen/games/lotn_v5/data/archetypes/_manifest.json"


def _venue():
    return load_venue()


def _opts(**kwargs):
    base = {
        "type": "vampire",
        "clan": "brujah",
        "arch": "diplomat",
        "sub": "courtier",
        "approval": "2026-06",
    }
    base.update(kwargs)
    return base


def test_all_profiles_load_without_orphans():
    profiles = load_all_archetypes()
    manifest = json.loads(MANIFEST.read_text())
    assert set(profiles) == set(manifest["primaries"])
    for arch_id, profile in profiles.items():
        ctype = profile.allowed_types[0] if profile.allowed_types else "vampire"
        for sub in profile.sub_archetypes:
            effective_profile(arch_id, sub.id, ctype)


def test_diplomat_tag_bias_skews_social_skills():
    profile = effective_profile("diplomat", "silver_tongue", "vampire")
    social = resolve_trait_bias(profile, "persuasion", "skills")
    combat = resolve_trait_bias(profile, "brawl", "skills")
    assert social > combat


def test_shadow_suppresses_fame_background():
    profile = effective_profile("shadow", "spy", "vampire")
    assert resolve_trait_bias(profile, "fame", "backgrounds") < 1.0


@pytest.mark.parametrize(
    "arch_id,sub_id,ctype,clan",
    [
        ("diplomat", "courtier", "vampire", "brujah"),
        ("enforcer", "brawler", "vampire", "brujah"),
        ("shadow", "spy", "vampire", "nosferatu"),
        ("scholar", "loremaster", "vampire", "tremere"),
        ("alchemist", "chemist", "thin_blood", "thin_blood"),
    ],
)
def test_generation_seed_stable(arch_id: str, sub_id: str, ctype: str, clan: str):
    opts = _opts(type=ctype, clan=clan, arch=arch_id, sub=sub_id)
    a = generate_character(42, opts, _venue()).character
    b = generate_character(42, opts, _venue()).character
    assert a["skills"] == b["skills"]
    assert a.get("discipline_powers") == b.get("discipline_powers")


def test_thirty_seed_diplomat_skills_skew_social():
    social_count = 0
    for seed in range(30):
        char = generate_character(seed, _opts(arch="diplomat", sub="courtier"), _venue()).character
        top = max(char["skills"], key=char["skills"].get)
        if top in ("persuasion", "politics", "etiquette", "subterfuge", "insight"):
            social_count += 1
    assert social_count >= 8
