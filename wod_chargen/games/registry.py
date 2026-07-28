"""Game system registry."""

from __future__ import annotations

from typing import Any

from wod_chargen.core.data_loader import load_json_cached
from wod_chargen.games.lotn_v5.system import LotnV5System
from wod_chargen.games.protocol import GAMES_PKG, VenueSystem
from wod_chargen.games.spi.system import SpiSystem

_SYSTEMS: dict[str, VenueSystem] = {
    "lotn_v5": LotnV5System(),
    "spi": SpiSystem(),
}


def load_game_catalog() -> dict[str, Any]:
    return load_json_cached(GAMES_PKG, "catalog.json")


def get_game(game_id: str) -> VenueSystem:
    if game_id not in _SYSTEMS:
        raise ValueError(f"Unknown game: {game_id}")
    return _SYSTEMS[game_id]


def registered_game_ids() -> list[str]:
    return list(_SYSTEMS.keys())
