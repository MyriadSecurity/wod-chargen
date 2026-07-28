"""Sheet render dispatch by Venue."""

from __future__ import annotations

from typing import Any, Callable

from app.components.sheet import render_lotn_v5_sheet
from app.components.sheet_spi import render_spi_sheet
from app.venue_dispatch import UnknownVenueError, require_venue_id


def render_sheet_for_game(
    game_id: str,
    sheet_model: Any,
    *,
    on_reroll_convictions: Callable | None = None,
) -> Any:
    gid = require_venue_id(game_id)
    if gid == "spi":
        return render_spi_sheet(sheet_model)
    if gid == "lotn_v5":
        return render_lotn_v5_sheet(
            sheet_model,
            on_reroll_convictions=on_reroll_convictions,
        )
    raise UnknownVenueError(f"No sheet renderer for {game_id!r}")
