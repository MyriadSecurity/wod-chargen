"""SPI Venue system facade (scaffold; generator lands in a later phase)."""

from __future__ import annotations

from typing import Any

from wod_chargen.core.data_loader import load_json_cached
from wod_chargen.games.spi.paths import DATA_PKG, GAMES_PKG, VENUE_PKG
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
