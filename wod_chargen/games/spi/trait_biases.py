"""Resolve SPI merit bias from explicit keys and theme tag affinities."""

from __future__ import annotations

from functools import lru_cache
from typing import Any, Mapping

from wod_chargen.core.data_loader import load_json_cached
from wod_chargen.games.spi.paths import DATA_PKG

BIAS_MIN = 0.05
BIAS_MAX = 3.0


@lru_cache(maxsize=1)
def load_trait_tags() -> dict[str, Any]:
    return load_json_cached(DATA_PKG, "trait_tags.json")


def clear_trait_tags_cache() -> None:
    """Test helper — drop cached trait_tags after data edits."""
    load_trait_tags.cache_clear()


def trait_tag_list(merit_id: str) -> list[str]:
    data = load_trait_tags()
    tags = (data.get("merits") or {}).get(merit_id, [])
    if isinstance(tags, str):
        return [tags]
    return list(tags)


def theme_vocab() -> set[str]:
    return set((load_trait_tags().get("tags") or {}).keys())


def _clamp(value: float) -> float:
    return max(BIAS_MIN, min(BIAS_MAX, value))


def _as_bias_maps(profile: Mapping[str, Any] | Any) -> tuple[dict[str, float], dict[str, float]]:
    if isinstance(profile, Mapping):
        explicit = dict(profile.get("merit_biases") or {})
        affinities = dict(profile.get("tag_affinities") or {})
        return explicit, affinities
    explicit = dict(getattr(profile, "merit_biases", None) or {})
    affinities = dict(getattr(profile, "tag_affinities", None) or {})
    return explicit, affinities


def _tag_product(affinities: dict[str, float], merit_id: str) -> float:
    if not affinities:
        return 1.0
    product = 1.0
    matched = False
    for tag in trait_tag_list(merit_id):
        if tag.startswith("hard_opposed:"):
            opposed = tag.split(":", 1)[1]
            if opposed in affinities:
                product *= _clamp(float(affinities[opposed]) * 0.15)
                matched = True
            continue
        if tag.startswith("opposed:"):
            opposed = tag.split(":", 1)[1]
            if opposed in affinities:
                product *= _clamp(float(affinities[opposed]) * 0.55)
                matched = True
            continue
        if tag in affinities:
            product *= _clamp(float(affinities[tag]))
            matched = True
    if not matched:
        return 1.0
    return _clamp(product)


def resolve_merit_bias(profile: Mapping[str, Any] | Any, merit_id: str) -> float:
    """Effective merit bias: explicit override, else tag product, else 1.0."""
    explicit, affinities = _as_bias_maps(profile)
    if merit_id in explicit:
        return _clamp(float(explicit[merit_id]))
    return _tag_product(affinities, merit_id)
