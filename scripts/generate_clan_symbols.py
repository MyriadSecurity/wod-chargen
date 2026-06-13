#!/usr/bin/env python3
"""Generate minimalist clan symbol SVGs for the faction picker."""

from __future__ import annotations

from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "static" / "img" / "clans"
STROKE = "#c9a0a8"
FILL = "#8b1538"
ACCENT = "#e8e4dc"

SYMBOLS: dict[str, str] = {
    "brujah": f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" fill="none">
  <path d="M32 8 L38 22 L52 24 L42 34 L44 50 L32 42 L20 50 L22 34 L12 24 L26 22 Z" stroke="{STROKE}" stroke-width="2" fill="{FILL}" opacity="0.35"/>
  <path d="M28 38 L28 18 M28 18 L22 12 M28 18 L34 12" stroke="{ACCENT}" stroke-width="3" stroke-linecap="round"/>
  <circle cx="28" cy="42" r="4" fill="{FILL}"/>
</svg>""",
    "gangrel": f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" fill="none">
  <path d="M18 40 C14 34 12 26 16 18 C20 10 30 8 38 12 C46 16 50 26 48 36 C46 46 36 52 26 50 C22 48 20 44 18 40 Z" stroke="{STROKE}" stroke-width="2" fill="{FILL}" opacity="0.3"/>
  <circle cx="28" cy="26" r="2.5" fill="{ACCENT}"/>
  <circle cx="38" cy="26" r="2.5" fill="{ACCENT}"/>
  <path d="M30 34 Q34 38 40 34" stroke="{ACCENT}" stroke-width="2" stroke-linecap="round"/>
  <path d="M14 22 L8 14 M50 22 L56 14" stroke="{STROKE}" stroke-width="2" stroke-linecap="round"/>
</svg>""",
    "malkavian": f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" fill="none">
  <path d="M32 8 C18 8 10 20 10 32 C10 44 18 56 32 56 C46 56 54 44 54 32 C54 20 46 8 32 8 Z" stroke="{STROKE}" stroke-width="2"/>
  <path d="M32 14 C24 20 20 28 20 32 C20 38 24 46 32 50 C40 46 44 38 44 32 C44 28 40 20 32 14 Z" stroke="{FILL}" stroke-width="2" fill="{FILL}" opacity="0.25"/>
  <path d="M32 18 C28 24 26 30 26 34 C26 40 28 44 32 46 C36 44 38 40 38 34 C38 30 36 24 32 18 Z" stroke="{ACCENT}" stroke-width="1.5" fill="none"/>
  <circle cx="32" cy="32" r="3" fill="{FILL}"/>
</svg>""",
    "nosferatu": f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" fill="none">
  <ellipse cx="32" cy="36" rx="18" ry="14" stroke="{STROKE}" stroke-width="2" fill="{FILL}" opacity="0.25"/>
  <circle cx="26" cy="32" r="3" fill="{ACCENT}"/>
  <circle cx="38" cy="32" r="3" fill="{ACCENT}"/>
  <path d="M28 40 L32 44 L36 40" stroke="{ACCENT}" stroke-width="2" stroke-linecap="round"/>
  <path d="M20 28 L10 22 M44 28 L54 22 M24 20 L20 10 M40 20 L44 10" stroke="{STROKE}" stroke-width="2" stroke-linecap="round"/>
  <path d="M18 48 L14 56 M46 48 L50 56" stroke="{STROKE}" stroke-width="2" stroke-linecap="round"/>
</svg>""",
    "toreador": f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" fill="none">
  <path d="M32 52 L32 28 C32 20 24 16 20 20 C16 24 18 32 24 36 L32 28" stroke="{STROKE}" stroke-width="2" fill="none"/>
  <path d="M32 28 C40 24 46 16 42 10 C38 6 30 10 28 18 L32 28" stroke="{FILL}" stroke-width="2" fill="{FILL}" opacity="0.35"/>
  <circle cx="24" cy="14" r="5" stroke="{STROKE}" stroke-width="2" fill="{FILL}" opacity="0.4"/>
  <path d="M20 10 L28 10" stroke="{ACCENT}" stroke-width="1.5"/>
</svg>""",
    "tremere": f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" fill="none">
  <path d="M32 10 L52 50 L12 50 Z" stroke="{STROKE}" stroke-width="2" fill="{FILL}" opacity="0.2"/>
  <path d="M32 18 L44 46 L20 46 Z" stroke="{FILL}" stroke-width="1.5" fill="none"/>
  <circle cx="32" cy="30" r="6" stroke="{ACCENT}" stroke-width="2" fill="{FILL}" opacity="0.5"/>
  <path d="M32 24 L32 36 M26 30 L38 30" stroke="{ACCENT}" stroke-width="1.5"/>
</svg>""",
    "ventrue": f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" fill="none">
  <path d="M16 44 C16 44 20 36 32 36 C44 36 48 44 48 44" stroke="{STROKE}" stroke-width="2" fill="none"/>
  <path d="M20 44 L20 48 L44 48 L44 44" stroke="{STROKE}" stroke-width="2" fill="{FILL}" opacity="0.2"/>
  <path d="M22 28 L32 14 L42 28" stroke="{STROKE}" stroke-width="2" fill="{FILL}" opacity="0.3"/>
  <rect x="28" y="20" width="8" height="6" rx="1" fill="{ACCENT}"/>
  <circle cx="32" cy="16" r="3" fill="{FILL}"/>
</svg>""",
    "lasombra": f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" fill="none">
  <path d="M32 8 L44 20 L44 44 C44 52 38 56 32 56 C26 56 20 52 20 44 L20 20 Z" stroke="{STROKE}" stroke-width="2" fill="#0a0a12"/>
  <circle cx="32" cy="22" r="6" fill="{FILL}" opacity="0.6"/>
  <path d="M26 36 L32 30 L38 36 L32 50 Z" stroke="{ACCENT}" stroke-width="2" fill="{FILL}" opacity="0.4"/>
  <path d="M8 56 L56 56" stroke="{STROKE}" stroke-width="3" opacity="0.5"/>
</svg>""",
    "ministry": f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" fill="none">
  <path d="M32 12 C24 20 20 32 22 44 C24 52 28 56 32 56 C36 56 40 52 42 44 C44 32 40 20 32 12 Z" stroke="{STROKE}" stroke-width="2" fill="{FILL}" opacity="0.25"/>
  <path d="M32 8 L28 16 L36 16 Z" fill="{FILL}"/>
  <ellipse cx="26" cy="30" rx="3" ry="4" fill="{ACCENT}"/>
  <ellipse cx="38" cy="30" rx="3" ry="4" fill="{ACCENT}"/>
  <path d="M32 38 L30 48 L34 48 Z" fill="{ACCENT}"/>
  <path d="M32 56 L32 62" stroke="{STROKE}" stroke-width="2"/>
</svg>""",
    "hecata": f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" fill="none">
  <circle cx="32" cy="28" r="16" stroke="{STROKE}" stroke-width="2" fill="{FILL}" opacity="0.2"/>
  <circle cx="26" cy="26" r="3" fill="{ACCENT}"/>
  <circle cx="38" cy="26" r="3" fill="{ACCENT}"/>
  <path d="M24 36 Q32 42 40 36" stroke="{ACCENT}" stroke-width="2" fill="none"/>
  <path d="M20 48 L16 56 M44 48 L48 56 M28 44 L24 58 M36 44 L40 58" stroke="{STROKE}" stroke-width="2" stroke-linecap="round"/>
</svg>""",
    "ravnos": f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" fill="none">
  <circle cx="32" cy="32" r="22" stroke="{STROKE}" stroke-width="2" fill="none"/>
  <circle cx="32" cy="32" r="4" fill="{FILL}"/>
  <path d="M32 10 L32 54 M10 32 L54 32 M16 16 L48 48 M48 16 L16 48" stroke="{FILL}" stroke-width="2" opacity="0.6"/>
  <circle cx="32" cy="10" r="3" fill="{ACCENT}"/>
  <circle cx="54" cy="32" r="3" fill="{ACCENT}"/>
  <circle cx="32" cy="54" r="3" fill="{ACCENT}"/>
  <circle cx="10" cy="32" r="3" fill="{ACCENT}"/>
</svg>""",
    "tzimisce": f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" fill="none">
  <path d="M12 40 C20 28 28 20 32 12 C36 20 44 28 52 40 C44 36 36 34 32 38 C28 34 20 36 12 40 Z" stroke="{STROKE}" stroke-width="2" fill="{FILL}" opacity="0.3"/>
  <path d="M32 12 L32 38 M24 24 L40 24" stroke="{ACCENT}" stroke-width="2"/>
  <path d="M20 44 C28 48 36 48 44 44" stroke="{STROKE}" stroke-width="2" fill="none"/>
  <circle cx="32" cy="20" r="3" fill="{FILL}"/>
</svg>""",
    "salubri": f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" fill="none">
  <path d="M32 10 L52 50 L12 50 Z" stroke="{STROKE}" stroke-width="2" fill="none"/>
  <ellipse cx="32" cy="30" rx="10" ry="12" stroke="{FILL}" stroke-width="2" fill="{FILL}" opacity="0.25"/>
  <circle cx="32" cy="28" r="5" stroke="{ACCENT}" stroke-width="2" fill="{FILL}" opacity="0.5"/>
  <circle cx="32" cy="28" r="2" fill="{ACCENT}"/>
  <path d="M32 34 L32 42" stroke="{ACCENT}" stroke-width="2" stroke-linecap="round"/>
</svg>""",
    "caitiff": f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" fill="none">
  <circle cx="32" cy="32" r="22" stroke="{STROKE}" stroke-width="2" stroke-dasharray="6 4" fill="none"/>
  <path d="M32 18 L32 46 M22 26 L42 38 M42 26 L22 38" stroke="{FILL}" stroke-width="2" opacity="0.5"/>
  <circle cx="32" cy="32" r="6" stroke="{ACCENT}" stroke-width="2" fill="none"/>
</svg>""",
    "thin_blood": f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" fill="none">
  <path d="M32 10 L38 28 L56 30 L42 42 L46 58 L32 48 L18 58 L22 42 L8 30 L26 28 Z" stroke="{STROKE}" stroke-width="2" fill="{FILL}" opacity="0.2"/>
  <circle cx="32" cy="32" r="10" stroke="{ACCENT}" stroke-width="2" fill="none"/>
  <path d="M32 26 C28 30 26 34 28 38 C30 42 34 42 36 38 C38 34 36 30 32 26 Z" fill="{FILL}" opacity="0.7"/>
  <path d="M32 38 L32 46" stroke="{ACCENT}" stroke-width="2" stroke-linecap="round"/>
</svg>""",
}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for clan_id, svg in SYMBOLS.items():
        path = OUT / f"{clan_id}.svg"
        path.write_text(svg.strip() + "\n", encoding="utf-8")
        print(f"Wrote {path.name}")
    print(f"Generated {len(SYMBOLS)} clan symbols in {OUT}")


if __name__ == "__main__":
    main()
