"""Venue-scoped UI dispatch — fail closed for unknown game ids."""

from __future__ import annotations

from types import ModuleType
from typing import Any, Callable

from app import strategy_content_lotn as lotn_guide
from app import strategy_content_spi as spi_guide
from app import weight_map_data as lotn_weights
from app import weight_map_data_spi as spi_weights


class UnknownVenueError(ValueError):
    """Raised when a game_id has no registered UI adapters."""


_GUIDES: dict[str, ModuleType] = {
    "lotn_v5": lotn_guide,
    "spi": spi_guide,
}

_WEIGHT_DATA: dict[str, ModuleType] = {
    "lotn_v5": lotn_weights,
    "spi": spi_weights,
}

IMPLEMENTED_UI_GAMES = frozenset(_GUIDES.keys())


def require_venue_id(game_id: str) -> str:
    gid = str(game_id or "").strip()
    if gid not in IMPLEMENTED_UI_GAMES:
        raise UnknownVenueError(f"Unknown or unimplemented Venue: {game_id!r}")
    return gid


def resolve_guide(game_id: str) -> dict[str, Any]:
    """Return build-guide payload for a Venue. Never falls back to LotN."""
    gid = require_venue_id(game_id)
    mod = _GUIDES[gid]
    return {
        "title": mod.STRATEGY_PAGE_TITLE,
        "blurb": mod.STRATEGY_BLURB,
        "tabs": mod.STRATEGY_TABS,
        "sections": mod.strategy_sections(),
        "game_id": gid,
    }


def weight_data_for(game_id: str) -> ModuleType:
    """Return weight-map data module for a Venue. Never falls back to LotN."""
    gid = require_venue_id(game_id)
    return _WEIGHT_DATA[gid]


def is_spi_game(game_id: str) -> bool:
    return game_id == "spi"


def is_lotn_game(game_id: str) -> bool:
    return game_id == "lotn_v5"
