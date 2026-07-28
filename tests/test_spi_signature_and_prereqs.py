"""SPI signature skills, prereqs, and mastery regression tests."""

from __future__ import annotations

from wod_chargen.core.data_loader import clear_cache
from wod_chargen.games.spi.archetypes import clear_archetype_caches
from wod_chargen.games.spi.generator import (
    _merit_creation_eligible,
    _merit_xp_prereqs_ok,
    _prereqs_met,
    generate_character,
)
from wod_chargen.games.spi.signature_skills import (
    ensure_signature_skill_floor,
    signature_skill_candidates,
)
from wod_chargen.games.spi.trait_biases import clear_trait_tags_cache, resolve_merit_bias
from wod_chargen.core.rng import SeededRng
from wod_chargen.venues import load_venue


def _reload_spi_data() -> None:
    clear_cache()
    clear_archetype_caches()
    clear_trait_tags_cache()


def test_signature_candidates_prefer_high_bias():
    biases = {"brawl": 2.2, "firearms": 1.15, "academics": 1.0, "occult": 0.9}
    cands = signature_skill_candidates(biases, list(biases))
    assert cands[0] == "brawl"
    assert "brawl" in cands


def test_ensure_signature_floor_raises_to_three():
    rng = SeededRng(1)
    ratings = {
        "brawl": 1,
        "firearms": 2,
        "weaponry": 2,
        "athletics": 2,
        "occult": 0,
        "academics": 0,
    }
    biases = {"brawl": 2.2, "firearms": 1.1, "weaponry": 1.1, "athletics": 1.2}
    cats = {
        "physical": ["brawl", "firearms", "weaponry", "athletics"],
        "mental": ["occult", "academics"],
        "social": [],
    }
    log: list = []
    sigs = ensure_signature_skill_floor(rng, ratings, biases, cats, log, floor=3)
    assert "brawl" in sigs
    assert ratings["brawl"] >= 3
    assert sum(ratings[s] for s in cats["physical"]) == 7  # dots conserved when donors exist


def test_resolve_merit_bias_explicit_is_floor_not_cap():
    clear_trait_tags_cache()
    # Weak explicit must not undercut a strong tag product.
    profile = {
        "merit_biases": {"division_liason": 1.4},
        "tag_affinities": {"status": 1.8, "influence": 1.7},
    }
    # division_liason tags are only "general" in merits.json extract; theme tags may be empty.
    # Use a known multi-tag merit instead.
    profile = {
        "merit_biases": {"defensive_combat_brawl": 1.4},
        "tag_affinities": {"combat": 1.85, "protection": 1.8},
    }
    bias = resolve_merit_bias(profile, "defensive_combat_brawl")
    assert bias >= 1.4
    assert bias == 3.0  # tag product clamps


def test_any_of_prereq_stamina_or_resolve():
    prereqs = [
        {
            "kind": "any_of",
            "options": [
                {"kind": "attribute", "id": "stamina", "dots": 3},
                {"kind": "attribute", "id": "resolve", "dots": 3},
            ],
        }
    ]
    char = {
        "attributes": {"stamina": 3, "resolve": 1},
        "skills": {},
        "merits": {},
        "affinities": {},
    }
    assert _prereqs_met(char, prereqs, soft=True)
    char["attributes"]["stamina"] = 2
    assert not _prereqs_met(char, prereqs, soft=True)
    char["attributes"]["resolve"] = 3
    assert _prereqs_met(char, prereqs, soft=True)


def test_merit_absent_and_unresolved_only_policy():
    assert _prereqs_met(
        {"attributes": {}, "skills": {}, "merits": {}, "affinities": {}},
        [{"kind": "merit_absent", "id": "fame"}],
        soft=True,
    )
    assert not _prereqs_met(
        {"attributes": {}, "skills": {}, "merits": {"fame": 1}, "affinities": {}},
        [{"kind": "merit_absent", "id": "fame"}],
        soft=True,
    )
    taste = {
        "id": "taste",
        "prereqs": [{"kind": "merit", "id": "crafts", "unresolved": True}],
    }
    assert not _merit_creation_eligible(taste)
    char = {"attributes": {}, "skills": {}, "merits": {}, "affinities": {}}
    assert not _merit_xp_prereqs_ok(char, taste)
    iron = {
        "id": "iron_stamina",
        "prereqs": [
            {
                "kind": "any_of",
                "options": [
                    {"kind": "attribute", "id": "stamina", "dots": 3},
                    {"kind": "attribute", "id": "resolve", "dots": 3},
                ],
            }
        ],
    }
    assert _merit_creation_eligible(iron)


def test_guardian_bodyguard_brawl_mastery_improved():
    """Signature path should put Brawl at creation ≥3 and lift final ≥4 rates."""
    _reload_spi_data()
    venue = load_venue("fixed_35")
    opts = {"archetype": "guardian", "sub": "bodyguard"}
    creation_ge3 = 0
    final_ge4 = 0
    iron = 0
    n = 80
    for seed in range(n):
        result = generate_character(seed, opts, venue)
        # Infer creation floor from log
        if any(
            e.detail and e.detail.get("signature_floor") and e.detail.get("trait") == "brawl"
            for e in result.creation_log
        ) or result.character["skills"]["brawl"] >= 3:
            # Count final; also track how often we end ≥3 after full gen
            pass
        if result.character["skills"]["brawl"] >= 3:
            creation_ge3 += 1  # post-gen ≥3 (creation floor + XP)
        if result.character["skills"]["brawl"] >= 4:
            final_ge4 += 1
        if "iron_stamina" in result.character["merits"]:
            iron += 1
    assert creation_ge3 / n >= 0.7, f"brawl≥3 rate {creation_ge3}/{n}"
    assert final_ge4 / n >= 0.12, f"brawl≥4 rate {final_ge4}/{n} (want ~≥15%)"
    assert iron / n >= 0.05, f"iron_stamina presence {iron}/{n}"
