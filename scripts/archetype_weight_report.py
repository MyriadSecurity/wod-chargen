#!/usr/bin/env python3
"""CSV report of top weighted picks per archetype over N seeds."""

from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from wod_chargen.games.lotn_v5.archetypes import load_all_archetypes  # noqa: E402
from wod_chargen.core.data_loader import load_json_cached  # noqa: E402
from wod_chargen.games.lotn_v5.generator import generate_character  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=20)
    parser.add_argument("--venue", default="mes_end_to_dawn")
    parser.add_argument("-o", "--output", type=Path, default=Path("archetype_weight_report.csv"))
    args = parser.parse_args()

    rows: list[dict[str, str | int]] = []
    for arch_id, profile in sorted(load_all_archetypes().items()):
        sub_id = profile.sub_archetypes[0].id
        ctype = profile.allowed_types[0] if profile.allowed_types else "vampire"
        skill_hits: Counter[str] = Counter()
        disc_hits: Counter[str] = Counter()
        for seed in range(args.seeds):
            result = generate_character(
                seed,
                {
                    "type": ctype,
                    "clan": "brujah" if ctype == "vampire" else "thin_blood",
                    "arch": arch_id,
                    "sub": sub_id,
                    "approval": "2026-06",
                },
                load_json_cached("wod_chargen.venues", "mes_end_to_dawn.json"),
            )
            char = result.character
            if char["skills"]:
                skill_hits[max(char["skills"], key=char["skills"].get)] += 1
            for disc, rating in char.get("disciplines", {}).items():
                if rating > 0:
                    disc_hits[disc] += rating
        top_skills = ", ".join(f"{k}({v})" for k, v in skill_hits.most_common(5))
        top_discs = ", ".join(f"{k}({v})" for k, v in disc_hits.most_common(5))
        rows.append(
            {
                "archetype": arch_id,
                "sub": sub_id,
                "seeds": args.seeds,
                "top_skills": top_skills,
                "top_disciplines": top_discs,
            }
        )

    with args.output.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {args.output} ({len(rows)} archetypes, {args.seeds} seeds each)")


if __name__ == "__main__":
    main()
