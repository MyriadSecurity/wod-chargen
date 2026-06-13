#!/usr/bin/env python3
"""Merge archetype families per v1 simplification and rewrite player copy."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ARCH = ROOT / "wod_chargen" / "games" / "lotn_v5" / "data" / "archetypes"

REMOVED = ("face", "bruiser", "hunter", "beast", "survivor")

MERGED_BASES: dict[str, dict] = {
    "diplomat": {
        "id": "diplomat",
        "label": "The Diplomat",
        "description": (
            "Your coterie sends you to Elysium because you can stand a room full of "
            "hungry aristocrats and still look like you belong. You speak for the group, "
            "trade favors between factions, and keep the knives sheathed long enough to matter."
        ),
        "weights": {
            "physical_attrs": 0.45,
            "social_attrs": 1.9,
            "mental_attrs": 1.1,
            "skills": 1.55,
            "in_clan_disciplines": 1.15,
            "backgrounds": 1.45,
            "merits": 0.75,
        },
        "attribute_biases": {
            "charisma": 1.5,
            "manipulation": 1.45,
            "composure": 1.25,
        },
        "skill_biases": {
            "persuasion": 2.0,
            "politics": 1.7,
            "etiquette": 1.5,
            "subterfuge": 1.3,
            "insight": 1.2,
        },
        "discipline_biases": {"presence": 1.65, "dominate": 1.2},
    },
    "enforcer": {
        "id": "enforcer",
        "label": "The Enforcer",
        "description": (
            "When the Prince needs a message delivered in bruises, you're the one who "
            "shows up on time. You break legs, collect debts, and win the fight that was "
            "never supposed to become a fair match."
        ),
        "weights": {
            "physical_attrs": 1.9,
            "social_attrs": 0.75,
            "mental_attrs": 0.55,
            "skills": 1.45,
            "in_clan_disciplines": 1.25,
            "backgrounds": 0.9,
            "merits": 0.65,
        },
        "attribute_biases": {
            "strength": 1.7,
            "stamina": 1.5,
            "charisma": 1.1,
        },
        "skill_biases": {
            "intimidation": 2.0,
            "brawl": 1.8,
            "athletics": 1.3,
            "melee": 1.3,
            "streetwise": 1.2,
        },
        "discipline_biases": {"potence": 1.7, "fortitude": 1.35, "presence": 1.25},
    },
    "predator": {
        "id": "predator",
        "label": "The Predator",
        "description": (
            "You notice who moved through a place before the rest of the city wakes up. "
            "Tail a target for nights, read a territory like a map, and when hunger wins "
            "you don't bother pretending to be civilized."
        ),
        "weights": {
            "physical_attrs": 1.6,
            "social_attrs": 0.5,
            "mental_attrs": 1.0,
            "skills": 1.6,
            "in_clan_disciplines": 1.35,
            "backgrounds": 0.8,
            "merits": 0.7,
        },
        "attribute_biases": {
            "dexterity": 1.45,
            "stamina": 1.45,
            "wits": 1.35,
            "strength": 1.2,
        },
        "skill_biases": {
            "survival": 1.7,
            "stealth": 1.5,
            "awareness": 1.4,
            "animal_ken": 1.4,
            "brawl": 1.2,
            "firearms": 1.1,
        },
        "discipline_biases": {
            "protean": 1.5,
            "animalism": 1.4,
            "celerity": 1.3,
            "potence": 1.1,
        },
        "type_weights": {"ghoul": {"in_clan_disciplines": 0.65}},
    },
    "criminal": {
        "id": "criminal",
        "label": "The Criminal",
        "description": (
            "You know which pawn shop doesn't ask questions and which alley still has "
            "a working exit. Stolen goods, side deals, and the stubborn habit of staying "
            "alive when the night turns ugly."
        ),
        "weights": {
            "physical_attrs": 1.15,
            "social_attrs": 0.95,
            "mental_attrs": 1.1,
            "skills": 1.75,
            "in_clan_disciplines": 1.0,
            "backgrounds": 1.2,
            "merits": 0.75,
        },
        "attribute_biases": {
            "dexterity": 1.4,
            "wits": 1.4,
            "stamina": 1.2,
            "manipulation": 1.15,
        },
        "skill_biases": {
            "streetwise": 2.0,
            "larceny": 1.9,
            "subterfuge": 1.35,
            "survival": 1.2,
            "awareness": 1.1,
            "drive": 1.1,
        },
        "discipline_biases": {"obfuscate": 1.35, "celerity": 1.15, "fortitude": 1.05},
        "type_weights": {"ghoul": {"in_clan_disciplines": 0.6}},
    },
}

SUB_COPY: dict[str, dict[str, dict]] = {
    "diplomat": {
        "silver_tongue": {
            "label": "Silver Tongue",
            "description": "You talk people into the deal they were already circling.",
            "modifiers": {
                "weights": {"skills": 0.25},
                "skill_biases": {"persuasion": 0.45, "subterfuge": 0.25},
                "discipline_biases": {"presence": 0.25},
            },
        },
        "socialite": {
            "label": "Socialite",
            "description": "You know whose hand to shake and whose drink to avoid.",
            "modifiers": {
                "weights": {"social_attrs": 0.15, "backgrounds": 0.15},
                "skill_biases": {"etiquette": 0.35, "insight": 0.15},
            },
        },
        "negotiator": {
            "label": "Negotiator",
            "description": "You find the number, the truce, or the threat everyone can swallow.",
            "modifiers": {
                "weights": {"backgrounds": 0.1},
                "skill_biases": {"politics": 0.35, "persuasion": 0.2},
                "discipline_biases": {"dominate": 0.15},
            },
        },
        "harpy_aspirant": {
            "label": "Harpy Aspirant",
            "description": "You live for status games and public embarrassment.",
            "modifiers": {
                "weights": {"social_attrs": 0.2, "merits": 0.1},
                "skill_biases": {"politics": 0.3, "etiquette": 0.2},
                "discipline_biases": {"presence": 0.2},
            },
        },
    },
    "enforcer": {
        "tank": {
            "label": "Tank",
            "description": "You absorb the hit and keep coming.",
            "modifiers": {
                "weights": {"physical_attrs": 0.2, "in_clan_disciplines": 0.1},
                "attribute_biases": {"stamina": 0.3},
                "discipline_biases": {"fortitude": 0.3},
            },
        },
        "brawler": {
            "label": "Brawler",
            "description": "Bars, back lots, anywhere fists settle it.",
            "modifiers": {
                "weights": {"skills": 0.15},
                "skill_biases": {"brawl": 0.35, "athletics": 0.2},
                "discipline_biases": {"potence": 0.2},
            },
        },
        "legbreaker": {
            "label": "Legbreaker",
            "description": "The warning leaves a limp.",
            "modifiers": {
                "skill_biases": {"intimidation": 0.3, "brawl": 0.2},
                "discipline_biases": {"potence": 0.15},
            },
        },
        "collector": {
            "label": "Collector",
            "description": "Debts come back with interest and bruises.",
            "modifiers": {
                "weights": {"backgrounds": 0.1},
                "skill_biases": {"streetwise": 0.25, "intimidation": 0.2},
                "discipline_biases": {"presence": 0.2},
            },
        },
    },
    "predator": {
        "stalker": {
            "label": "Stalker",
            "description": "Close behind, just out of sight.",
            "modifiers": {
                "skill_biases": {"stealth": 0.35, "awareness": 0.2},
                "discipline_biases": {"obfuscate": 0.15},
            },
        },
        "tracker": {
            "label": "Tracker",
            "description": "You read habit, weather, and ground.",
            "modifiers": {
                "skill_biases": {"survival": 0.35, "awareness": 0.25},
                "discipline_biases": {"auspex": 0.15},
            },
        },
        "feral": {
            "label": "Feral",
            "description": "Court manners peel off fast.",
            "modifiers": {
                "weights": {"physical_attrs": 0.15},
                "skill_biases": {"animal_ken": 0.3, "brawl": 0.2},
                "discipline_biases": {"protean": 0.25, "animalism": 0.2},
            },
        },
        "scourge": {
            "label": "Scourge",
            "description": "Sent to end the problem, not chase it.",
            "modifiers": {
                "weights": {"in_clan_disciplines": 0.1},
                "skill_biases": {"firearms": 0.25, "intimidation": 0.2},
                "discipline_biases": {"potence": 0.2, "celerity": 0.15},
            },
        },
    },
    "criminal": {
        "thief": {
            "label": "Thief",
            "description": "In, out, no receipt.",
            "modifiers": {
                "skill_biases": {"larceny": 0.35, "stealth": 0.2},
                "discipline_biases": {"celerity": 0.15},
            },
        },
        "street_rat": {
            "label": "Street Rat",
            "description": "You learned the city by surviving it.",
            "modifiers": {
                "skill_biases": {"streetwise": 0.35, "survival": 0.2, "awareness": 0.15},
            },
        },
        "hustler": {
            "label": "Hustler",
            "description": "Every handshake hides an angle.",
            "modifiers": {
                "weights": {"backgrounds": 0.1},
                "skill_biases": {"subterfuge": 0.3, "streetwise": 0.2},
            },
        },
        "fence": {
            "label": "Fence",
            "description": "Hot goods find quiet buyers through you.",
            "modifiers": {
                "weights": {"backgrounds": 0.15},
                "skill_biases": {"larceny": 0.2, "finance": 0.15},
                "discipline_biases": {"obfuscate": 0.15},
            },
        },
    },
}

# Remaining archetypes — copy refresh only
OTHER_COPY: dict[str, str] = {
    "shadow": (
        "You slip through places that keep guest lists for a reason. Listen, take, "
        "leave before anyone agrees on what they saw."
    ),
    "scholar": (
        "Old books, bad translations, and the one footnote that saves someone's unlife. "
        "You'd rather read the room after you've read the file."
    ),
    "manipulator": (
        "The prince signs the order. You decide who whispers in his ear first. "
        "Rumors, pressure, and debts that never show on paper."
    ),
    "duelist": (
        "You train for violence the way other Kindred train for court. Win clean, "
        "win visibly, and let the story do the rest."
    ),
    "occultist": (
        "Blood, circles, and texts that were never meant for your clan. You treat "
        "sorcery like work, not a hobby."
    ),
    "investigator": (
        "Someone lied. The scene still says so. You keep asking until the timeline "
        "finally holds together."
    ),
    "artist": (
        "The city watches you, and you know how to use that. Patrons, premieres, "
        "and being impossible to ignore."
    ),
    "alchemist": (
        "Thin blood means improvising. You brew what passes for miracles in a bottle "
        "and hope the batch holds."
    ),
}


def _write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _write_subs(arch_id: str, subs: dict[str, dict]) -> None:
    sub_dir = ARCH / arch_id
    sub_dir.mkdir(exist_ok=True)
    for old in sub_dir.glob("*.json"):
        old.unlink()
    for sub_id, doc in subs.items():
        doc = {"id": sub_id, **doc}
        _write_json(sub_dir / f"{sub_id}.json", doc)


def main() -> None:
    for arch_id, base in MERGED_BASES.items():
        _write_json(ARCH / f"{arch_id}.json", base)
        _write_subs(arch_id, SUB_COPY[arch_id])
        print(f"Merged {arch_id}")

    for arch_id in REMOVED:
        path = ARCH / f"{arch_id}.json"
        if path.exists():
            path.unlink()
        sub_dir = ARCH / arch_id
        if sub_dir.is_dir():
            shutil.rmtree(sub_dir)
        print(f"Removed {arch_id}")

    for arch_id, description in OTHER_COPY.items():
        path = ARCH / f"{arch_id}.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data["description"] = description
        _write_json(path, data)

    print("Done.")


if __name__ == "__main__":
    main()
