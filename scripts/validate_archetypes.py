#!/usr/bin/env python3
"""Validate archetype base JSON + per-sub modifier files."""

from __future__ import annotations

import sys

from wod_chargen.games.lotn_v5.archetypes import load_all_archetypes

MIN_SUBS = 2


def main() -> int:
    profiles = load_all_archetypes()
    errors: list[str] = []
    sub_total = 0
    for arch_id, profile in profiles.items():
        if not profile.description.strip():
            errors.append(f"{arch_id}: missing description")
        n = len(profile.sub_archetypes)
        sub_total += n
        if n < MIN_SUBS:
            errors.append(f"{arch_id}: expected at least {MIN_SUBS} subtypes, got {n}")
        labels = [s.label for s in profile.sub_archetypes]
        if len(labels) != len(set(labels)):
            errors.append(f"{arch_id}: duplicate subtype labels")
        for sub in profile.sub_archetypes:
            if not sub.description.strip():
                errors.append(f"{arch_id}/{sub.id}: missing description")
            if sub.label.strip().lower() == profile.label.strip().lower():
                errors.append(f"{arch_id}/{sub.id}: subtype label mirrors primary")
            has_mod = any(
                (
                    sub.weight_deltas,
                    sub.attribute_bias_deltas,
                    sub.skill_bias_deltas,
                    sub.discipline_bias_deltas,
                )
            )
            if not has_mod:
                errors.append(f"{arch_id}/{sub.id}: modifiers block is empty")
    if errors:
        for err in errors:
            print(err, file=sys.stderr)
        return 1
    print(f"Validated {len(profiles)} archetypes, {sub_total} subtypes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
