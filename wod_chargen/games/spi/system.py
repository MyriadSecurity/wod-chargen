"""SPI Venue system facade."""

from __future__ import annotations

from typing import Any

from wod_chargen.core.data_loader import load_json_cached
from wod_chargen.core.models import GenerationResult
from wod_chargen.games.spi.archetypes import archetype_picker
from wod_chargen.games.spi.generator import generate_character
from wod_chargen.games.spi.paths import DATA_PKG, GAMES_PKG, VENUE_PKG
from wod_chargen.games.spi.sheet_model import SpiSheetModel, build_sheet_model
from wod_chargen.venues import load_venue


class SpiSystem:
    id = "spi"

    @property
    def label(self) -> str:
        return str(self._catalog_entry().get("label", "Society of Paranormal Investigators"))

    @property
    def tagline(self) -> str:
        return str(self._catalog_entry().get("tagline", ""))

    def _catalog_entry(self) -> dict[str, Any]:
        catalog = load_json_cached(GAMES_PKG, "catalog.json")
        return dict(catalog.get(self.id, {}))

    def _wizard_ui(self) -> dict[str, Any]:
        return load_json_cached(DATA_PKG, "wizard_ui.json")

    def get_wizard_copy(self) -> dict[str, str]:
        copy = self._wizard_ui().get("copy", {})
        return {str(k): str(v) for k, v in copy.items()}

    def get_wizard_steps(self) -> list[str]:
        steps = self._wizard_ui().get("wizard_steps", [])
        return [str(s) for s in steps]

    def get_venue_picker(self) -> list[dict[str, Any]]:
        picker = load_json_cached(VENUE_PKG, "picker.json")
        ids = picker.get(self.id, [])
        out: list[dict[str, Any]] = []
        for vid in ids:
            venue = load_venue(str(vid))
            out.append(
                {
                    "id": venue["id"],
                    "label": venue.get("label", venue["id"]),
                    "requires_approval_month": venue.get("xp_method") == "mes_approval_month",
                    "requires_custom_xp": venue.get("xp_method") == "custom",
                }
            )
        return out

    def get_xp_profile_picker(self) -> list[dict[str, Any]]:
        """Alias for get_venue_picker — starting XP profiles (not Venues)."""
        return self.get_venue_picker()

    def get_division_options(self) -> list[dict[str, str]]:
        divisions = load_json_cached(DATA_PKG, "divisions.json")
        return [
            {
                "id": d["id"],
                "label": d.get("label", d["id"]),
                "description": d.get("summary", ""),
            }
            for d in divisions.values()
        ]

    def get_faction_options(self) -> list[dict[str, str]]:
        factions = load_json_cached(DATA_PKG, "factions.json")
        return [
            {
                "id": f["id"],
                "label": f.get("label", f["id"]),
                "description": f.get("summary", ""),
            }
            for f in factions.values()
        ]

    def get_archetypes(self) -> list[dict[str, str]]:
        return archetype_picker()

    def get_affinity_options(self) -> list[dict[str, str]]:
        copy = self.get_wizard_copy()
        types = load_json_cached(DATA_PKG, "affinity_types.json")
        out = [
            {
                "id": "any",
                "label": copy.get("affinity_any_label", "Any (from archetype)"),
                "description": "",
            }
        ]
        for tid, entry in types.items():
            out.append(
                {
                    "id": tid,
                    "label": entry.get("label", tid),
                    "description": "",
                }
            )
        return out

    def generate(
        self,
        seed: int,
        options: dict[str, Any],
        venue_config: dict[str, Any],
    ) -> GenerationResult:
        return generate_character(seed, options, venue_config)

    def build_sheet_model(self, result: GenerationResult, **_kwargs: Any) -> SpiSheetModel:
        return build_sheet_model(result)
