"""VenueSystem protocol — shared surface for game-line (Venue) engines."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from wod_chargen.core.models import GenerationResult

# Package path for games/catalog.json (Venue-neutral; do not import from lotn_v5.paths).
GAMES_PKG = "wod_chargen.games"


@runtime_checkable
class VenueSystem(Protocol):
    """Minimum contract the app shell calls on a Venue engine.

    Venue-specific pickers (clan, predator, division, affinity, …) remain
    optional duck-typed methods — not every Venue implements every picker.
    """

    id: str

    @property
    def label(self) -> str: ...

    @property
    def tagline(self) -> str: ...

    def get_wizard_steps(self) -> list[str]: ...

    def get_wizard_copy(self) -> dict[str, str]: ...

    def get_venue_picker(self) -> list[dict[str, Any]]:
        """Starting XP profiles for this Venue (legacy name; prefer get_xp_profile_picker)."""
        ...

    def generate(
        self,
        seed: int,
        options: dict[str, Any],
        venue_config: dict[str, Any],
    ) -> GenerationResult: ...

    def build_sheet_model(self, result: GenerationResult, **kwargs: Any) -> Any: ...
