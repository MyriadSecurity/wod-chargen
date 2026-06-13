"""Resolve effective trait bias from archetype profile explicit keys and tag affinities."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from wod_chargen.core.data_loader import load_json_cached

DATA_PKG = "wod_chargen.games.lotn_v5.data"

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
}


@lru_cache(maxsize=1)
def load_trait_tags() -> dict[str, Any]:
    return load_json_cached(DATA_PKG, "trait_tags.json")


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


def build_power_biases(profile: Any, power_ids: list[str]) -> dict[str, float]:
    """Precompute power biases for pick_power (explicit + tag resolution per id)."""
    return {pid: resolve_trait_bias(profile, pid, "powers") for pid in power_ids}
