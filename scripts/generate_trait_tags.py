#!/usr/bin/env python3
"""Generate power tags in trait_tags.json from discipline_powers catalog."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "wod_chargen/games/lotn_v5/data"
POWERS_PATH = DATA / "discipline_powers.json"
TAGS_PATH = DATA / "trait_tags.json"

DISC_TAGS: dict[str, list[str]] = {
    "animalism": ["predation", "animal"],
    "auspex": ["mental", "information", "perception"],
    "blood_sorcery": ["occult", "ritual", "blood_sorcery"],
    "celerity": ["combat", "mobility"],
    "dominate": ["social", "control", "dominate"],
    "fortitude": ["endurance", "resilience"],
    "obfuscate": ["stealth", "deception"],
    "oblivion": ["occult", "necromancy", "oblivion"],
    "potence": ["combat", "physical"],
    "presence": ["social", "influence", "presence"],
    "protean": ["predation", "physical", "shapeshift"],
    "thin_blood_alchemy": ["alchemy", "thin_blood"],
}

POWER_EXTRA: dict[str, list[str]] = {
    "mesmerize": ["social", "control"],
    "command": ["social", "control"],
    "cloud_memory": ["deception", "social"],
    "compel": ["social", "control"],
    "dominate_mastery": ["social", "control"],
    "a_taste_for_blood": ["occult", "ritual", "blood_sorcery"],
    "corrosive_vitae": ["occult", "combat"],
    "blood_of_potency": ["occult", "ritual"],
    "warding_circle": ["occult", "ritual", "defense"],
    "commune_with_the_dead": ["occult", "necromancy", "information"],
    "shadow_spectre": ["occult", "necromancy", "combat"],
    "arms_of_ahriman": ["occult", "necromancy", "combat"],
    "fleetness": ["combat", "mobility"],
    "rapier": ["combat", "mobility"],
    "precision": ["combat", "mobility"],
    "eyes_of_the_beast": ["predation", "perception"],
    "feral_weapons": ["predation", "combat"],
    "shapechange": ["predation", "shapeshift"],
    "vanish": ["stealth", "deception"],
    "cloak_of_shadows": ["stealth", "deception"],
    "silent_hunter": ["stealth", "predation"],
    "sense_the_unseen": ["mental", "perception", "information"],
    "smell_fear": ["mental", "perception"],
    "forensic_awareness": ["mental", "investigation"],
    "unswayable_mind": ["mental", "resilience"],
    "awe": ["social", "influence"],
    "dread_gaze": ["social", "intimidation"],
    "entrancement": ["social", "influence"],
    "majestic_presence": ["social", "influence", "reputation"],
    "iron_grip": ["combat", "physical"],
    "lethal_body": ["combat", "physical"],
    "soaring_leap": ["combat", "mobility"],
    "resilience": ["endurance", "resilience"],
    "unswayable": ["endurance", "resilience"],
    "flesh_of_marble": ["endurance", "resilience"],
    "animal_succulence": ["predation", "animal"],
    "feral_whispers": ["predation", "animal"],
    "animalism_mastery": ["predation", "animal"],
    "contortions": ["alchemy", "thin_blood"],
    "hardened_scales": ["alchemy", "thin_blood", "defense"],
    "thin_blood_alchemy_mastery": ["alchemy", "thin_blood"],
}


def main() -> None:
    catalog = json.loads(POWERS_PATH.read_text())
    tags_data = json.loads(TAGS_PATH.read_text()) if TAGS_PATH.exists() else {"tags": {}}
    power_tags: dict[str, list[str]] = dict(tags_data.get("powers", {}))

    for disc in catalog["disciplines"]:
        disc_id = disc["id"]
        base = list(DISC_TAGS.get(disc_id, []))
        for power in disc.get("powers", []):
            pid = power["id"]
            if pid.startswith("counterfeit"):
                continue
            level = int(power.get("level", 99))
            if level > 5:
                continue
            merged = list(dict.fromkeys(base + POWER_EXTRA.get(pid, [])))
            if disc_id in ("blood_sorcery", "oblivion") and power.get("rules", {}).get("track") in (
                "ritual",
                "ceremony",
            ):
                merged.append("ritual")
            power_tags[pid] = merged

    tags_data["powers"] = dict(sorted(power_tags.items()))
    TAGS_PATH.write_text(json.dumps(tags_data, indent=2, ensure_ascii=False) + "\n")
    print(f"Wrote {len(power_tags)} power tags to {TAGS_PATH}")


if __name__ == "__main__":
    main()
