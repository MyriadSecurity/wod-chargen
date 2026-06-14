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

from wod_chargen.games.lotn_v5.paths import DATA_PKG as DATA
from wod_chargen.games.lotn_v5.trait_catalog import (
    attribute_ids,
    background_ids,
    discipline_ids,
    skill_ids,
)


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
    attrs = attribute_ids()
    skills = skill_ids()
    discs = discipline_ids()
    bg_types = background_ids()

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


from wod_chargen.games.lotn_v5.package_grants import background_mod_def as _background_mod_def

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
