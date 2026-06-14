"""Shared grant helpers for predator and loresheet benefit packages."""

from __future__ import annotations

from typing import Any

from wod_chargen.core.rng import SeededRng
from wod_chargen.games.lotn_v5.archetypes import ArchetypeProfile
from wod_chargen.games.lotn_v5.backgrounds import (
    background_defs,
    background_label,
    can_add_modifier_dot,
    entries_for_type,
    get_modifier_rating,
    grant_background_rating,
    set_modifier_rating,
)
from wod_chargen.games.lotn_v5.merits_flaws import (
    apply_enemy_flaw,
    apply_trait_dots,
    trait_display_label,
    trait_label,
)

def split_dots(rng: SeededRng, total: int, options: list[str]) -> dict[str, int]:
    allocation = {opt: 0 for opt in options}
    for _ in range(total):
        allocation[rng.choice(options)] += 1
    return allocation


def background_mod_def(bg_type: str, mod_id: str, kind: str) -> dict[str, Any] | None:
    key = "advantages" if kind == "advantage" else "disadvantages"
    for mod in background_defs().get(bg_type, {}).get(key, []):
        if mod["id"] == mod_id:
            return mod
    return None


def latest_background_entry(entries: list[dict[str, Any]], bg_type: str) -> dict[str, Any] | None:
    typed = entries_for_type(entries, bg_type)
    return typed[-1] if typed else None


def record_predator_modifier(char: dict[str, Any], dots: int) -> None:
    meta = char.setdefault("background_meta", {})
    meta["predator_modifier_dots"] = int(meta.get("predator_modifier_dots", 0)) + dots


def attach_advantage(
    entry: dict[str, Any],
    mod_id: str,
    dots: int,
    *,
    char: dict[str, Any] | None = None,
    log_prefix: str = "Predator",
) -> str | None:
    mod_def = background_mod_def(entry["type"], mod_id, "advantage")
    if not mod_def:
        return None
    before = get_modifier_rating(entry, mod_id, "advantage")
    target = max(before, int(dots))
    if target <= before or not can_add_modifier_dot(entry, mod_def, "advantage"):
        return None
    set_modifier_rating(entry, mod_id, "advantage", target)
    added = target - before
    if char is not None and added > 0:
        record_predator_modifier(char, added)
    label = mod_def["label"]
    return f"{log_prefix}: {background_label(entry['type'])} advantage {label} •{'•' * target}"


def grant_background_spec(
    rng: SeededRng,
    entries: list[dict[str, Any]],
    spec: dict[str, Any],
    profile: ArchetypeProfile,
    *,
    char: dict[str, Any] | None = None,
) -> list[str]:
    lines: list[str] = []
    bg_type = spec["type"]
    dots = int(spec["dots"])
    sphere = spec.get("sphere")
    if sphere is None and spec.get("sphere_options"):
        sphere = rng.choice(list(spec["sphere_options"]))

    if spec.get("split_instances") and dots > 1:
        max_dots = int(background_defs()[bg_type].get("max_dots", 3))
        remaining = dots
        while remaining > 0:
            chunk = min(remaining, max_dots)
            line = grant_background_rating(
                rng, entries, bg_type, chunk, profile, sphere=sphere, from_predator=True, char=char
            )
            if line:
                lines.append(line)
            remaining -= chunk
    else:
        line = grant_background_rating(
            rng,
            entries,
            bg_type,
            dots,
            profile,
            sphere=sphere,
            name=spec.get("name"),
            from_predator=True,
            char=char,
        )
        if line:
            lines.append(line)

    entry = latest_background_entry(entries, bg_type)
    if not entry:
        return lines

    adv = spec.get("advantage")
    if adv:
        adv_line = attach_advantage(entry, adv["id"], int(adv.get("dots", 1)), char=char)
        if adv_line:
            lines.append(adv_line)

    adv_pick = spec.get("advantage_pick")
    if adv_pick:
        mod_id = rng.choice(list(adv_pick["options"]))
        adv_line = attach_advantage(entry, mod_id, int(adv_pick.get("dots", 1)), char=char)
        if adv_line:
            lines.append(adv_line)

    return lines


def apply_flaw_grant(
    rng: SeededRng,
    char: dict[str, Any],
    entries: list[dict[str, Any]],
    flaw_spec: dict[str, Any],
    profile: ArchetypeProfile,
) -> list[str]:
    if flaw_spec.get("pick"):
        choice = rng.choice(flaw_spec["options"])
        return apply_flaw_grant(rng, char, entries, choice, profile)

    flaw_id = flaw_spec["id"]
    dots = int(flaw_spec.get("dots", 1))
    category = flaw_spec.get("category", "")
    note = flaw_spec.get("note", "")
    label = trait_label(flaw_id, "flaw")

    if category in ("herd", "haven"):
        bg_type = category
        typed = entries_for_type(entries, bg_type)
        mod_def = background_mod_def(bg_type, flaw_id, "disadvantage")
        if typed and mod_def and can_add_modifier_dot(typed[0], mod_def, "disadvantage", char):
            set_modifier_rating(typed[0], flaw_id, "disadvantage", dots)
            return [f"Predator: {background_defs()[bg_type]['label']} flaw {label} •{'•' * dots}"]

    flaws = char.setdefault("flaws", {})
    if flaw_id == "enemy":
        added, key = apply_enemy_flaw(rng, char, profile, dots, ignore_rules=True)
        if added <= 0 or not key:
            return []
        suffix = f" ({note})" if note else ""
        return [
            f"Predator: Flaw {trait_display_label(key, 'flaw')} •{'•' * flaws[key]}{suffix}"
        ]

    added = apply_trait_dots(flaws, flaw_id, "flaw", dots, char, ignore_rules=True)
    if added <= 0:
        return []
    suffix = f" ({note})" if note else ""
    return [f"Predator: Flaw {label} •{'•' * flaws[flaw_id]}{suffix}"]


def apply_flaw_spend(
    rng: SeededRng,
    char: dict[str, Any],
    flaw_spend: dict[str, Any],
    profile: ArchetypeProfile,
) -> list[str]:
    lines: list[str] = []
    allocation = split_dots(rng, int(flaw_spend["dots"]), list(flaw_spend["options"]))
    flaws = char.setdefault("flaws", {})
    for flaw_id, grant in allocation.items():
        if grant <= 0:
            continue
        if flaw_id == "enemy":
            added, key = apply_enemy_flaw(rng, char, profile, grant, ignore_rules=True)
            if added <= 0 or not key:
                continue
            lines.append(f"Predator: Flaw {trait_display_label(key, 'flaw')} •{'•' * flaws[key]}")
            continue
        apply_trait_dots(flaws, flaw_id, "flaw", grant, char, ignore_rules=True)
        label = trait_label(flaw_id, "flaw")
        lines.append(f"Predator: Flaw {label} •{'•' * flaws[flaw_id]}")
    return lines

