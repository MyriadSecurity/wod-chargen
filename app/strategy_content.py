"""Venue-scoped build guide content dispatcher."""

from __future__ import annotations

from typing import Any

from app import strategy_content_lotn as lotn
from app import strategy_content_spi as spi

STRATEGY_TABS = lotn.STRATEGY_TABS


def resolve_guide(game_id: str) -> dict[str, Any]:
    if game_id == "spi":
        return {
            "title": spi.STRATEGY_PAGE_TITLE,
            "blurb": spi.STRATEGY_BLURB,
            "tabs": spi.STRATEGY_TABS,
            "sections": spi.strategy_sections(),
        }
    return {
        "title": lotn.STRATEGY_PAGE_TITLE,
        "blurb": lotn.STRATEGY_BLURB,
        "tabs": lotn.STRATEGY_TABS,
        "sections": lotn.strategy_sections(),
    }


# Back-compat for tests that import LotN symbols from this module.
STRATEGY_PAGE_TITLE = lotn.STRATEGY_PAGE_TITLE
STRATEGY_BLURB = lotn.STRATEGY_BLURB


def strategy_sections() -> dict[str, list[dict[str, Any]]]:
    return lotn.strategy_sections()
