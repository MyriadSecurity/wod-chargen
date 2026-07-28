"""SPI merit theme-tag bias resolution tests."""

from __future__ import annotations

from collections import Counter

from wod_chargen.games.spi.generator import generate_character
from wod_chargen.games.spi.trait_biases import (
    clear_trait_tags_cache,
    resolve_merit_bias,
    trait_tag_list,
)
from wod_chargen.venues import load_venue


def test_resolve_explicit_is_floor():
    clear_trait_tags_cache()
    profile = {
        "merit_biases": {"library": 2.0},
        "tag_affinities": {"academia": 1.5, "combat": 1.8},
    }
    # library theme tags do not include combat; explicit 2.0 remains the floor.
    assert resolve_merit_bias(profile, "library") == 2.0
    # Weak explicit must not undercut a strong tag product.
    combat_profile = {
        "merit_biases": {"defensive_combat_brawl": 1.4},
        "tag_affinities": {"combat": 1.85, "protection": 1.8},
    }
    assert resolve_merit_bias(combat_profile, "defensive_combat_brawl") == 3.0


def test_resolve_tag_product_and_default():
    clear_trait_tags_cache()
    tags = trait_tag_list("library")
    assert tags, "library should be theme-tagged"
    profile = {"merit_biases": {}, "tag_affinities": {"academia": 1.5, "information": 1.4}}
    bias = resolve_merit_bias(profile, "library")
    assert bias > 1.0
    assert resolve_merit_bias({"merit_biases": {}, "tag_affinities": {}}, "library") == 1.0


def test_investigator_veritas_rnd_prefers_investigation_over_combat_merits():
    """Seeded builds should lift investigation-tagged merits vs combat for this combo."""
    clear_trait_tags_cache()
    venue = load_venue("fixed_35")
    opts = {
        "archetype": "investigator",
        "division": "research_and_development",
        "faction": "veritas",
        "affinity": "mage",
        "multi_affinity": False,
    }
    inv_hits = 0
    combat_hits = 0
    for seed in range(40):
        result = generate_character(seed, opts, venue)
        for mid in result.character["merits"]:
            tags = set(trait_tag_list(mid))
            if "investigation" in tags or "information" in tags or "perception" in tags:
                inv_hits += 1
            if "combat" in tags:
                combat_hits += 1
    assert inv_hits > combat_hits, f"expected investigation-leaning merits, got inv={inv_hits} combat={combat_hits}"


def test_guardian_defense_lifts_combat_merits_vs_scholar():
    clear_trait_tags_cache()
    venue = load_venue("fixed_35")
    guardian_combat = Counter()
    scholar_combat = Counter()
    for seed in range(30):
        g = generate_character(
            seed,
            {
                "archetype": "guardian",
                "division": "defense",
                "faction": "humanity_first",
                "affinity": "vampire",
            },
            venue,
        )
        s = generate_character(
            seed,
            {
                "archetype": "scholar",
                "division": "research_and_development",
                "faction": "veritas",
                "affinity": "mage",
            },
            venue,
        )
        for mid in g.character["merits"]:
            if "combat" in trait_tag_list(mid):
                guardian_combat[mid] += 1
        for mid in s.character["merits"]:
            if "combat" in trait_tag_list(mid):
                scholar_combat[mid] += 1
    assert sum(guardian_combat.values()) > sum(scholar_combat.values())
