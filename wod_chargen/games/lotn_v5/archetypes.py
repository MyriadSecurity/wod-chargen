"""Archetype JSON loader and validation."""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
from typing import Any

from wod_chargen.core.data_loader import load_json_cached

DATA_PKG = "wod_chargen.games.lotn_v5.data"
VALID_TYPES = {"vampire", "ghoul", "thin_blood"}
MODIFIER_KEYS = ("weights", "attribute_biases", "skill_biases", "discipline_biases")


@dataclass(frozen=True)
class SubArchetypeProfile:
    id: str
    label: str
    description: str
    weight_deltas: dict[str, float]
    attribute_bias_deltas: dict[str, float]
    skill_bias_deltas: dict[str, float]
    discipline_bias_deltas: dict[str, float]


@dataclass(frozen=True)
class ArchetypeProfile:
    id: str
    label: str
    description: str
    weights: dict[str, float]
    attribute_biases: dict[str, float]
    skill_biases: dict[str, float]
    discipline_biases: dict[str, float]
    sub_archetypes: tuple[SubArchetypeProfile, ...]
    allowed_types: tuple[str, ...] = ()
    type_weights: dict[str, dict[str, float]] = field(default_factory=dict)


def _registry_ids() -> tuple[set[str], set[str], set[str]]:
    attrs = set(load_json_cached(DATA_PKG, "attributes.json")["all"])
    skills = set(load_json_cached(DATA_PKG, "skills.json")["all"])
    discs = set(load_json_cached(DATA_PKG, "disciplines.json")["all"])
    return attrs, skills, discs


def _validate_bias_keys(data: dict[str, Any], registry: set[str], label: str, arch_id: str) -> None:
    for key in data:
        if key not in registry:
            raise ValueError(f"Unknown {label} key {key!r} in archetype {arch_id!r}")


def _parse_modifiers(raw: dict[str, Any], arch_id: str, sub_id: str) -> dict[str, dict[str, float]]:
    attrs, skills, discs = _registry_ids()
    modifiers = raw.get("modifiers", {})
    if not modifiers and any(k in raw for k in ("weight_deltas", "skill_bias_deltas", "discipline_bias_deltas")):
        modifiers = {
            "weights": raw.get("weight_deltas", {}),
            "attribute_biases": raw.get("attribute_bias_deltas", {}),
            "skill_biases": raw.get("skill_bias_deltas", {}),
            "discipline_biases": raw.get("discipline_bias_deltas", {}),
        }
    parsed: dict[str, dict[str, float]] = {}
    for key in MODIFIER_KEYS:
        block = {k: float(v) for k, v in modifiers.get(key, {}).items()}
        if key == "attribute_biases":
            _validate_bias_keys(block, attrs, "attribute", f"{arch_id}/{sub_id}")
        elif key == "skill_biases":
            _validate_bias_keys(block, skills, "skill", f"{arch_id}/{sub_id}")
        elif key == "discipline_biases":
            _validate_bias_keys(block, discs, "discipline", f"{arch_id}/{sub_id}")
        parsed[key] = block
    return parsed


def _parse_sub(raw: dict[str, Any], arch_id: str) -> SubArchetypeProfile:
    sub_id = raw["id"]
    mods = _parse_modifiers(raw, arch_id, sub_id)
    return SubArchetypeProfile(
        id=sub_id,
        label=raw["label"],
        description=raw.get("description", ""),
        weight_deltas=mods["weights"],
        attribute_bias_deltas=mods["attribute_biases"],
        skill_bias_deltas=mods["skill_biases"],
        discipline_bias_deltas=mods["discipline_biases"],
    )


def _load_sub_archetypes(arch_id: str, inline: list[dict[str, Any]] | None = None) -> tuple[SubArchetypeProfile, ...]:
    if inline:
        return tuple(_parse_sub(sub, arch_id) for sub in inline)

    manifest = load_json_cached(DATA_PKG, "archetypes/_manifest.json")
    sub_ids = manifest.get("subtypes", {}).get(arch_id)
    if not sub_ids:
        raise ValueError(f"Archetype {arch_id!r} has no subtypes in manifest")

    subs: list[SubArchetypeProfile] = []
    for sub_id in sub_ids:
        raw = load_json_cached(DATA_PKG, f"archetypes/{arch_id}/{sub_id}.json")
        subs.append(_parse_sub(raw, arch_id))
    if not subs:
        raise ValueError(f"Archetype {arch_id!r} has no sub-archetype JSON files")
    return tuple(subs)


