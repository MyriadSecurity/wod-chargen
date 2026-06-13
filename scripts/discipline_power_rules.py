"""Structured eligibility rules for discipline powers (hand-curated overrides).

Auto-enrichment maps MES amalgam/prerequisite text; entries here override or
fill gaps (OR prereqs, import typos).
"""

from __future__ import annotations

from typing import Any

# power_id -> rules dict (merged into catalog by enrich_discipline_powers.py)
RULES: dict[str, dict[str, Any]] = {
    # Amalgams (discipline slug + min level)
    "unliving_hive": {"track": "discipline", "amalgam_discipline": "obfuscate", "amalgam_min_level": 2},
    "panacea": {"track": "discipline", "amalgam_discipline": "fortitude", "amalgam_min_level": 1},
    "possession": {"track": "discipline", "amalgam_discipline": "dominate", "amalgam_min_level": 3},
    "unburdening_the_bestial_soul": {
        "track": "discipline",
        "amalgam_discipline": "dominate",
        "amalgam_min_level": 3,
        "requires_all_powers": ["panacea"],
    },
    "unerring_aim": {"track": "discipline", "amalgam_discipline": "auspex", "amalgam_min_level": 2},
    "dementation": {"track": "discipline", "amalgam_discipline": "obfuscate", "amalgam_min_level": 2},
    "enduring_beasts": {"track": "discipline", "amalgam_discipline": "animalism", "amalgam_min_level": 1},
    "valeren": {"track": "discipline", "amalgam_discipline": "auspex", "amalgam_min_level": 1},
    "chimerstry": {"track": "discipline", "amalgam_discipline": "presence", "amalgam_min_level": 1},
    "fata_morgana": {"track": "discipline", "amalgam_discipline": "presence", "amalgam_min_level": 2},
    "arms_of_ahriman": {"track": "discipline", "amalgam_discipline": "potence", "amalgam_min_level": 2},
    "reaper_s_passing": {"track": "discipline", "amalgam_discipline": "dominate", "amalgam_min_level": 1},
    "eyes_of_the_serpent": {"track": "discipline", "amalgam_discipline": "protean", "amalgam_min_level": 1},
    "vicissitude": {"track": "discipline", "amalgam_discipline": "dominate", "amalgam_min_level": 2},
    "fleshcrafting": {
        "track": "discipline",
        "amalgam_discipline": "dominate",
        "amalgam_min_level": 2,
        "requires_all_powers": ["vicissitude"],
    },
    "abrupt_internment": {"track": "discipline", "amalgam_discipline": "auspex", "amalgam_min_level": 1},
    "horrid_form": {
        "track": "discipline",
        "amalgam_discipline": "dominate",
        "amalgam_min_level": 2,
        "requires_all_powers": ["vicissitude"],
    },
    "heart_of_darkness": {"track": "discipline", "amalgam_discipline": "fortitude", "amalgam_min_level": 2},
    "shape_mastery": {"track": "discipline", "amalgam_discipline": "presence", "amalgam_min_level": 2},
    # Power prerequisites
    "baal_s_caress": {"track": "discipline", "requires_all_powers": ["scorpion_s_touch"]},
    "conditioning": {"track": "discipline", "requires_all_powers": ["submerged_directive"]},
    "cache": {"track": "discipline", "requires_all_powers": ["conceal"]},
    "vanish_from_the_mind_s_eye": {
        "track": "discipline",
        "requires_any_powers": ["conceal", "unseen_passage"],
    },
    "metamorphosis": {"track": "discipline", "requires_all_powers": ["shapechange"]},
    # Rituals / ceremonies
    "blood_walk": {"track": "ritual", "requires_all_powers": ["a_taste_for_blood"]},
}

# Default track for each discipline catalog group
TRACK_BY_DISCIPLINE: dict[str, str] = {
    "blood_sorcery_rituals": "ritual",
    "ceremonies": "ceremony",
    "thin_blood_alchemy": "formula",
}

# MES amalgam display name -> discipline slug
AMALGAM_DISCIPLINE_SLUGS: dict[str, str] = {
    "Animalism": "animalism",
    "Auspex": "auspex",
    "Celerity": "celerity",
    "Dominate": "dominate",
    "Fortitude": "fortitude",
    "Obfuscate": "obfuscate",
    "Oblivion": "oblivion",
    "Potence": "potence",
    "Presence": "presence",
    "Protean": "protean",
    "Blood Sorcery": "blood_sorcery",
}
