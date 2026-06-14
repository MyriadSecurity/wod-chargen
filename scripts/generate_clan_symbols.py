#!/usr/bin/env python3
"""Generate thin-blood clan symbol SVG (no official wiki asset)."""

from __future__ import annotations

from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "static" / "img" / "clans"
STROKE = "#c9a0a8"
FILL = "#8b1538"
ACCENT = "#e8e4dc"

THIN_BLOOD = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" fill="none">
  <path d="M32 10 L38 28 L56 30 L42 42 L46 58 L32 48 L18 58 L22 42 L8 30 L26 28 Z" stroke="{STROKE}" stroke-width="2" fill="{FILL}" opacity="0.2"/>
  <circle cx="32" cy="32" r="10" stroke="{ACCENT}" stroke-width="2" fill="none"/>
  <path d="M32 26 C28 30 26 34 28 38 C30 42 34 42 36 38 C38 34 36 30 32 26 Z" fill="{FILL}" opacity="0.7"/>
  <path d="M32 38 L32 46" stroke="{ACCENT}" stroke-width="2" stroke-linecap="round"/>
</svg>"""


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "thin_blood.svg"
    path.write_text(THIN_BLOOD.strip() + "\n", encoding="utf-8")
    print(f"Wrote {path.name}")
    print("Official clan PNGs: uv run python scripts/fetch_clan_symbols_wiki.py")


if __name__ == "__main__":
    main()
