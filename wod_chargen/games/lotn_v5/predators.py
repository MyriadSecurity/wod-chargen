"""Predator type catalog, validation, and generation bias helpers."""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from wod_chargen.core.data_loader import load_json_cached
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
from wod_chargen.games.lotn_v5.merits_flaws import apply_enemy_flaw, apply_trait_dots, trait_display_label, trait_label

DATA = "wod_chargen.games.lotn_v5.data"


def load_predator_types() -> list[dict[str, Any]]:
    return load_json_cached(DATA, "predator_types.json")["types"]


def predator_by_id(predator_id: str) -> dict[str, Any]:
    for entry in load_predator_types():
        if entry["id"] == predator_id:
            return entry
    raise KeyError(f"Unknown predator type: {predator_id!r}")


def resolve_predator(
    options: dict[str, Any],
    rng: SeededRng,
    *,
    types: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    catalog = types if types is not None else load_predator_types()
    by_id = {t["id"]: t for t in catalog}
    chosen = options.get("predator")
    if chosen and chosen in by_id:
        return by_id[chosen]
    return rng.weighted_choice(catalog, [t["weight"] for t in catalog])


def _multiply_bias_map(base: dict[str, float], extra: dict[str, float]) -> dict[str, float]:
    merged = dict(base)
    for key, weight in extra.items():
        merged[key] = merged.get(key, 1.0) * float(weight)
    return merged


def apply_predator_biases(profile: ArchetypeProfile, predator: dict[str, Any]) -> ArchetypeProfile:
    pool_weights = predator.get("pool_weights") or {}
    benefit_weights = predator.get("benefit_weights") or {}
    return replace(
        profile,
        attribute_biases=_multiply_bias_map(profile.attribute_biases, pool_weights.get("attributes", {})),
        skill_biases=_multiply_bias_map(
            _multiply_bias_map(profile.skill_biases, pool_weights.get("skills", {})),
            benefit_weights.get("skills", {}),
        ),
        discipline_biases=_multiply_bias_map(profile.discipline_biases, benefit_weights.get("disciplines", {})),
    )


def predator_background_biases(predator: dict[str, Any]) -> dict[str, float]:
    return dict((predator.get("benefit_weights") or {}).get("backgrounds", {}))


def validate_predator_catalog(types: list[dict[str, Any]] | None = None) -> None:
    catalog = types if types is not None else load_predator_types()
    attrs = set(load_json_cached(DATA, "attributes.json")["all"])
    skills = set(load_json_cached(DATA, "skills.json")["all"])
    discs = set(load_json_cached(DATA, "disciplines.json")["all"])
    bg_types = set(load_json_cached(DATA, "backgrounds.json")["backgrounds"].keys())

    for entry in catalog:
        pid = entry["id"]
        if not entry.get("feeding_pool"):
            raise ValueError(f"{pid}: missing feeding_pool")
        if not entry.get("benefits"):
            raise ValueError(f"{pid}: missing display benefits")
        if "drawbacks" not in entry:
            raise ValueError(f"{pid}: missing drawbacks key")
        if "package" not in entry:
            raise ValueError(f"{pid}: missing package")

        pool = entry.get("pool")
        pool_weights = entry.get("pool_weights") or {}
        benefit_weights = entry.get("benefit_weights") or {}
        package = entry["package"]

        if pool:
            attr = pool["attribute"]
            skill = pool["skill"]
            if attr not in attrs:
                raise ValueError(f"{pid}: unknown pool attribute {attr!r}")
            if skill not in skills:
                raise ValueError(f"{pid}: unknown pool skill {skill!r}")
            if pool_weights.get("attributes", {}).get(attr, 0) <= 0:
                raise ValueError(f"{pid}: pool_weights missing primary attribute {attr!r}")
            if pool_weights.get("skills", {}).get(skill, 0) <= 0:
                raise ValueError(f"{pid}: pool_weights missing primary skill {skill!r}")

        for key in pool_weights.get("attributes", {}):
            if key not in attrs:
                raise ValueError(f"{pid}: unknown pool_weights attribute {key!r}")
        for key in pool_weights.get("skills", {}):
            if key not in skills:
                raise ValueError(f"{pid}: unknown pool_weights skill {key!r}")
        for key in benefit_weights.get("skills", {}):
            if key not in skills:
                raise ValueError(f"{pid}: unknown benefit_weights skill {key!r}")
        for key in benefit_weights.get("disciplines", {}):
            if key not in discs:
                raise ValueError(f"{pid}: unknown benefit_weights discipline {key!r}")
        for key in benefit_weights.get("backgrounds", {}):
            if key not in bg_types:
                raise ValueError(f"{pid}: unknown benefit_weights background {key!r}")

        _validate_package(pid, package, skills, discs, bg_types)


def _validate_package(
    pid: str,
    package: dict[str, Any],
    skills: set[str],
    discs: set[str],
    bg_types: set[str],
) -> None:
    for spec in package.get("specialties", []):
        if spec["skill"] not in skills:
            raise ValueError(f"{pid}: unknown specialty skill {spec['skill']!r}")

    disc = package.get("disciplines")
    if disc:
        clan_only = disc.get("clan_only", {})
        for opt in disc.get("options", []):
            if opt not in discs and opt not in clan_only:
                raise ValueError(f"{pid}: unknown discipline option {opt!r}")

    for bg in package.get("backgrounds", []):
        _validate_bg_spec(pid, bg, bg_types)

    for grant in package.get("background_grants", []):
        _validate_bg_spec(pid, grant, bg_types)

    spend = package.get("background_spend")
    if spend:
        for opt in spend.get("options", []):
            if opt not in bg_types:
                raise ValueError(f"{pid}: unknown background_spend option {opt!r}")

    adv_spend = package.get("advantage_spend")
    if adv_spend:
        bg_type = adv_spend.get("background")
        if bg_type not in bg_types:
            raise ValueError(f"{pid}: unknown advantage_spend background {bg_type!r}")


def _validate_bg_spec(pid: str, spec: dict[str, Any], bg_types: set[str]) -> None:
    bg_type = spec["type"]
    if bg_type not in bg_types:
        raise ValueError(f"{pid}: unknown background type {bg_type!r}")
    adv = spec.get("advantage")
    if adv:
        mod_def = _background_mod_def(bg_type, adv["id"], "advantage")
        if not mod_def:
            raise ValueError(f"{pid}: unknown {bg_type} advantage {adv['id']!r}")
    adv_pick = spec.get("advantage_pick")
    if adv_pick:
        for opt in adv_pick.get("options", []):
            if not _background_mod_def(bg_type, opt, "advantage"):
                raise ValueError(f"{pid}: unknown {bg_type} advantage option {opt!r}")


def _split_dots(rng: SeededRng, total: int, options: list[str]) -> dict[str, int]:
    allocation = {opt: 0 for opt in options}
    for _ in range(total):
        allocation[rng.choice(options)] += 1
    return allocation


def _background_mod_def(bg_type: str, mod_id: str, kind: str) -> dict[str, Any] | None:
    key = "advantages" if kind == "advantage" else "disadvantages"
    for mod in background_defs().get(bg_type, {}).get(key, []):
        if mod["id"] == mod_id:
            return mod
    return None


def _latest_background_entry(entries: list[dict[str, Any]], bg_type: str) -> dict[str, Any] | None:
    typed = entries_for_type(entries, bg_type)
    return typed[-1] if typed else None


def _record_predator_modifier(char: dict[str, Any], dots: int) -> None:
    meta = char.setdefault("background_meta", {})
    meta["predator_modifier_dots"] = int(meta.get("predator_modifier_dots", 0)) + dots


def _attach_advantage(
    entry: dict[str, Any],
    mod_id: str,
    dots: int,
    *,
    char: dict[str, Any] | None = None,
    log_prefix: str = "Predator",
) -> str | None:
    mod_def = _background_mod_def(entry["type"], mod_id, "advantage")
    if not mod_def:
        return None
    before = get_modifier_rating(entry, mod_id, "advantage")
    target = max(before, int(dots))
    if target <= before or not can_add_modifier_dot(entry, mod_def, "advantage"):
        return None
    set_modifier_rating(entry, mod_id, "advantage", target)
    added = target - before
    if char is not None and added > 0:
        _record_predator_modifier(char, added)
    label = mod_def["label"]
    return f"{log_prefix}: {background_label(entry['type'])} advantage {label} •{'•' * target}"


def _grant_background_spec(
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

    entry = _latest_background_entry(entries, bg_type)
    if not entry:
        return lines

    adv = spec.get("advantage")
    if adv:
        adv_line = _attach_advantage(entry, adv["id"], int(adv.get("dots", 1)), char=char)
        if adv_line:
            lines.append(adv_line)

    adv_pick = spec.get("advantage_pick")
    if adv_pick:
        mod_id = rng.choice(list(adv_pick["options"]))
        adv_line = _attach_advantage(entry, mod_id, int(adv_pick.get("dots", 1)), char=char)
        if adv_line:
            lines.append(adv_line)

    return lines


def _apply_flaw_grant(
    rng: SeededRng,
    char: dict[str, Any],
    entries: list[dict[str, Any]],
    flaw_spec: dict[str, Any],
    profile: ArchetypeProfile,
) -> list[str]:
    if flaw_spec.get("pick"):
        choice = rng.choice(flaw_spec["options"])
        return _apply_flaw_grant(rng, char, entries, choice, profile)

    flaw_id = flaw_spec["id"]
    dots = int(flaw_spec.get("dots", 1))
    category = flaw_spec.get("category", "")
    note = flaw_spec.get("note", "")
    label = trait_label(flaw_id, "flaw")

    if category in ("herd", "haven"):
        bg_type = category
        typed = entries_for_type(entries, bg_type)
        mod_def = _background_mod_def(bg_type, flaw_id, "disadvantage")
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


def _apply_flaw_spend(
    rng: SeededRng,
    char: dict[str, Any],
    flaw_spend: dict[str, Any],
    profile: ArchetypeProfile,
) -> list[str]:
    lines: list[str] = []
    allocation = _split_dots(rng, int(flaw_spend["dots"]), list(flaw_spend["options"]))
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


def apply_predator_package(
    predator: dict[str, Any],
    char: dict[str, Any],
    rng: SeededRng,
    profile: ArchetypeProfile,
    *,
    caps: dict[str, int],
) -> list[str]:
    """Apply structured predator benefits and drawbacks after base creation."""
    from wod_chargen.games.lotn_v5.benefit_packages import apply_benefit_package

    lines = apply_benefit_package(
        predator.get("package") or {},
        char,
        rng,
        profile,
        caps=caps,
        log_prefix="Predator",
    )
    char["predator_meta"] = {
        "package_applied": True,
        "log_lines": len(lines),
        "requires_max_blood_potency": predator.get("requires_max_blood_potency"),
    }
    return lines
