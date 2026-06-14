#!/usr/bin/env python3
"""Report discipline power bias coverage gaps per archetype."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from wod_chargen.core.data_loader import load_json_cached  # noqa: E402
from wod_chargen.games.lotn_v5.archetypes import effective_profile, load_all_archetypes  # noqa: E402
from wod_chargen.games.lotn_v5.disciplines import load_power_catalog  # noqa: E402
from wod_chargen.games.lotn_v5.trait_biases import (  # noqa: E402
    _explicit_bias,
    _tag_product,
    power_utility_bias,
    resolve_trait_bias,
)


def _in_clan_disciplines(clan_id: str) -> list[str]:
    clans = load_json_cached("wod_chargen.games.lotn_v5.data", "clans.json")
    return list(clans.get(clan_id, {}).get("disciplines", []))


def _disc_summary(profile, disc_id: str) -> dict[str, int | float]:
    boosts = suppress = neutral = 0
    max_boost = 0.0
    max_boost_id = ""
    for disc in load_power_catalog()["disciplines"]:
        if disc["id"] != disc_id:
            continue
        for power in disc["powers"]:
            pid = power["id"]
            theme = resolve_trait_bias(profile, pid, "powers")
            utility = power_utility_bias(pid)
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


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--clan", default="toreador", help="Clan for in-clan discipline context")
    parser.add_argument("--arch", default="", help="Single archetype id (default: all)")
    args = parser.parse_args()

    in_clan = _in_clan_disciplines(args.clan)
    profiles = load_all_archetypes()
    if args.arch:
        profiles = {args.arch: profiles[args.arch]}

    for arch_id, base in sorted(profiles.items()):
        ctype = base.allowed_types[0] if base.allowed_types else "vampire"
        if ctype != "vampire":
            continue
        sub = base.sub_archetypes[0]
        profile = effective_profile(arch_id, sub.id, ctype)
        explicit_count = len(profile.discipline_power_biases)

        print(f"\n== {arch_id} / {sub.id} (explicit power keys: {explicit_count}) ==")
        print(f"In-clan ({args.clan}): {', '.join(in_clan)}")
        from wod_chargen.games.lotn_v5.disciplines import power_by_id

        for disc_id in in_clan:
            s = _disc_summary(profile, disc_id)
            explicit_keys = [
                pid
                for pid in profile.discipline_power_biases
                if (pw := power_by_id(pid)) and pw["discipline_id"] == disc_id
            ]
            flag = ""
            if s["suppress"] and not s["boosts"] and not explicit_keys:
                flag = "  ← theme-only suppression, no signature picks"
            elif explicit_keys:
                flag = f"  ← {len(explicit_keys)} signature power(s)"
            print(
                f"  {disc_id:18} boost={s['boosts']:2} neutral={s['neutral']:2} "
                f"suppress={s['suppress']:2}{flag}"
            )


if __name__ == "__main__":
    main()
