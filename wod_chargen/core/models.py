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
    cost: int
    weight: float
    roll: float
    score: float
    source: str


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
                    "cost": e.cost,
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
