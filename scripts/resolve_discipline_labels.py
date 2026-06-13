#!/usr/bin/env python3
"""Validate discipline power label/slug index and rules references."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CATALOG = ROOT / "wod_chargen" / "games" / "lotn_v5" / "data" / "discipline_powers.json"


def main() -> int:
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    ids: set[str] = set()
    for disc in catalog["disciplines"]:
        for power in disc["powers"]:
            ids.add(power["id"])

    errors: list[str] = []
    for disc in catalog["disciplines"]:
        for power in disc["powers"]:
            rules = power.get("rules") or {}
            for key in ("requires_all_powers", "requires_any_powers"):
                for ref in rules.get(key, []):
                    if ref not in ids:
                        errors.append(f"{power['id']}: missing ref {ref!r} in {key}")
            amalg = rules.get("amalgam_discipline")
            if amalg and amalg not in {d["id"] for d in catalog["disciplines"]}:
                errors.append(f"{power['id']}: unknown amalgam discipline {amalg!r}")

    if errors:
        for e in errors:
            print(e, file=sys.stderr)
        return 1
    print(f"OK — {len(ids)} power ids, rules validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
