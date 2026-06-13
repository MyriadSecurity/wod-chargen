#!/usr/bin/env python3
"""Merge descriptions and rules into discipline_powers.json."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
CATALOG = ROOT / "wod_chargen" / "games" / "lotn_v5" / "data" / "discipline_powers.json"

sys.path.insert(0, str(ROOT / "scripts"))
from discipline_power_descriptions import DESCRIPTIONS  # noqa: E402
from discipline_power_rules import (  # noqa: E402
    AMALGAM_DISCIPLINE_SLUGS,
    RULES,
    TRACK_BY_DISCIPLINE,
)


def _build_label_index(catalog: dict[str, Any]) -> dict[str, str]:
    index: dict[str, str] = {}
    for disc in catalog.get("disciplines", []):
        for power in disc.get("powers", []):
            label = str(power["label"]).strip()
            index[label.lower()] = power["id"]
            index[power["id"]] = power["id"]
    return index


def _resolve_prerequisite(text: str, label_index: dict[str, str]) -> dict[str, Any] | None:
    if not text:
        return None
    raw = str(text).strip()
    if " or " in raw.lower():
        parts = re.split(r"\s+or\s+", raw, flags=re.IGNORECASE)
        ids = []
        for part in parts:
            pid = label_index.get(part.strip().lower())
            if pid:
                ids.append(pid)
        if ids:
            return {"requires_any_powers": ids}
        return None
    # typo fix
    if raw.lower() == "vicssitide":
        raw = "Vicissitude"
    pid = label_index.get(raw.lower())
    if pid:
        return {"requires_all_powers": [pid]}
    return None


def _rules_from_mes(power: dict[str, Any], disc_id: str, label_index: dict[str, str]) -> dict[str, Any]:
    rules: dict[str, Any] = {"track": TRACK_BY_DISCIPLINE.get(disc_id, "discipline")}
    amalgam = power.get("amalgam")
    if amalgam:
        slug = AMALGAM_DISCIPLINE_SLUGS.get(str(amalgam))
        if slug:
            rules["amalgam_discipline"] = slug
            level = power.get("amalgam_level")
            if level is not None:
                rules["amalgam_min_level"] = int(level)
    prereq = _resolve_prerequisite(power.get("prerequisite"), label_index)
    if prereq:
        rules.update(prereq)
    return rules


def enrich(catalog: dict[str, Any], *, force: bool = False) -> tuple[int, int, list[str]]:
    label_index = _build_label_index(catalog)
    filled_desc = 0
    filled_rules = 0
    missing: list[str] = []

    for disc in catalog.get("disciplines", []):
        disc_id = disc["id"]
        for power in disc.get("powers", []):
            pid = power["id"]
            if (not power.get("description") or force) and DESCRIPTIONS.get(pid):
                power["description"] = DESCRIPTIONS[pid]
                filled_desc += 1
            elif not power.get("description") and power.get("notes"):
                power["description"] = str(power["notes"])
                filled_desc += 1

            if power.get("rules") and not force:
                continue
            merged = _rules_from_mes(power, disc_id, label_index)
            override = RULES.get(pid, {})
            merged.update(override)
            power["rules"] = merged
            filled_rules += 1

            if power.get("prerequisite") and not merged.get("requires_all_powers") and not merged.get(
                "requires_any_powers"
            ):
                missing.append(f"{pid}: unmapped prereq {power['prerequisite']!r}")

    for rule_id in RULES:
        if rule_id not in label_index:
            missing.append(f"orphan rule: {rule_id}")

    return filled_desc, filled_rules, missing


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="Overwrite existing description/rules")
    args = parser.parse_args()

    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    desc_n, rules_n, missing = enrich(catalog, force=args.force)
    CATALOG.write_text(json.dumps(catalog, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Filled {desc_n} descriptions, {rules_n} rules entries -> {CATALOG}")
    if missing:
        print("Warnings:")
        for line in missing:
            print(f"  {line}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
