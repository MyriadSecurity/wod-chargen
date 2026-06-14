#!/usr/bin/env python3
"""Split combined archetype JSON into base file + per-sub modifier files."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ARCH_DIR = ROOT / "wod_chargen" / "games" / "lotn_v5" / "data" / "archetypes"

# Optional richer modifiers keyed as "archetype/sub"
ENHANCED_MODIFIERS: dict[str, dict] = {
    "face/silver_tongue": {
        "weights": {"skills": 0.3},
        "skill_biases": {"persuasion": 0.5, "subterfuge": 0.4},
        "discipline_biases": {"presence": 0.3},
    },
    "face/socialite": {
        "weights": {"social_attrs": 0.2, "backgrounds": 0.2},
        "skill_biases": {"etiquette": 0.4, "persuasion": 0.2},
        "discipline_biases": {"presence": 0.2},
    },
    "face/instigator": {
        "weights": {"social_attrs": 0.15},
        "skill_biases": {"intimidation": 0.4, "subterfuge": 0.2},
        "discipline_biases": {"presence": 0.15},
    },
    "face/preacher": {
        "weights": {"merits": 0.1, "backgrounds": 0.1},
        "skill_biases": {"persuasion": 0.3, "insight": 0.2},
        "discipline_biases": {"presence": 0.4, "dominate": 0.1},
    },
    "bruiser/tank": {
        "weights": {"physical_attrs": 0.2, "in_clan_disciplines": 0.1},
        "attribute_biases": {"stamina": 0.3},
        "discipline_biases": {"fortitude": 0.3},
    },
    "bruiser/brawler": {
        "weights": {"skills": 0.2},
        "skill_biases": {"brawl": 0.4, "athletics": 0.2},
        "discipline_biases": {"potence": 0.2},
    },
    "bruiser/wrestler": {
        "weights": {"physical_attrs": 0.15},
        "skill_biases": {"brawl": 0.3, "athletics": 0.3},
        "attribute_biases": {"strength": 0.2},
    },
    "bruiser/juggernaut": {
        "weights": {"physical_attrs": 0.25, "merits": 0.1},
        "attribute_biases": {"stamina": 0.4, "strength": 0.2},
        "discipline_biases": {"potence": 0.25, "fortitude": 0.2},
    },
    "shadow/spy": {
        "weights": {"skills": 0.2},
        "skill_biases": {"stealth": 0.4, "subterfuge": 0.3},
        "discipline_biases": {"obfuscate": 0.3},
    },
    "shadow/infiltrator": {
        "weights": {"mental_attrs": 0.1, "skills": 0.15},
        "skill_biases": {"larceny": 0.3, "stealth": 0.3},
        "discipline_biases": {"celerity": 0.2},
    },
    "shadow/ghost": {
        "weights": {"in_clan_disciplines": 0.15},
        "skill_biases": {"stealth": 0.5},
        "discipline_biases": {"obfuscate": 0.4},
    },
    "shadow/saboteur": {
        "weights": {"skills": 0.2, "mental_attrs": 0.1},
        "skill_biases": {"craft": 0.3, "larceny": 0.2, "technology": 0.2},
    },
    "alchemist/distiller": {
        "weights": {"thin_blood_formulas": 0.3},
        "skill_biases": {"craft": 0.3, "science": 0.2},
    },
    "alchemist/chemist": {
        "weights": {"skills": 0.2, "thin_blood_formulas": 0.2},
        "skill_biases": {"science": 0.4, "medicine": 0.2},
    },
    "alchemist/blood_brewer": {
        "weights": {"thin_blood_formulas": 0.4, "in_clan_disciplines": 0.1},
        "discipline_biases": {"thin_blood_alchemy": 0.3},
    },
    "alchemist/mixer": {
        "weights": {"skills": 0.15, "merits": 0.1},
        "skill_biases": {"craft": 0.4, "occult": 0.2},
    },
}


def _legacy_to_modifiers(sub: dict) -> dict:
    return {
        "weights": sub.get("weight_deltas", {}),
        "attribute_biases": sub.get("attribute_bias_deltas", {}),
        "skill_biases": sub.get("skill_bias_deltas", {}),
        "discipline_biases": sub.get("discipline_bias_deltas", {}),
    }


def _write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def migrate_file(path: Path) -> None:
    raw = json.loads(path.read_text(encoding="utf-8"))
    arch_id = raw["id"]
    subs = raw.pop("sub_archetypes", [])
    _write_json(path, raw)

    sub_dir = ARCH_DIR / arch_id
    sub_dir.mkdir(exist_ok=True)
    for sub in subs:
        key = f"{arch_id}/{sub['id']}"
        modifiers = ENHANCED_MODIFIERS.get(key) or _legacy_to_modifiers(sub)
        doc = {
            "id": sub["id"],
            "label": sub["label"],
            "modifiers": modifiers,
        }
        if sub.get("description"):
            doc["description"] = sub["description"]
        _write_json(sub_dir / f"{sub['id']}.json", doc)


def main() -> None:
    for path in sorted(ARCH_DIR.glob("*.json")):
        if path.name.startswith("_"):
            continue
        migrate_file(path)
        print(f"Split {path.name}")


if __name__ == "__main__":
    main()
