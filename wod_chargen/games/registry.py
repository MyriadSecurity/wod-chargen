"""Game system registry."""

from __future__ import annotations

from typing import Any

from wod_chargen.core.data_loader import load_json_cached
from wod_chargen.games.lotn_v5.paths import GAMES_PKG
from wod_chargen.games.lotn_v5.system import LotnV5System

_SYSTEMS = {
    "lotn_v5": LotnV5System(),
}


def load_game_catalog() -> dict[str, Any]:
    return load_json_cached(GAMES_PKG, "catalog.json")


def get_game(game_id: str) -> LotnV5System:
    if game_id not in _SYSTEMS:
        raise ValueError(f"Unknown game: {game_id}")
    return _SYSTEMS[game_id]
