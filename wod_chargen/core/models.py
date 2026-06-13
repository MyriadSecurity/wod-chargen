"""Shared dataclasses for generation results."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class LogEntry:
    phase: str
    message: str
    detail: dict[str, Any] = field(default_factory=dict)


@dataclass
class XpLogEntry:
    item: str
    category: str
    spend_group: str
    new_level: int
    cost: int
    group_weight: float
    item_bias: float
    clan_factor: float
    efficiency_bias: float
    roll: float
    score: float
    source: str

    @property
    def weight(self) -> float:
        """Effective pick weight (group × item bias × clan factor)."""
        return self.group_weight * self.item_bias * self.clan_factor


@dataclass
class GenerationResult:
    engine_version: str
    schema: str
    game_id: str
    venue_id: str
    seed: int
    options: dict[str, Any]
    character: dict[str, Any]
    creation_log: list[LogEntry]
    xp_log: list[XpLogEntry]
    xp_budget: int
    xp_spent: int
    xp_remaining: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "engine_version": self.engine_version,
            "schema": self.schema,
            "game_id": self.game_id,
            "venue_id": self.venue_id,
            "seed": self.seed,
            "options": self.options,
            "character": self.character,
            "creation_log": [
                {"phase": e.phase, "message": e.message, "detail": e.detail} for e in self.creation_log
            ],
            "xp_log": [
                {
                    "item": e.item,
                    "category": e.category,
                    "spend_group": e.spend_group,
                    "new_level": e.new_level,
                    "cost": e.cost,
                    "group_weight": e.group_weight,
                    "item_bias": e.item_bias,
                    "clan_factor": e.clan_factor,
                    "efficiency_bias": e.efficiency_bias,
                    "weight": e.weight,
                    "roll": e.roll,
                    "score": e.score,
                    "source": e.source,
                }
                for e in self.xp_log
            ],
            "xp_budget": self.xp_budget,
            "xp_spent": self.xp_spent,
            "xp_remaining": self.xp_remaining,
        }
