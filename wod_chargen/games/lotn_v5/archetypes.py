"""Archetype JSON loader and validation."""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
from typing import Any

from wod_chargen.core.data_loader import load_json_cached
from wod_chargen.games.lotn_v5.paths import DATA_PKG
from wod_chargen.games.lotn_v5.trait_biases import load_trait_tags

VALID_TYPES = {"vampire", "ghoul", "thin_blood"}
THIN_BLOOD_ONLY_SUFFIX = " *** Thin-Blood Only ***"

BIAS_MODIFIER_KEYS = (
    "weights",
    "attribute_biases",
    "skill_biases",
    "discipline_biases",
    "merit_biases",
    "flaw_biases",
    "background_biases",
    "sphere_biases",
    "modifier_biases",
    "discipline_power_biases",
    "tag_affinities",
    "loresheet_biases",
)

# Legacy alias for tests importing MODIFIER_KEYS
MODIFIER_KEYS = BIAS_MODIFIER_KEYS


@dataclass(frozen=True)
class SubArchetypeProfile:
    id: str
    label: str
    description: str
    weight_deltas: dict[str, float]
    attribute_bias_deltas: dict[str, float]
    skill_bias_deltas: dict[str, float]
    discipline_bias_deltas: dict[str, float]
    merit_bias_deltas: dict[str, float] = field(default_factory=dict)
    flaw_bias_deltas: dict[str, float] = field(default_factory=dict)
    background_bias_deltas: dict[str, float] = field(default_factory=dict)
    sphere_bias_deltas: dict[str, float] = field(default_factory=dict)
    modifier_bias_deltas: dict[str, float] = field(default_factory=dict)
    discipline_power_bias_deltas: dict[str, float] = field(default_factory=dict)
    tag_affinity_deltas: dict[str, float] = field(default_factory=dict)
    loresheet_bias_deltas: dict[str, float] = field(default_factory=dict)


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
    merit_biases: dict[str, float] = field(default_factory=dict)
    flaw_biases: dict[str, float] = field(default_factory=dict)
    background_biases: dict[str, float] = field(default_factory=dict)
    sphere_biases: dict[str, float] = field(default_factory=dict)
    modifier_biases: dict[str, float] = field(default_factory=dict)
    discipline_power_biases: dict[str, float] = field(default_factory=dict)
    tag_affinities: dict[str, float] = field(default_factory=dict)
    discipline_expressions: dict[str, Any] = field(default_factory=dict)
    loresheet_biases: dict[str, float] = field(default_factory=dict)


def _registry_ids() -> dict[str, set[str]]:
    attrs = set(load_json_cached(DATA_PKG, "attributes.json")["all"])
    skills = set(load_json_cached(DATA_PKG, "skills.json")["all"])
    discs = set(load_json_cached(DATA_PKG, "disciplines.json")["all"])
    mf = load_json_cached(DATA_PKG, "merits_flaws.json")
    merits = {m["id"] for m in mf["merits"]}
    flaws = {f["id"] for f in mf["flaws"]}
    bg = load_json_cached(DATA_PKG, "backgrounds.json")
    backgrounds = set(bg["backgrounds"].keys())
    spheres = {s["id"] for s in bg["spheres"]}
    modifiers: set[str] = set()
    for spec in bg["backgrounds"].values():
        for mod in spec.get("advantages", []) + spec.get("disadvantages", []):
            modifiers.add(mod["id"])
    tags = set(load_trait_tags().get("tags", {}).keys())
    powers: set[str] = set()
    for disc in load_json_cached(DATA_PKG, "discipline_powers.json")["disciplines"]:
        for p in disc.get("powers", []):
            powers.add(p["id"])
    loresheets = {ls["id"] for ls in load_json_cached(DATA_PKG, "loresheets.json")["loresheets"]}
    return {
        "attribute_biases": attrs,
        "skill_biases": skills,
        "discipline_biases": discs,
        "merit_biases": merits,
        "flaw_biases": flaws,
        "background_biases": backgrounds,
        "sphere_biases": spheres,
        "modifier_biases": modifiers,
        "discipline_power_biases": powers,
        "tag_affinities": tags,
        "loresheet_biases": loresheets,
    }


def _validate_bias_keys(data: dict[str, float], registry: set[str], label: str, arch_id: str) -> None:
    for key in data:
        if key not in registry:
            raise ValueError(f"Unknown {label} key {key!r} in archetype {arch_id!r}")


