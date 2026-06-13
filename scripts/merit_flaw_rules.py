"""Structured prerequisite and exclusion rules for LoTN merits and flaws.

Source: Laws of the Night pocket book, Chapter 7 (Merits & Flaws).
Merged into merits_flaws.json by scripts/enrich_merits_flaws_descriptions.py.
"""

from __future__ import annotations

from typing import Any

# id -> rules object (omit empty / default-only entries)
RULES: dict[str, dict[str, Any]] = {
    # Bonding
    "unbondable": {
        "creation_only": True,
        "forbidden_with_categories": [{"kind": "flaw", "category": "bonding"}],
    },
    "short_bond": {"forbidden_with": ["long_bond"]},
    "long_bond": {"forbidden_with": ["short_bond", "unbondable"]},
    "bond_at_first_taste": {"forbidden_with": ["unbondable"]},
    "bond_junkie": {"forbidden_with": ["unbondable"]},
    "symbiotic_dependency": {"forbidden_with": ["unbondable"]},
    # Connection
    "cobbler": {"requires_background_min": {"mask": 2}},
    "zeroed": {
        "requires_background_min": {"mask": 3},
        "forbidden_with": ["known_blankbody"],
    },
    "known_corpse": {"requires_background_max": {"mask": 0}},
    "known_blankbody": {
        "requires_background_max": {"mask": 0},
        "forbidden_with": ["zeroed"],
    },
    "enemy": {
        "instance_key": "sphere",
        "max_dots_per_instance": 3,
    },
    "poor": {},
    "no_haven": {},
    # Feeding
    "iron_gullet": {
        "forbidden_clans": ["ventrue"],
        "requires_max_blood_potency": 2,
    },
    "farmer": {"requires_max_blood_potency": 2},
    # Physical
    "low_pain_threshold": {"max_dots_from_health_minus": 3},
    # Psychological
    "archaic": {"requires_max_generation": 9},
    "dark_secret": {"max_per_character": 1},
    # Thin-blood pairs
    "lifelike": {"forbidden_with": ["dead_flesh"]},
    "dead_flesh": {"forbidden_with": ["lifelike"]},
    "vampiric_resilience": {"forbidden_with": ["mortal_frailty"]},
    "mortal_frailty": {"forbidden_with": ["vampiric_resilience"]},
    "anarch_comrades": {"forbidden_with": ["shunned_by_the_anarchs"]},
    "shunned_by_the_anarchs": {"forbidden_with": ["anarch_comrades"]},
}
