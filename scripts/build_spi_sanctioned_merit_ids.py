#!/usr/bin/env python3
"""Build sanctioned SPI merit id allowlist from Rules Addendum + sheet extract.

Sheet extract supplies structured rows; Rules Addendum is the legal allowlist.
Affinity rows on the sheet are kept in full (MES affinity tabs). General rows
are kept only when they match an Addendum-sanctioned name (with typo aliases).

Requires (gitignored) reference files:
  reference/spi/rules_addendum.txt
  reference/spi/extracted/merits.json

Writes:
  wod_chargen/games/spi/data/sanctioned_merit_ids.json
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ADDENDUM = ROOT / "reference" / "spi" / "rules_addendum.txt"
SHEET = ROOT / "reference" / "spi" / "extracted" / "merits.json"
OUT = ROOT / "wod_chargen" / "games" / "spi" / "data" / "sanctioned_merit_ids.json"

BOOKISH = frozenset(
    {
        "chronicles of darkness core rulebook",
        "hurt locker",
        "hunter the vigil second edition core rulebook",
        "geist the sin eaters second edition core rulebook",
        "changeling the lost second edition core rulebook",
        "mage the awakening second edition core rulebook",
        "werewolf the forsaken second edition core rulebook",
        "vampire the requiem second edition core rulebook",
        "custom general merits",
        "sanctioned as written",
        "geist the sin",
        "affinity power index",
    }
)

# Explicit sheet id keeps when name matching is ambiguous or Addendum spelling differs.
FORCE_KEEP_GENERAL = frozenset(
    {
        "defensive_combat_brawl",
        "defensive_combat_weaponry",
        "sleight_of_hand",  # Addendum: "Slight of Hand"
        "compartimentalization",  # Addendum: Compartmentalization
        "division_liason",  # Addendum: Division Liaison
        "s_ance_devotee",  # Séance Devotee
        "cenonte",  # Addendum spelling
        "goblin_contract",
        "token",
        "fetish",
        "talon",
        "etiquette",
        "enchanting_performance",
    }
)

# Sheet rows that must never enter the packaged catalog.
FORCE_DROP_GENERAL = frozenset(
    {
        # Unsanctioned fighting styles (Addendum: only listed styles are in play)
        "armed_defense",
        "avoidance",
        "berserker",
        "bowmanship",
        "boxing",
        "chain_weapons",
        "cheap_shot",
        "close_quarters_combat",
        "combat_archery",
        "falconry",
        "firefight",
        "grappling",
        "heavy_weaponry",
        "improvised_weaponry",
        "iron_skin",
        "k_9",
        "kindred_dueling",
        "kino_mutai",
        "light_weapons",
        "marksmanship",
        "martial_arts",
        "mounted_combat",
        "police_tactics",
        "powered_projectile",
        "psychokinetic_warrior",
        "shiv",
        "spear_and_bayonet",
        "staff_fighting",  # must not match Social "Staff"
        "street_fighting",
        "strength_performance",
        "thrown_weapons",
        "two_weapon_fighting",
        "unarmed_defense",
        "weapon_and_shield",
        # Explicitly unavailable / not in General allowlist
        "artifact",
        "mystery_cult_initiation",
        # CoD supernatural block — not in General sanctioned list; Affinity copies kept
        "aura_reading",
        "automatic_writing",
        "biokinesis",
        "clairvoyance",
        "laying_on_hands",
        "medium",
        "numbing_touch",
        "omen_sensitivity",
        "psychokinesis",
        "psychometry",
        "telekinesis",
        "telepathy",
        "thief_of_fate",
        "unseen_sense",
    }
)


def norm(s: str) -> str:
    s = s.lower().replace("’", "'").replace("–", "-").replace("—", "-")
    s = s.replace("é", "e").replace("è", "e")
    s = re.sub(r"\([^)]*\)", " ", s)
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def _add_name(bucket: set[str], raw: str) -> None:
    n = norm(raw)
    if not n or len(n) < 2 or len(n) > 60 or n in BOOKISH:
        return
    bucket.add(n)


def parse_general_names(chunk: str) -> set[str]:
    names: set[str] = set()
    for m in re.finditer(r"Sanctioned as written:\s*(.+?)(?:\n\s+\d+\.|\Z)", chunk, re.S):
        blob = re.sub(r"\([^)]*\)", ",", m.group(1))
        for part in re.split(r",", blob):
            if part.strip():
                _add_name(names, part)
    for m in re.finditer(r"^\s+\d+\.\s+(.+?)(?:\s+\(|\s+-\s)", chunk, re.M):
        _add_name(names, m.group(1))
    for pat in (
        r"following Ceremonies as general merits[^:]*:\s*(.+)",
        r"Goblin Contracts are available[^:]*:\s*(.+)",
        r"following tokens may be bought[^:]*:\s*(.+)",
        r"following Rites as general merits[^:]*:\s*(.+)",
        r"Talons and Fetishes are available[^:]*:\s*(.+)",
    ):
        m = re.search(pat, chunk)
        if m:
            for part in re.split(r",\s*", m.group(1)):
                _add_name(names, part.strip().rstrip("."))
    for x in (
        "Limerick",
        "Poem",
        "Sonnet",
        "Bless His Heart",
        "Losing Your Religion",
        "In High Cotton",
        "Half Cocked",
        "Grace Under Fire",
        "Extra Touchstone",
        "Locus",
        "Goetic Companion",
        "Spirit Companion",
        "Ghostly Companion",
        "Defensive Combat",
        "Compartmentalization",
        "Division Liaison",
        "Slight of Hand",
        "Sleight of Hand",
        "Séance Devotee",
        "Seance Devotee",
        "Cenonte",
        "The Bold",
        "Animal Companion",
        "Creature Clothing",
        "Spook",
        "Kindness Begets Kindness",
        "Scrying",
        "Vibrant Soul",
        "Etiquette",
        "Goblin Contract",
        "Token",
        "Fetish",
        "Talon",
        "Enchanting Performance",
        "Parkour",
        "Professional Training",
        "Fast Talking",
    ):
        _add_name(names, x)
    # Typo / sheet-label aliases
    names.update(
        {
            "sleight of hand",
            "compartimentalization",
            "division liason",
            "s ance devotee",
            "defensive combat brawl",
            "defensive combat weaponry",
        }
    )
    return names


def exact_match(names: set[str], entry: dict) -> bool:
    candidates = {norm(entry["label"]), norm(entry["id"].replace("_", " "))}
    if "devotee" in entry["id"] and "seance devotee" in names:
        return True
    return bool(candidates & names)


def main() -> int:
    if not ADDENDUM.is_file():
        print(f"ERROR: missing {ADDENDUM}", file=sys.stderr)
        return 1
    if not SHEET.is_file():
        print(f"ERROR: missing {SHEET}", file=sys.stderr)
        return 1

    text = ADDENDUM.read_text(encoding="utf-8", errors="replace")
    g_start = text.find("2. General Merits\n         1. Chronicles of Darkness")
    a_start = text.find("3. Affinity Powers / Merits", g_start)
    if g_start < 0 or a_start < 0:
        print("ERROR: could not locate General Merits / Affinity sections", file=sys.stderr)
        return 1
    general_names = parse_general_names(text[g_start:a_start])

    sheet = json.loads(SHEET.read_text(encoding="utf-8"))["merits"]
    keep_entries: list[dict[str, str]] = []
    general_ids: list[str] = []
    affinity_ids: list[str] = []
    dropped: list[dict] = []

    for entry in sheet:
        mid = entry["id"]
        cat = entry.get("category") or ""
        if cat == "affinity":
            # Sheet affinity tabs are the MES-maintained Affinity Powers catalog.
            keep_entries.append({"id": mid, "category": "affinity"})
            affinity_ids.append(mid)
            continue
        if mid in FORCE_DROP_GENERAL:
            dropped.append({"id": mid, "label": entry.get("label"), "reason": "force_drop"})
            continue
        if mid in FORCE_KEEP_GENERAL or exact_match(general_names, entry):
            keep_entries.append({"id": mid, "category": "general"})
            general_ids.append(mid)
            continue
        dropped.append({"id": mid, "label": entry.get("label"), "reason": "not_in_addendum"})

    payload = {
        "notes": (
            "SPI merits allowed in chargen. Built from character_sheet.xlsx extract "
            "filtered by Rules Addendum. Affinity: all sheet affinity rows. "
            "General: Addendum allowlist (+ typo aliases). Matching is (id, category) "
            "because some powers exist as both general (dropped) and affinity (kept)."
        ),
        "source": {
            "addendum": "reference/spi/rules_addendum.txt",
            "sheet_extract": "reference/spi/extracted/merits.json",
        },
        "keep_all_affinity": True,
        "general_ids": general_ids,
        "affinity_ids": affinity_ids,
        "entries": keep_entries,
        "dropped_general": dropped,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        f"wrote {OUT.relative_to(ROOT)}: keep {len(keep_entries)} entries "
        f"({len(general_ids)} general + {len(affinity_ids)} affinity), "
        f"drop {len(dropped)} general rows"
    )
    for row in dropped:
        print(f"  DROP {row['id']}: {row['label']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
