#!/usr/bin/env python3
"""Revise sub-archetype roster: clear names, distinct themes, no filler fours."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ARCH = ROOT / "wod_chargen" / "games" / "lotn_v5" / "data" / "archetypes"

# id, label, description, modifiers — only subs listed are kept
SUBTYPES: dict[str, list[dict]] = {
    "diplomat": [
        {
            "id": "silver_tongue",
            "label": "Silver Tongue",
            "description": "Public charm. You talk a room into calm or chaos.",
            "modifiers": {
                "weights": {"skills": 0.2},
                "skill_biases": {"persuasion": 0.5, "subterfuge": 0.2},
                "discipline_biases": {"presence": 0.3},
            },
        },
        {
            "id": "socialite",
            "label": "Socialite",
            "description": "Guest lists, introductions, and who not to sit beside.",
            "modifiers": {
                "weights": {"social_attrs": 0.2, "backgrounds": 0.15},
                "skill_biases": {"etiquette": 0.4, "insight": 0.2},
            },
        },
        {
            "id": "zealot",
            "label": "Zealot",
            "description": "Faith, dogma, and sermons that leave no room for doubt.",
            "modifiers": {
                "weights": {"social_attrs": 0.15, "merits": 0.1},
                "skill_biases": {"persuasion": 0.25, "occult": 0.3, "insight": 0.2, "subterfuge": -0.25},
                "discipline_biases": {"presence": 0.2},
            },
        },
        {
            "id": "negotiator",
            "label": "Negotiator",
            "description": "Truces, treaties, and threats everyone can sign.",
            "modifiers": {
                "weights": {"backgrounds": 0.1},
                "skill_biases": {"politics": 0.4, "persuasion": 0.25},
                "discipline_biases": {"dominate": 0.15},
            },
        },
        {
            "id": "harpy",
            "label": "Harpy",
            "description": "Status games, scandal, and public humiliation as sport.",
            "modifiers": {
                "weights": {"social_attrs": 0.15, "merits": 0.1},
                "skill_biases": {"politics": 0.3, "subterfuge": 0.3, "etiquette": 0.15, "insight": 0.15},
                "discipline_biases": {"presence": 0.25},
            },
        },
        {
            "id": "courtier",
            "label": "Courtier",
            "description": "Who stands where, and who owes whom before the vote.",
            "modifiers": {
                "weights": {"backgrounds": 0.15},
                "skill_biases": {"politics": 0.45, "etiquette": 0.25, "leadership": 0.15},
                "discipline_biases": {"presence": 0.15},
            },
        },
        {
            "id": "agitator",
            "label": "Agitator",
            "description": "Crowds, slogans, and making the street impossible to ignore.",
            "modifiers": {
                "weights": {"social_attrs": 0.1},
                "skill_biases": {"streetwise": 0.4, "persuasion": 0.2, "politics": 0.15, "etiquette": -0.35},
                "discipline_biases": {"presence": 0.2},
            },
        },
    ],
    "enforcer": [
        {
            "id": "tank",
            "label": "Tank",
            "description": "Stand in the fire and keep standing.",
            "modifiers": {
                "weights": {"physical_attrs": 0.2, "in_clan_disciplines": 0.1},
                "attribute_biases": {"stamina": 0.35},
                "discipline_biases": {"fortitude": 0.35},
            },
        },
        {
            "id": "brawler",
            "label": "Brawler",
            "description": "Fists, bottles, and whatever's loose on the floor.",
            "modifiers": {
                "weights": {"skills": 0.15},
                "skill_biases": {"brawl": 0.4, "athletics": 0.2},
                "discipline_biases": {"potence": 0.25},
            },
        },
        {
            "id": "collector",
            "label": "Debt Collector",
            "description": "Money owed comes back with interest and bruises.",
            "modifiers": {
                "weights": {"backgrounds": 0.1},
                "skill_biases": {"intimidation": 0.4, "streetwise": 0.3, "finance": 0.15},
                "discipline_biases": {"presence": 0.2},
            },
        },
        {
            "id": "guardian",
            "label": "Guardian",
            "description": "Stand between the threat and whoever you're sworn to protect.",
            "modifiers": {
                "weights": {"physical_attrs": 0.15},
                "attribute_biases": {"stamina": 0.25, "strength": 0.15},
                "skill_biases": {"awareness": 0.5, "athletics": 0.2, "intimidation": 0.1, "firearms": -0.2, "brawl": -0.25},
                "discipline_biases": {"fortitude": 0.25},
            },
        },
        {
            "id": "scourge",
            "label": "Scourge",
            "description": "Prince's errand. The problem doesn't wake up.",
            "modifiers": {
                "weights": {"in_clan_disciplines": 0.1},
                "skill_biases": {"firearms": 0.4, "intimidation": 0.1, "stealth": 0.15, "brawl": -0.5},
                "discipline_biases": {"potence": 0.25, "celerity": 0.15},
            },
        },
    ],
    "predator": [
        {
            "id": "stalker",
            "label": "Stalker",
            "description": "Follow a target for nights without being clocked.",
            "modifiers": {
                "skill_biases": {"stealth": 0.4, "awareness": 0.25},
                "discipline_biases": {"obfuscate": 0.15},
            },
        },
        {
            "id": "feral",
            "label": "Feral",
            "description": "The Beast shows. Manners don't.",
            "modifiers": {
                "weights": {"physical_attrs": 0.15},
                "skill_biases": {"animal_ken": 0.35, "brawl": 0.25},
                "discipline_biases": {"protean": 0.3, "animalism": 0.25},
            },
        },
    ],
    "criminal": [
        {
            "id": "thief",
            "label": "Thief",
            "description": "Take it and vanish.",
            "modifiers": {
                "skill_biases": {"larceny": 0.45, "stealth": 0.35, "subterfuge": -0.2},
                "discipline_biases": {"celerity": 0.15},
            },
        },
        {
            "id": "hustler",
            "label": "Hustler",
            "description": "Every handshake hides an angle.",
            "modifiers": {
                "weights": {"backgrounds": 0.1},
                "skill_biases": {"subterfuge": 0.4, "persuasion": 0.2, "streetwise": 0.2, "stealth": -0.2},
            },
        },
        {
            "id": "fence",
            "label": "Fence",
            "description": "Hot goods find quiet buyers through you.",
            "modifiers": {
                "weights": {"backgrounds": 0.15},
                "skill_biases": {"finance": 0.35, "larceny": 0.15, "streetwise": -0.15, "subterfuge": 0.1},
                "discipline_biases": {"obfuscate": 0.15},
            },
        },
        {
            "id": "fixer",
            "label": "Fixer",
            "description": "Wrong tool, wrong contact, wrong hour — you know who to call.",
            "modifiers": {
                "weights": {"backgrounds": 0.15, "skills": 0.1},
                "skill_biases": {"streetwise": 0.4, "subterfuge": 0.2, "finance": 0.2, "larceny": -0.35},
            },
        },
    ],
    "shadow": [
        {
            "id": "spy",
            "label": "Spy",
            "description": "Watch, listen, report back.",
            "modifiers": {
                "weights": {"skills": 0.15},
                "skill_biases": {"stealth": 0.3, "subterfuge": 0.25, "investigation": 0.15},
                "discipline_biases": {"auspex": 0.15},
            },
        },
        {
            "id": "infiltrator",
            "label": "Infiltrator",
            "description": "Inside the place you're not meant to reach.",
            "modifiers": {
                "skill_biases": {"larceny": 0.3, "stealth": 0.3},
                "discipline_biases": {"obfuscate": 0.25, "celerity": 0.1},
            },
        },
        {
            "id": "saboteur",
            "label": "Saboteur",
            "description": "Break the lock, the camera, or the whole plan.",
            "modifiers": {
                "weights": {"mental_attrs": 0.1},
                "skill_biases": {"craft": 0.3, "technology": 0.25, "larceny": 0.15},
            },
        },
    ],
    "scholar": [
        {
            "id": "loremaster",
            "label": "Loremaster",
            "description": "Kindred history, occult theory, and what the elders got wrong.",
            "modifiers": {
                "skill_biases": {"occult": 0.45, "academics": 0.3},
                "discipline_biases": {"auspex": 0.15},
            },
        },
        {
            "id": "scientist",
            "label": "Scientist",
            "description": "Lab work, medicine, and answers that don't need a ritual circle.",
            "modifiers": {
                "skill_biases": {"science": 0.5, "medicine": 0.35, "academics": 0.15},
            },
        },
        {
            "id": "archivist",
            "label": "Archivist",
            "description": "Records, dates, and what someone tried to shred.",
            "modifiers": {
                "weights": {"backgrounds": 0.1},
                "skill_biases": {"academics": 0.35, "investigation": 0.25},
            },
        },
        {
            "id": "medic",
            "label": "Medic",
            "description": "Stitches, transfusions, and keeping mortals alive long enough to matter.",
            "modifiers": {
                "skill_biases": {
                    "medicine": 0.55,
                    "science": 0.3,
                    "insight": 0.15,
                    "academics": -0.45,
                    "occult": -0.3,
                },
            },
        },
    ],
    "manipulator": [
        {
            "id": "puppetmaster",
            "label": "Puppetmaster",
            "description": "People move and swear it was their idea.",
            "modifiers": {
                "weights": {"social_attrs": 0.15},
                "skill_biases": {"subterfuge": 0.35, "insight": 0.35, "politics": 0.2},
                "discipline_biases": {"dominate": 0.25},
            },
        },
        {
            "id": "gaslighter",
            "label": "Gaslighter",
            "description": "They doubt what they saw because you said so.",
            "modifiers": {
                "skill_biases": {"persuasion": 0.4, "subterfuge": 0.25, "insight": 0.1},
                "discipline_biases": {"dominate": 0.2},
            },
        },
        {
            "id": "siren",
            "label": "Siren",
            "description": "Desire on a leash. They come closer and call it their choice.",
            "modifiers": {
                "weights": {"social_attrs": 0.15},
                "skill_biases": {"persuasion": 0.4, "insight": 0.2, "subterfuge": 0.1, "politics": -0.2},
                "discipline_biases": {"presence": 0.25, "dominate": 0.1},
            },
        },
    ],
    "duelist": [
        {
            "id": "fencer",
            "label": "Fencer",
            "description": "Blades, footwork, and winning the elegant way.",
            "modifiers": {
                "skill_biases": {"melee": 0.45, "athletics": 0.2},
                "discipline_biases": {"celerity": 0.25},
            },
        },
        {
            "id": "marksman",
            "label": "Marksman",
            "description": "Distance, sight lines, one clean shot.",
            "modifiers": {
                "skill_biases": {"firearms": 0.45, "awareness": 0.2},
                "discipline_biases": {"celerity": 0.15},
            },
        },
        {
            "id": "skirmisher",
            "label": "Skirmisher",
            "description": "Hit, move, hit again. Never a static target.",
            "modifiers": {
                "attribute_biases": {"dexterity": 0.3},
                "skill_biases": {"athletics": 0.35, "melee": 0.2, "brawl": 0.15},
                "discipline_biases": {"celerity": 0.3},
            },
        },
    ],
    "occultist": [
        {
            "id": "thaumaturge",
            "label": "Thaumaturge",
            "description": "Formal blood magic. Steps you do not skip.",
            "modifiers": {
                "weights": {"in_clan_disciplines": 0.2, "merits": 0.1},
                "skill_biases": {"occult": 0.35},
                "discipline_biases": {"blood_sorcery": 0.4, "auspex": 0.15},
            },
        },
        {
            "id": "ritualist",
            "label": "Ritualist",
            "description": "Circles, components, and the long way that works.",
            "modifiers": {
                "weights": {"merits": 0.15},
                "skill_biases": {"occult": 0.3, "academics": 0.25},
                "discipline_biases": {"blood_sorcery": -0.15},
            },
        },
        {
            "id": "necromancer",
            "label": "Necromancer",
            "description": "Dead things answer. Living things regret asking.",
            "modifiers": {
                "skill_biases": {"occult": 0.4, "medicine": 0.15},
                "discipline_biases": {"blood_sorcery": 0.25},
            },
        },
    ],
    "investigator": [
        {
            "id": "detective",
            "label": "Detective",
            "description": "Interviews, timelines, and who lied first.",
            "modifiers": {
                "skill_biases": {"investigation": 0.45, "insight": 0.25},
                "discipline_biases": {"auspex": 0.15},
            },
        },
        {
            "id": "forensic",
            "label": "Forensic",
            "description": "Blood spatter, fibers, what the scene still says.",
            "modifiers": {
                "skill_biases": {
                    "science": 0.45,
                    "investigation": 0.25,
                    "medicine": 0.2,
                    "intimidation": -0.2,
                },
            },
        },
        {
            "id": "interrogator",
            "label": "Interrogator",
            "description": "One room. One chair. Answers.",
            "modifiers": {
                "skill_biases": {"intimidation": 0.45, "insight": 0.35, "investigation": 0.1},
                "discipline_biases": {"dominate": 0.2},
            },
        },
    ],
    "artist": [
        {
            "id": "virtuoso",
            "label": "Virtuoso",
            "description": "Canvas, verse, clay — you make the work they argue about.",
            "modifiers": {
                "weights": {"mental_attrs": 0.15, "social_attrs": -0.15},
                "skill_biases": {"craft": 0.5, "performance": -0.5, "academics": 0.2},
                "discipline_biases": {"auspex": 0.15, "presence": -0.15},
            },
        },
        {
            "id": "performer",
            "label": "Performer",
            "description": "Stage, crowd, and the silence after the last note.",
            "modifiers": {
                "skill_biases": {"performance": 0.45, "persuasion": 0.2, "craft": -0.2},
                "discipline_biases": {"presence": 0.25},
            },
        },
        {
            "id": "patron",
            "label": "Patron",
            "description": "Wealthy admirers and what they pay for access.",
            "modifiers": {
                "weights": {"backgrounds": 0.2, "social_attrs": 0.1},
                "skill_biases": {"etiquette": 0.35, "finance": 0.25, "performance": -0.35, "craft": -0.2},
            },
        },
        {
            "id": "director",
            "label": "Director",
            "description": "Owns the vision. Names the scene. Blocks everyone else.",
            "modifiers": {
                "weights": {"social_attrs": 0.15},
                "skill_biases": {"persuasion": 0.3, "insight": 0.3, "performance": 0.1},
            },
        },
    ],
    "alchemist": [
        {
            "id": "chemist",
            "label": "Chemist",
            "description": "Lab discipline. Measured doses. No guessing.",
            "modifiers": {
                "skill_biases": {"science": 0.45, "medicine": 0.25},
                "weights": {"thin_blood_formulas": 0.15},
            },
        },
        {
            "id": "distiller",
            "label": "Distiller",
            "description": "Batches, bottles, and what not to drink yet.",
            "modifiers": {
                "weights": {"thin_blood_formulas": 0.35},
                "skill_biases": {"craft": 0.3, "science": 0.2},
            },
        },
        {
            "id": "blood_brewer",
            "label": "Blood Brewer",
            "description": "Vitae in the mix. Gloves on. Prayers optional.",
            "modifiers": {
                "weights": {"thin_blood_formulas": 0.25, "in_clan_disciplines": 0.1},
                "skill_biases": {"occult": 0.3, "medicine": 0.2, "science": 0.1},
                "discipline_biases": {"thin_blood_alchemy": 0.35},
            },
        },
    ],
}


def _write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    total = 0
    manifest: dict[str, list] = {"primaries": [], "subtypes": {}}
    for arch_id, subs in SUBTYPES.items():
        manifest["primaries"].append(arch_id)
        manifest["subtypes"][arch_id] = [s["id"] for s in subs]
        sub_dir = ARCH / arch_id
        if not sub_dir.is_dir():
            raise SystemExit(f"Missing archetype dir: {sub_dir}")
        keep = {s["id"] for s in subs}
        for old in sub_dir.glob("*.json"):
            if old.stem not in keep:
                old.unlink()
                print(f"Removed {old.relative_to(ARCH)}")
        for spec in subs:
            doc = {
                "id": spec["id"],
                "label": spec["label"],
                "description": spec["description"],
                "modifiers": spec["modifiers"],
            }
            _write_json(sub_dir / f"{spec['id']}.json", doc)
            total += 1
        print(f"{arch_id}: {len(subs)} subtypes")
    _write_json(ARCH / "_manifest.json", manifest)
    print(f"Wrote {total} sub-archetype files across {len(SUBTYPES)} primaries")


if __name__ == "__main__":
    main()
