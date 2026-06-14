#!/usr/bin/env python3
"""Report discipline power bias coverage gaps per archetype."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from wod_chargen.core.data_loader import load_json_cached  # noqa: E402
from wod_chargen.games.lotn_v5.archetypes import effective_profile, load_all_archetypes  # noqa: E402
from wod_chargen.games.lotn_v5.clan_discipline_adapt import adapt_profile_for_clan  # noqa: E402
from wod_chargen.games.lotn_v5.disciplines import load_power_catalog, power_by_id  # noqa: E402
from wod_chargen.games.lotn_v5.trait_biases import resolve_trait_bias  # noqa: E402


def _in_clan_disciplines(clan_id: str) -> list[str]:
    clans = load_json_cached("wod_chargen.games.lotn_v5.data", "clans.json")
    return list(clans.get(clan_id, {}).get("disciplines", []))


def _disc_summary(profile, disc_id: str) -> dict[str, int | float | str]:
    boosts = suppress = neutral = 0
    max_boost = 0.0
    max_boost_id = ""
    for disc in load_power_catalog()["disciplines"]:
        if disc["id"] != disc_id:
            continue
        for power in disc["powers"]:
            pid = power["id"]
            theme = resolve_trait_bias(profile, pid, "powers")
            if theme > 1.05:
                boosts += 1
                if theme > max_boost:
                    max_boost = theme
                    max_boost_id = pid
            elif theme < 0.95:
                suppress += 1
            else:
                neutral += 1
    return {
        "boosts": boosts,
        "suppress": suppress,
        "neutral": neutral,
        "max_boost": max_boost,
        "max_boost_id": max_boost_id,
    }


def _has_expression_alternate(profile, disc_id: str) -> bool:
    expr = profile.discipline_expressions or {}
    return disc_id in (expr.get("alternates") or {})


def _matrix_rows(clan_id: str, arch_filter: str) -> list[dict[str, str | int]]:
    in_clan = _in_clan_disciplines(clan_id)
    profiles = load_all_archetypes()
    if arch_filter:
        profiles = {arch_filter: profiles[arch_filter]}

    rows: list[dict[str, str | int]] = []
    for arch_id, base in sorted(profiles.items()):
        ctype = base.allowed_types[0] if base.allowed_types else "vampire"
        if ctype != "vampire":
            continue
        sub = base.sub_archetypes[0]
        profile = adapt_profile_for_clan(effective_profile(arch_id, sub.id, ctype), clan_id)
        for disc_id in in_clan:
            s = _disc_summary(profile, disc_id)
            explicit_keys = [
                pid
                for pid in profile.discipline_power_biases
                if (pw := power_by_id(pid)) and pw["discipline_id"] == disc_id
            ]
            flagged = (
                s["suppress"] > 0
                and s["boosts"] == 0
                and not explicit_keys
                and not _has_expression_alternate(profile, disc_id)
            )
            rows.append(
                {
                    "archetype": arch_id,
                    "sub": sub.id,
                    "clan": clan_id,
                    "in_clan_disc": disc_id,
                    "boost": s["boosts"],
                    "suppress": s["suppress"],
                    "neutral": s["neutral"],
                    "explicit_powers": len(explicit_keys),
                    "expression_alternate": int(_has_expression_alternate(profile, disc_id)),
                    "flagged": int(flagged),
                }
            )
    return rows


def _print_matrix(clan_id: str, arch_filter: str, csv_out: str | None) -> None:
    rows = _matrix_rows(clan_id, arch_filter)
    fields = [
        "archetype",
        "sub",
        "clan",
        "in_clan_disc",
        "boost",
        "suppress",
        "neutral",
        "explicit_powers",
        "expression_alternate",
        "flagged",
    ]
    if csv_out:
        with open(csv_out, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
        print(f"Wrote {len(rows)} rows to {csv_out}")
        return

    print(",".join(fields))
    for row in rows:
        print(",".join(str(row[f]) for f in fields))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--clan", default="toreador", help="Clan for in-clan discipline context")
    parser.add_argument("--arch", default="", help="Single archetype id (default: all)")
    parser.add_argument("--matrix", action="store_true", help="CSV matrix of in-clan coverage")
    parser.add_argument("--csv", default="", help="Write matrix to file")
    args = parser.parse_args()

    if args.matrix:
        _print_matrix(args.clan, args.arch, args.csv or None)
        return

    in_clan = _in_clan_disciplines(args.clan)
    profiles = load_all_archetypes()
    if args.arch:
        profiles = {args.arch: profiles[args.arch]}

    for arch_id, base in sorted(profiles.items()):
        ctype = base.allowed_types[0] if base.allowed_types else "vampire"
        if ctype != "vampire":
            continue
        sub = base.sub_archetypes[0]
        profile = adapt_profile_for_clan(effective_profile(arch_id, sub.id, ctype), args.clan)
        explicit_count = len(profile.discipline_power_biases)

        print(f"\n== {arch_id} / {sub.id} (explicit power keys: {explicit_count}) ==")
        print(f"In-clan ({args.clan}): {', '.join(in_clan)}")

        for disc_id in in_clan:
            s = _disc_summary(profile, disc_id)
            explicit_keys = [
                pid
                for pid in profile.discipline_power_biases
                if (pw := power_by_id(pid)) and pw["discipline_id"] == disc_id
            ]
            flag = ""
            if s["suppress"] and not s["boosts"] and not explicit_keys and not _has_expression_alternate(
                profile, disc_id
            ):
                flag = "  ← theme-only suppression, no signature picks"
            elif explicit_keys:
                flag = f"  ← {len(explicit_keys)} signature power(s)"
            elif _has_expression_alternate(profile, disc_id):
                flag = "  ← expression alternate defined"
            print(
                f"  {disc_id:18} boost={s['boosts']:2} neutral={s['neutral']:2} "
                f"suppress={s['suppress']:2}{flag}"
            )


if __name__ == "__main__":
    main()