def _parse_profile(raw: dict[str, Any]) -> ArchetypeProfile:
    arch_id = raw["id"]
    attrs, skills, discs = _registry_ids()
    _validate_bias_keys(raw.get("attribute_biases", {}), attrs, "attribute", arch_id)
    _validate_bias_keys(raw.get("skill_biases", {}), skills, "skill", arch_id)
    _validate_bias_keys(raw.get("discipline_biases", {}), discs, "discipline", arch_id)

    allowed = tuple(raw.get("allowed_types", ()))
    for t in allowed:
        if t not in VALID_TYPES:
            raise ValueError(f"Invalid allowed_types entry {t!r} in {arch_id}")

    inline = raw.get("sub_archetypes")
    subs = _load_sub_archetypes(arch_id, inline if inline else None)

    ids = [s.id for s in subs]
    if len(ids) != len(set(ids)):
        raise ValueError(f"Duplicate sub-archetype ids in {arch_id!r}")

    return ArchetypeProfile(
        id=arch_id,
        label=raw["label"],
        description=raw.get("description", ""),
        weights={k: float(v) for k, v in raw["weights"].items()},
        attribute_biases={k: float(v) for k, v in raw.get("attribute_biases", {}).items()},
        skill_biases={k: float(v) for k, v in raw.get("skill_biases", {}).items()},
        discipline_biases={k: float(v) for k, v in raw.get("discipline_biases", {}).items()},
        sub_archetypes=subs,
        allowed_types=allowed,
        type_weights=raw.get("type_weights", {}),
    )


@lru_cache(maxsize=1)
def load_all_archetypes() -> dict[str, ArchetypeProfile]:
    profiles: dict[str, ArchetypeProfile] = {}
    manifest = load_json_cached(DATA_PKG, "archetypes/_manifest.json")
    for arch_id in manifest["primaries"]:
        raw = load_json_cached(DATA_PKG, f"archetypes/{arch_id}.json")
        profile = _parse_profile(raw)
        profiles[profile.id] = profile
    return profiles


def get_archetype(arch_id: str) -> ArchetypeProfile:
    profiles = load_all_archetypes()
    if arch_id not in profiles:
        raise ValueError(f"Unknown archetype: {arch_id}")
    return profiles[arch_id]


def archetypes_for_type(character_type: str) -> list[ArchetypeProfile]:
    result = []
    for profile in load_all_archetypes().values():
        if profile.allowed_types and character_type not in profile.allowed_types:
            continue
        result.append(profile)
    return sorted(result, key=lambda p: p.id)


def _apply_deltas(base: dict[str, float], deltas: dict[str, float]) -> dict[str, float]:
    merged = dict(base)
    for key, delta in deltas.items():
        merged[key] = merged.get(key, 1.0) + delta
    return merged


def effective_profile(
    arch_id: str,
    sub_id: str,
    character_type: str,
    venue_overrides: dict[str, Any] | None = None,
) -> ArchetypeProfile:
    base = get_archetype(arch_id)
    if base.allowed_types and character_type not in base.allowed_types:
        raise ValueError(f"Archetype {arch_id!r} not allowed for type {character_type!r}")

    sub = next((s for s in base.sub_archetypes if s.id == sub_id), None)
    if sub is None:
        raise ValueError(f"Unknown sub-archetype {sub_id!r} for {arch_id!r}")

    weights = _apply_deltas(base.weights, sub.weight_deltas)
    if character_type in base.type_weights:
        for k, v in base.type_weights[character_type].items():
            weights[k] = weights.get(k, 1.0) * v

    attribute_biases = _apply_deltas(base.attribute_biases, sub.attribute_bias_deltas)
    skill_biases = _apply_deltas(base.skill_biases, sub.skill_bias_deltas)
    disc_biases = _apply_deltas(base.discipline_biases, sub.discipline_bias_deltas)

    if venue_overrides and arch_id in venue_overrides:
        vo = venue_overrides[arch_id]
        for k, v in vo.get("skill_biases", {}).items():
            skill_biases[k] = skill_biases.get(k, 1.0) + v

    return ArchetypeProfile(
        id=base.id,
        label=base.label,
        description=base.description,
        weights=weights,
        attribute_biases=attribute_biases,
        skill_biases=skill_biases,
        discipline_biases=disc_biases,
        sub_archetypes=base.sub_archetypes,
        allowed_types=base.allowed_types,
        type_weights=base.type_weights,
    )
