#!/usr/bin/env python3
"""Invert clan symbol PNGs (RGB only) so black wiki assets read on the dark theme."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CLANS_DIR = ROOT / "static" / "img" / "clans"
MANIFEST = CLANS_DIR / "manifest.json"


def invert_png(path: Path) -> None:
    from PIL import Image, ImageOps

    with Image.open(path) as img:
        rgba = img.convert("RGBA")
        r, g, b, a = rgba.split()
        inverted_rgb = ImageOps.invert(Image.merge("RGB", (r, g, b)))
        ir, ig, ib = inverted_rgb.split()
        out = Image.merge("RGBA", (ir, ig, ib, a))
        out.save(path, format="PNG", optimize=True)


def clan_png_paths() -> list[Path]:
    if MANIFEST.is_file():
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
        return [ROOT / rel for rel in data.values()]
    return sorted(CLANS_DIR.glob("*.png"))


def main() -> int:
    paths = clan_png_paths()
    if not paths:
        print("No clan PNGs found.", file=sys.stderr)
        return 1

    for path in paths:
        if not path.is_file():
            print(f"skip missing: {path}", file=sys.stderr)
            continue
        invert_png(path)
        print(f"inverted {path.relative_to(ROOT)}")

    print(f"Inverted {len(paths)} clan symbol(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
