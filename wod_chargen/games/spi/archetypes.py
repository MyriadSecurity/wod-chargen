"""SPI archetype loading with primary + subtype delta merge."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from wod_chargen.core.data_loader import load_json_cached
from wod_chargen.games.spi.paths import DATA_PKG

BIAS_KEYS = (
    "attribute_biases",
    "skill_biases",
    "affinity_biases",
    "merit_biases",
    "tag_affinities",
)


@lru_cache(maxsize=1)
def load_manifest() -> dict[str, Any]:
    return load_json_cached(DATA_PKG, "archetypes/_manifest.json")


def clear_archetype_caches() -> None:
    """Test helper after data edits."""
    load_manifest.cache_clear()
    get_archetype.cache_clear()
    get_sub_archetype.cache_clear()


@lru_cache(maxsize=32)
def get_archetype(archetype_id: str) -> dict[str, Any]:
    """Load primary archetype and attach listed subtypes (metadata only)."""
    primary = dict(load_json_cached(DATA_PKG, f"archetypes/{archetype_id}.json"))
    sub_ids = list((load_manifest().get("subtypes") or {}).get(archetype_id, []))
    subs: list[dict[str, Any]] = []
    for sid in sub_ids:
        raw = load_json_cached(DATA_PKG, f"archetypes/{archetype_id}/{sid}.json")
        subs.append(
            {
                "id": raw["id"],
                "label": raw.get("label", raw["id"]),
                "description": raw.get("description", ""),
                "modifiers": dict(raw.get("modifiers") or {}),
            }
        )
    primary["sub_archetypes"] = subs
    return primary


@lru_cache(maxsize=64)
def get_sub_archetype(archetype_id: str, sub_id: str) -> dict[str, Any]:
    arch = get_archetype(archetype_id)
    for sub in arch.get("sub_archetypes") or []:
        if sub["id"] == sub_id:
            return sub
    raise KeyError(f"Unknown SPI subtype {sub_id!r} for archetype {archetype_id!r}")


def default_sub_id(archetype_id: str) -> str:
    arch = get_archetype(archetype_id)
    subs = arch.get("sub_archetypes") or []
    if not subs:
        raise KeyError(f"Archetype {archetype_id!r} has no subtypes")
    return str(subs[0]["id"])


def resolve_sub_id(archetype_id: str, options: dict[str, Any] | None = None) -> str:
    """Pick subtype from options; default to first listed when missing/any/invalid."""
    opts = options or {}
    raw = opts.get("sub", opts.get("sub_archetype", ""))
    sub = str(raw or "").strip()
    arch = get_archetype(archetype_id)
    valid = {s["id"] for s in arch.get("sub_archetypes") or []}
    if sub and sub != "any" and sub in valid:
        return sub
    return default_sub_id(archetype_id)


def _apply_deltas(base: dict[str, float], deltas: dict[str, float]) -> dict[str, float]:
    merged = dict(base)
    for key, delta in (deltas or {}).items():
        merged[key] = float(merged.get(key, 1.0)) + float(delta)
    return merged


def effective_profile(archetype_id: str, sub_id: str | None = None) -> dict[str, Any]:
    """Primary absolute biases + subtype additive deltas (LotN-style)."""
    primary = get_archetype(archetype_id)
    sid = sub_id or default_sub_id(archetype_id)
    sub = get_sub_archetype(archetype_id, sid)
    mods = sub.get("modifiers") or {}

    out = {
        "id": primary["id"],
        "label": primary.get("label", primary["id"]),
        "description": primary.get("description", ""),
        "sub_id": sub["id"],
        "sub_label": sub.get("label", sub["id"]),
        "sub_description": sub.get("description", ""),
    }
    for key in BIAS_KEYS:
        base = dict(primary.get(key) or {})
        out[key] = _apply_deltas(base, dict(mods.get(key) or {}))
    return out


def list_archetypes() -> list[dict[str, Any]]:
    return [get_archetype(aid) for aid in load_manifest().get("primaries", [])]


def archetype_picker() -> list[dict[str, Any]]:
    return [
        {
            "id": a["id"],
            "label": a.get("label", a["id"]),
            "description": a.get("description", ""),
            "sub_archetypes": [
                {
                    "id": s["id"],
                    "label": s.get("label", s["id"]),
                    "description": s.get("description", ""),
                }
                for s in a.get("sub_archetypes") or []
            ],
        }
        for a in list_archetypes()
    ]
