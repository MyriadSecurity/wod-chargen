"""Resolve effective trait bias from archetype profile explicit keys and tag affinities."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from wod_chargen.core.data_loader import load_json_cached
from wod_chargen.games.lotn_v5.paths import DATA_PKG

BIAS_MIN = 0.05
BIAS_MAX = 3.0

TRAIT_CATEGORIES = (
    "attributes",
    "skills",
    "disciplines",
    "merits",
    "flaws",
    "powers",
    "backgrounds",
    "spheres",
    "modifiers",
    "loresheets",
)

_EXPLICIT_FIELD: dict[str, str] = {
    "attributes": "attribute_biases",
    "skills": "skill_biases",
    "disciplines": "discipline_biases",
    "merits": "merit_biases",
    "flaws": "flaw_biases",
    "powers": "discipline_power_biases",
    "backgrounds": "background_biases",
    "spheres": "sphere_biases",
    "modifiers": "modifier_biases",
    "loresheets": "loresheet_biases",
}


@lru_cache(maxsize=1)
def load_trait_tags() -> dict[str, Any]:
    return load_json_cached(DATA_PKG, "trait_tags.json")


@lru_cache(maxsize=1)
def load_power_utility() -> dict[str, Any]:
    return load_json_cached(DATA_PKG, "discipline_power_utility.json")


def power_utility_bias(power_id: str) -> float:
    """Archetype-neutral LARP usefulness for a discipline power (0.9–1.2 typical)."""
    spec = load_power_utility()
    overrides = spec.get("powers", {})
    if power_id in overrides:
        return _clamp(float(overrides[power_id]))

    from wod_chargen.games.lotn_v5.disciplines import power_by_id

    power = power_by_id(power_id)
    if power is None:
        return float(spec.get("default", 1.0))

    level_defaults = spec.get("level_defaults", {})
    level = str(int(power["level"]))
    if level in level_defaults:
        return _clamp(float(level_defaults[level]))
    return float(spec.get("default", 1.0))


def trait_tag_list(trait_id: str, category: str) -> list[str]:
    data = load_trait_tags()
    block = data.get(category, {})
    tags = block.get(trait_id, [])
    if isinstance(tags, str):
        return [tags]
    return list(tags)


def _clamp(value: float) -> float:
    return max(BIAS_MIN, min(BIAS_MAX, value))


def _explicit_bias(profile: Any, trait_id: str, category: str) -> float | None:
    field = _EXPLICIT_FIELD.get(category)
    if not field:
        return None
    biases = getattr(profile, field, None) or {}
    if trait_id in biases:
        return _clamp(float(biases[trait_id]))
    return None


def _tag_product(profile: Any, trait_id: str, category: str) -> float:
    affinities: dict[str, float] = getattr(profile, "tag_affinities", None) or {}
    if not affinities:
        return 1.0
    product = 1.0
    for tag in trait_tag_list(trait_id, category):
        if tag.startswith("hard_opposed:"):
            opposed = tag.split(":", 1)[1]
            if opposed in affinities:
                product *= _clamp(float(affinities[opposed]) * 0.15)
            continue
        if tag.startswith("opposed:"):
            opposed = tag.split(":", 1)[1]
            if opposed in affinities:
                product *= _clamp(float(affinities[opposed]) * 0.55)
            continue
        if tag in affinities:
            product *= _clamp(float(affinities[tag]))
    return _clamp(product)


def resolve_trait_bias(profile: Any, trait_id: str, category: str) -> float:
    """Return effective bias for a trait: explicit override, else tag product, else 1.0."""
    if category not in TRAIT_CATEGORIES:
        raise ValueError(f"Unknown trait category: {category!r}")
    explicit = _explicit_bias(profile, trait_id, category)
    if explicit is not None:
        return explicit
    tag_bias = _tag_product(profile, trait_id, category)
    return tag_bias if tag_bias != 1.0 else 1.0


def build_power_biases(
    profile: Any,
    power_ids: list[str],
    *,
    char: dict[str, Any] | None = None,
    track_id: str | None = None,
    clan_pool: frozenset[str] | set[str] | None = None,
) -> dict[str, float]:
    """Precompute power biases: archetype theme × neutral LARP usefulness."""
    from wod_chargen.games.lotn_v5.clan_discipline_adapt import IN_CLAN_POWER_FLOOR, char_clan_pool
    from wod_chargen.games.lotn_v5.disciplines import power_by_id

    if clan_pool is None and char is not None:
        clan_pool = char_clan_pool(char)

    out: dict[str, float] = {}
    for pid in power_ids:
        theme = resolve_trait_bias(profile, pid, "powers") * power_utility_bias(pid)
        if (
            char is not None
            and clan_pool
            and _explicit_bias(profile, pid, "powers") is None
        ):
            disc_id = track_id or (power_by_id(pid) or {}).get("discipline_id")
            rating = int(char.get("disciplines", {}).get(disc_id, 0)) if disc_id else 0
            if disc_id in clan_pool and rating >= 1 and theme < IN_CLAN_POWER_FLOOR:
                theme = IN_CLAN_POWER_FLOOR
        out[pid] = _clamp(theme)
    return out