def _parse_bias_block(
    raw: dict[str, Any],
    key: str,
    arch_id: str,
    sub_id: str,
    registries: dict[str, set[str]],
) -> dict[str, float]:
    block = {k: float(v) for k, v in raw.get(key, {}).items()}
    registry = registries.get(key)
    if registry is not None and block:
        _validate_bias_keys(block, registry, key.replace("_", " "), f"{arch_id}/{sub_id}")
    return block


def _parse_modifiers(raw: dict[str, Any], arch_id: str, sub_id: str) -> dict[str, dict[str, float]]:
    registries = _registry_ids()
    modifiers = raw.get("modifiers", {})
    if not modifiers and any(k in raw for k in ("weight_deltas", "skill_bias_deltas", "discipline_bias_deltas")):
        modifiers = {
            "weights": raw.get("weight_deltas", {}),
            "attribute_biases": raw.get("attribute_bias_deltas", {}),
            "skill_biases": raw.get("skill_bias_deltas", {}),
            "discipline_biases": raw.get("discipline_bias_deltas", {}),
        }
    parsed: dict[str, dict[str, float]] = {}
    for key in BIAS_MODIFIER_KEYS:
        parsed[key] = _parse_bias_block(modifiers, key, arch_id, sub_id, registries)
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
        merit_bias_deltas=mods["merit_biases"],
        flaw_bias_deltas=mods["flaw_biases"],
        background_bias_deltas=mods["background_biases"],
        sphere_bias_deltas=mods["sphere_biases"],
        modifier_bias_deltas=mods["modifier_biases"],
        discipline_power_bias_deltas=mods["discipline_power_biases"],
        tag_affinity_deltas=mods["tag_affinities"],
        loresheet_bias_deltas=mods["loresheet_biases"],
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
    registries = _registry_ids()
    for key in (
        "attribute_biases",
        "skill_biases",
        "discipline_biases",
        "merit_biases",
        "flaw_biases",
        "background_biases",
        "sphere_biases",
        "modifier_biases",
        "discipline_power_biases",
        "tag_affinities",
        "loresheet_biases",
    ):
        block = {k: float(v) for k, v in raw.get(key, {}).items()}
        registry = registries.get(key)
        if registry is not None and block:
            _validate_bias_keys(block, registry, key.replace("_", " "), arch_id)
        raw[key] = block

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
        attribute_biases=raw.get("attribute_biases", {}),
        skill_biases=raw.get("skill_biases", {}),
        discipline_biases=raw.get("discipline_biases", {}),
        sub_archetypes=subs,
        allowed_types=allowed,
        type_weights=raw.get("type_weights", {}),
        merit_biases=raw.get("merit_biases", {}),
        flaw_biases=raw.get("flaw_biases", {}),
        background_biases=raw.get("background_biases", {}),
        sphere_biases=raw.get("sphere_biases", {}),
        modifier_biases=raw.get("modifier_biases", {}),
        discipline_power_biases=raw.get("discipline_power_biases", {}),
        tag_affinities=raw.get("tag_affinities", {}),
        discipline_expressions=dict(raw.get("discipline_expressions") or {}),
        loresheet_biases=raw.get("loresheet_biases", {}),
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


def is_thin_blood_only(profile: ArchetypeProfile) -> bool:
    return profile.allowed_types == ("thin_blood",)


def archetype_display_label(profile: ArchetypeProfile) -> str:
    if is_thin_blood_only(profile):
        return f"{profile.label}{THIN_BLOOD_ONLY_SUFFIX}"
    return profile.label


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
    merit_biases = _apply_deltas(base.merit_biases, sub.merit_bias_deltas)
    flaw_biases = _apply_deltas(base.flaw_biases, sub.flaw_bias_deltas)
    background_biases = _apply_deltas(base.background_biases, sub.background_bias_deltas)
    sphere_biases = _apply_deltas(base.sphere_biases, sub.sphere_bias_deltas)
    modifier_biases = _apply_deltas(base.modifier_biases, sub.modifier_bias_deltas)
    power_biases = _apply_deltas(base.discipline_power_biases, sub.discipline_power_bias_deltas)
    tag_affinities = _apply_deltas(base.tag_affinities, sub.tag_affinity_deltas)
    loresheet_biases = _apply_deltas(base.loresheet_biases, sub.loresheet_bias_deltas)

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
        merit_biases=merit_biases,
        flaw_biases=flaw_biases,
        background_biases=background_biases,
        sphere_biases=sphere_biases,
        modifier_biases=modifier_biases,
        discipline_power_biases=power_biases,
        tag_affinities=tag_affinities,
        discipline_expressions=base.discipline_expressions,
        loresheet_biases=loresheet_biases,
    )
