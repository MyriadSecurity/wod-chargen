"""Venue-scoped build guide content dispatcher (fail-closed)."""

from __future__ import annotations

from typing import Any

from app.venue_dispatch import UnknownVenueError, resolve_guide as _resolve_guide
from app import strategy_content_lotn as lotn

STRATEGY_TABS = lotn.STRATEGY_TABS
STRATEGY_PAGE_TITLE = lotn.STRATEGY_PAGE_TITLE
STRATEGY_BLURB = lotn.STRATEGY_BLURB


def resolve_guide(game_id: str) -> dict[str, Any]:
    """Return guide for game_id. Raises UnknownVenueError if unknown."""
    return _resolve_guide(game_id)


def strategy_sections() -> dict[str, list[dict[str, Any]]]:
    """LotN sections (back-compat for tests that omit game_id)."""
    return lotn.strategy_sections()


__all__ = [
    "STRATEGY_TABS",
    "STRATEGY_PAGE_TITLE",
    "STRATEGY_BLURB",
    "UnknownVenueError",
    "resolve_guide",
    "strategy_sections",
]
