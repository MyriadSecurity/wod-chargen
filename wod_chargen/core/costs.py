"""XP cost calculation from typed cost table entries."""

from __future__ import annotations

from typing import Any


def cost_for(entry: dict[str, Any], new_level: int = 1, *, current_level: int = 0) -> int:
    kind = entry.get("kind", "flat")
    if kind == "multiply":
        return new_level * int(entry["factor"])
    if kind == "flat":
        return int(entry.get("amount", entry.get("per_dot", 0)))
    if kind == "per_dot":
        return int(entry["per_dot"])
    raise ValueError(f"Unknown cost kind: {kind}")


def lookup_cost(cost_table: dict[str, Any], category: str, **kwargs: Any) -> int:
    entry = cost_table.get(category)
    if entry is None:
        raise KeyError(f"Unknown cost category: {category}")
    return cost_for(entry, **kwargs)
