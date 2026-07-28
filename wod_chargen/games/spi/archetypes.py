"""SPI archetype loading (primaries only for MVP)."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from wod_chargen.core.data_loader import load_json_cached
from wod_chargen.games.spi.paths import DATA_PKG


@lru_cache(maxsize=1)
def load_manifest() -> dict[str, Any]:
    return load_json_cached(DATA_PKG, "archetypes/_manifest.json")


@lru_cache(maxsize=32)
def get_archetype(archetype_id: str) -> dict[str, Any]:
    return load_json_cached(DATA_PKG, f"archetypes/{archetype_id}.json")


def list_archetypes() -> list[dict[str, Any]]:
    return [get_archetype(aid) for aid in load_manifest().get("primaries", [])]


def archetype_picker() -> list[dict[str, str]]:
    return [
        {
            "id": a["id"],
            "label": a.get("label", a["id"]),
            "description": a.get("description", ""),
        }
        for a in list_archetypes()
    ]
