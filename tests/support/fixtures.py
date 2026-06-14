"""Shared test helpers for character generation."""

from __future__ import annotations

from typing import Any

from wod_chargen.core.data_loader import load_json_cached
from wod_chargen.defaults import DEFAULT_VENUE_ID
from wod_chargen.games.lotn_v5.paths import VENUE_PKG

CUSTOM_XP_VENUE = "custom_xp"


def load_venue(venue_id: str = DEFAULT_VENUE_ID) -> dict[str, Any]:
    return load_json_cached(VENUE_PKG, f"{venue_id}.json")


def opts(**kwargs: Any) -> dict[str, Any]:
    base = {
        "type": "vampire",
        "clan": "brujah",
        "arch": "diplomat",
        "sub": "silver_tongue",
        "approval": "2026-06",
    }
    base.update(kwargs)
    return base


def ghoul_opts(**kwargs: Any) -> dict[str, Any]:
    base = {
        "type": "ghoul",
        "domitor_clan": "tremere",
        "arch": "shadow",
        "sub": "spy",
        "xp": "200",
    }
    base.update(kwargs)
    return base


def caitiff_opts(**kwargs: Any) -> dict[str, Any]:
    base = {
        "type": "vampire",
        "clan": "caitiff",
        "arch": "diplomat",
        "sub": "silver_tongue",
        "xp": "500",
    }
    base.update(kwargs)
    return base


def thin_blood_opts(**kwargs: Any) -> dict[str, Any]:
    base = {
        "type": "thin_blood",
        "arch": "alchemist",
        "sub": "distiller",
        "xp": "300",
    }
    base.update(kwargs)
    return base
