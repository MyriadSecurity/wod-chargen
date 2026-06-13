"""LoTN V5 character generation."""

from __future__ import annotations

from typing import Any

from wod_chargen.core.data_loader import load_json_cached
from wod_chargen.core.models import GenerationResult
from wod_chargen.games.lotn_v5.archetypes import archetypes_for_type
from wod_chargen.games.lotn_v5.generator import generate_character

DATA_PKG = "wod_chargen.games.lotn_v5.data"
GAMES_PKG = "wod_chargen.games"
VENUE_PKG = "wod_chargen.venues"


class LotnV5System:
    id = "lotn_v5"

    @property
    def label(self) -> str:
        return self._catalog()["label"]

    @property
    def tagline(self) -> str:
        return self._catalog()["tagline"]

    def _catalog(self) -> dict[str, Any]:
        return load_json_cached(GAMES_PKG, "catalog.json")[self.id]

    def _wizard_ui(self) -> dict[str, Any]:
        return load_json_cached(DATA_PKG, "wizard_ui.json")

    def get_wizard_copy(self) -> dict[str, str]:
        return dict(self._wizard_ui().get("copy", {}))

    def generate(self, seed: int, options: dict[str, Any], venue_config: dict[str, Any]) -> GenerationResult:
        return generate_character(seed, options, venue_config)

    def get_wizard_steps(self) -> list[str]:
        return list(self._wizard_ui()["wizard_steps"])

    def get_archetypes(self, character_type: str = "vampire") -> list[dict[str, Any]]:
        return [
            {
                "id": p.id,
                "label": p.label,
                "description": p.description,
                "sub_archetypes": [
                    {
                        "id": s.id,
                        "label": s.label,
                        "description": s.description,
                    }
                    for s in p.sub_archetypes
                ],
            }
            for p in archetypes_for_type(character_type)
        ]

    def _lineage_entry(self, entry_id: str, raw: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": entry_id,
            "label": raw["label"],
            "description": raw.get("description", ""),
            "disciplines": raw.get("disciplines", []),
            "discipline_note": raw.get("discipline_note", ""),
            "symbol": raw.get("symbol", f"static/img/clans/{entry_id}.svg"),
            "kind": raw.get("kind", "clan"),
        }

    def get_faction_picker_title(self, role: str) -> str:
        picker = load_json_cached(DATA_PKG, "faction_picker.json")
        return picker[role]["title"]

    def get_faction_options(self, role: str) -> list[dict[str, Any]]:
        picker = load_json_cached(DATA_PKG, "faction_picker.json")
        clans = load_json_cached(DATA_PKG, "clans.json")
        role_cfg = picker[role]
        exclude = set(role_cfg.get("exclude_kinds", []))
        options: list[dict[str, Any]] = []
        for entry_id in role_cfg["order"]:
            raw = clans[entry_id]
            entry = self._lineage_entry(entry_id, raw)
            if entry["kind"] in exclude:
                continue
            options.append(entry)
        return options

    def get_character_type_picker(self) -> list[dict[str, Any]]:
        picker_ids = self._wizard_ui()["character_type_picker"]
        types = load_json_cached(DATA_PKG, "character_types.json")
        return [{"id": tid, "label": types[tid]["label"]} for tid in picker_ids]

    def get_venue_picker(self) -> list[dict[str, Any]]:
        from wod_chargen.venues import load_venue

        venue_ids = load_json_cached(VENUE_PKG, "picker.json")[self.id]
        return [
            {
                "id": vid,
                "label": load_venue(vid)["label"],
                "requires_approval_month": vid == self._wizard_ui()["mes_approval_venue"],
            }
            for vid in venue_ids
        ]

    def get_character_types(self) -> list[dict[str, Any]]:
        types = load_json_cached(DATA_PKG, "character_types.json")
        return [{"id": k, **v} for k, v in types.items()]

    def type_uses_predator(self, character_type: str) -> bool:
        types = load_json_cached(DATA_PKG, "character_types.json")
        return bool(types.get(character_type, {}).get("predator"))

    def get_predator_picker(self) -> list[dict[str, Any]]:
        data = load_json_cached(DATA_PKG, "predator_types.json")
        out: list[dict[str, Any]] = []
        for t in data["types"]:
            entry: dict[str, Any] = {"id": t["id"], "label": t["label"]}
            for key in ("summary", "feeding_pool", "benefits", "drawbacks", "restrictions"):
                if t.get(key):
                    entry[key] = t[key]
            out.append(entry)
        return out
