#!/usr/bin/env python3
"""Merge descriptions and rules into merits_flaws.json.

Preserves existing fields when re-running; fills gaps from pocket-book maps.

Usage:
    uv run python scripts/enrich_merits_flaws_descriptions.py [--force]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "wod_chargen" / "games" / "lotn_v5" / "data"
CATALOG = DATA / "merits_flaws.json"

sys.path.insert(0, str(ROOT / "scripts"))
from merit_flaw_rules import RULES  # noqa: E402
from merits_flaws_descriptions import DESCRIPTIONS  # noqa: E402


def enrich_rules(catalog: dict[str, Any], *, force: bool = False) -> tuple[int, list[str]]:
    filled = 0
    orphans: list[str] = []
    seen: set[str] = set()

    for kind in ("merits", "flaws"):
        for entry in catalog.get(kind, []):
            entry_id = entry["id"]
            seen.add(entry_id)
            rules = RULES.get(entry_id)
            if not rules:
                entry.pop("rules", None)
                continue
            if entry.get("rules") and not force:
                continue
            entry["rules"] = rules
            filled += 1

    for rule_id in RULES:
        if rule_id not in seen:
            orphans.append(rule_id)
    return filled, orphans


def enrich(catalog: dict[str, Any], *, force: bool = False) -> tuple[int, int, list[str]]:
    """Return (filled, skipped, missing_ids)."""
    filled = 0
    skipped = 0
    seen: set[str] = set()
    missing: list[str] = []

    for kind in ("merits", "flaws"):
        for entry in catalog.get(kind, []):
            entry_id = entry["id"]
            seen.add(entry_id)
            if entry.get("description") and not force:
                skipped += 1
                continue
            text = DESCRIPTIONS.get(entry_id)
            if text:
                entry["description"] = text
                filled += 1
            else:
                missing.append(entry_id)

    for desc_id in DESCRIPTIONS:
        if desc_id not in seen:
            missing.append(f"orphan:{desc_id}")

    return filled, skipped, missing


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing description fields",
    )
    args = parser.parse_args()

    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    filled, skipped, missing = enrich(catalog, force=args.force)
    rules_filled, rule_orphans = enrich_rules(catalog, force=args.force)

    # Stable field order: description and rules after label
    for kind in ("merits", "flaws"):
        ordered: list[dict[str, Any]] = []
        for entry in catalog[kind]:
            row = dict(entry)
            desc = row.pop("description", None)
            rules = row.pop("rules", None)
            out: dict[str, Any] = {}
            for k, v in row.items():
                out[k] = v
                if k == "label":
                    if desc is not None:
                        out["description"] = desc
                    if rules is not None:
                        out["rules"] = rules
            if desc is not None and "description" not in out:
                out["description"] = desc
            if rules is not None and "rules" not in out:
                out["rules"] = rules
            ordered.append(out)
        catalog[kind] = ordered

    CATALOG.write_text(json.dumps(catalog, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    desc_orphans = [m for m in missing if m.startswith("orphan:")]
    desc_gaps = [m for m in missing if not m.startswith("orphan:")]
    print(
        f"Updated {CATALOG.name}: descriptions filled={filled}, kept={skipped}, "
        f"desc_gaps={len(desc_gaps)}, desc_orphans={len(desc_orphans)}, "
        f"rules filled={rules_filled}, rule_orphans={len(rule_orphans)}"
    )
    if desc_gaps:
        print("Missing descriptions for:", ", ".join(desc_gaps))
        return 1
    if desc_orphans:
        print("Unused description keys:", ", ".join(m.replace("orphan:", "") for m in desc_orphans))
        return 1
    if rule_orphans:
        print("Unused rule keys:", ", ".join(rule_orphans))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
