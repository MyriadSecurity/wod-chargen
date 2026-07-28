#!/usr/bin/env python3
"""Copy SPI extract catalogs into wod_chargen/games/spi/data (strip Codex blurbs)."""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "reference" / "spi" / "extracted"
DST = ROOT / "wod_chargen" / "games" / "spi" / "data"

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


def _strip_merits(payload: dict) -> dict:
    merits_out = []
    for entry in payload.get("merits", []):
        cleaned = {k: v for k, v in entry.items() if k not in DROP_MERIT_KEYS}
        merits_out.append(cleaned)
    return {
        "notes": "SPI merit/affinity catalog (ids, dots, prereqs, tags). No Codex blurbs.",
        "merits": merits_out,
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
    stripped = _strip_merits(payload)
    out = DST / "merits.json"
    out.write_text(json.dumps(stripped, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote merits.json ({len(stripped['merits'])} entries, blurbs stripped)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
