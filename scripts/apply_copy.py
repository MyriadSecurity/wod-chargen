#!/usr/bin/env python3
"""Apply player-facing copy to clan JSON."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CLANS = ROOT / "wod_chargen" / "games" / "lotn_v5" / "data" / "clans.json"

CLAN_COPY = {
    "brujah": "Revolution in their veins and a grudge for anyone talking down to them.",
    "gangrel": "More comfortable on the road than in a salon.",
    "malkavian": "Sees the crack in everything. Can't always explain it.",
    "nosferatu": "Ugly, unseen, and usually first to know.",
    "toreador": "Beauty is leverage. They never forget to spend it.",
    "tremere": "Rank, ritual, and blood magic behind locked doors.",
    "ventrue": "Breeding, boardrooms, and the assumption you'll obey.",
    "lasombra": "Faith, shadow, and a smile that never reaches the eyes.",
    "ministry": "Vice sold as salvation. Serpents in good linen.",
    "hecata": "Death is family business. They collect on both sides.",
    "ravnos": "A good story beats the truth. They travel light.",
    "tzimisce": "Landlords of nightmare. They remember every trespass.",
    "salubri": "Healers with a price on their heads.",
    "caitiff": "No clan. Pick three Disciplines and make your own luck.",
    "thin_blood": "Half in the mortal world. Alchemy where pedigree fails.",
}


def main() -> None:
    clans = json.loads(CLANS.read_text(encoding="utf-8"))
    for cid, text in CLAN_COPY.items():
        clans[cid]["description"] = text
    CLANS.write_text(json.dumps(clans, indent=2) + "\n", encoding="utf-8")
    print(f"Updated {len(CLAN_COPY)} clan descriptions")


if __name__ == "__main__":
    main()
