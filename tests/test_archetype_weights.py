"""Cross-cutting archetype weight validation and seed smoke tests."""

from __future__ import annotations

import json
from pathlib import Path

from wod_chargen.games.lotn_v5.archetypes import effective_profile, load_all_archetypes
from wod_chargen.games.lotn_v5.trait_biases import resolve_trait_bias

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "wod_chargen/games/lotn_v5/data/archetypes/_manifest.json"


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
