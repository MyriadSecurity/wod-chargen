#!/usr/bin/env python3
"""Copy SPI extract catalogs into wod_chargen/games/spi/data (strip Codex blurbs).

Merits are filtered to Rules Addendum–sanctioned entries via
`sanctioned_merit_ids.json` (rebuild with scripts/build_spi_sanctioned_merit_ids.py).
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "reference" / "spi" / "extracted"
DST = ROOT / "wod_chargen" / "games" / "spi" / "data"
ALLOWLIST = DST / "sanctioned_merit_ids.json"

COPY_AS_IS = (
    "creation.json",
    "costs.json",
    "attributes.json",
    "skills.json",
    "affinity_types.json",
    "advantages.json",
)
# divisions.json is authored in-package (bias hooks); not overwritten by extract.

DROP_MERIT_KEYS = frozenset({"summary", "book", "summary_source"})


def _load_allowlist() -> tuple[bool, set[str]]:
    if not ALLOWLIST.is_file():
        print(f"ERROR: missing {ALLOWLIST}", file=sys.stderr)
        print("Run scripts/build_spi_sanctioned_merit_ids.py first.", file=sys.stderr)
        raise SystemExit(1)
    data = json.loads(ALLOWLIST.read_text(encoding="utf-8"))
    keep_all_affinity = bool(data.get("keep_all_affinity", True))
    general_ids = set(data.get("general_ids") or [])
    if not general_ids and data.get("entries"):
        general_ids = {
            e["id"] for e in data["entries"] if e.get("category") == "general"
        }
    return keep_all_affinity, general_ids


def _strip_and_filter_merits(payload: dict) -> dict:
    keep_all_affinity, general_ids = _load_allowlist()
    merits_out = []
    skipped = 0
    for entry in payload.get("merits", []):
        cat = entry.get("category")
        mid = entry.get("id")
        if cat == "affinity":
            if not keep_all_affinity:
                skipped += 1
                continue
        elif cat == "general":
            if mid not in general_ids:
                skipped += 1
                continue
        else:
            skipped += 1
            continue
        cleaned = {k: v for k, v in entry.items() if k not in DROP_MERIT_KEYS}
        merits_out.append(cleaned)
    return {
        "notes": (
            "SPI merit/affinity catalog (ids, dots, prereqs, tags). "
            "Sanctioned material only (Rules Addendum + sheet extract). No Codex blurbs."
        ),
        "merits": merits_out,
        "_seed_skipped": skipped,
    }


def main() -> int:
    if not SRC.is_dir():
        print(f"ERROR: extract dir missing: {SRC}", file=sys.stderr)
        print("Run scripts/extract_spi_sheet_catalogs.py first.", file=sys.stderr)
        return 1

    DST.mkdir(parents=True, exist_ok=True)
    for name in COPY_AS_IS:
        src = SRC / name
        if not src.is_file():
            print(f"ERROR: missing {src}", file=sys.stderr)
            return 1
        shutil.copy2(src, DST / name)
        print(f"copied {name}")

    merits_src = SRC / "merits.json"
    if not merits_src.is_file():
        print(f"ERROR: missing {merits_src}", file=sys.stderr)
        return 1
    payload = json.loads(merits_src.read_text(encoding="utf-8"))
    stripped = _strip_and_filter_merits(payload)
    skipped = stripped.pop("_seed_skipped", 0)
    out = DST / "merits.json"
    out.write_text(json.dumps(stripped, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        f"wrote merits.json ({len(stripped['merits'])} sanctioned entries, "
        f"{skipped} unsanctioned skipped, blurbs stripped)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
