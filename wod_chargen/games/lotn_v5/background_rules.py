"""Shared background and merit/flaw interaction rules (Poor, Haven, etc.)."""

from __future__ import annotations

from typing import Any

ModifierKind = str


def _entries_for_type(entries: list[dict[str, Any]], bg_type: str) -> list[dict[str, Any]]:
    return [e for e in entries if e.get("type") == bg_type]


def _total_background_dots(entries: list[dict[str, Any]]) -> int:
    return sum(int(e.get("dots", 0)) for e in entries)


def _modifier_rating_value(mod: Any) -> int:
    if isinstance(mod, dict):
        return int(mod.get("dots", 0))
    if isinstance(mod, str):
        return 1
    return 0


def _total_modifier_dots(entries: list[dict[str, Any]], kind: ModifierKind) -> int:
    key = "advantages" if kind == "advantage" else "disadvantages"
    total = 0
    for entry in entries:
        for mod in entry.get(key, []):
            total += _modifier_rating_value(mod)
    return total


def poor_level(char: dict[str, Any]) -> int:
    return int(char.get("flaws", {}).get("poor", 0))


def no_haven_flaw_active(char: dict[str, Any]) -> bool:
    return int(char.get("flaws", {}).get("no_haven", 0)) > 0


def background_type_dots(char: dict[str, Any], bg_type: str) -> int:
    return _total_background_dots(_entries_for_type(char.get("backgrounds", []), bg_type))


def total_haven_advantage_dots(char: dict[str, Any]) -> int:
    return _total_modifier_dots(_entries_for_type(char.get("backgrounds", []), "haven"), "advantage")


def max_haven_connection_dots_allowed(char: dict[str, Any]) -> int | None:
    if no_haven_flaw_active(char) or poor_level(char) >= 3:
        return 0
    if poor_level(char) >= 1:
        return 1
    return None


def max_haven_advantage_dots_allowed(char: dict[str, Any]) -> int | None:
    if no_haven_flaw_active(char) or poor_level(char) >= 2:
        return 0
    if poor_level(char) >= 1:
        return 1
    return None


def background_connection_blocked(char: dict[str, Any], bg_type: str) -> bool:
    if bg_type == "resources" and poor_level(char) > 0:
        return True
    if bg_type == "haven" and (no_haven_flaw_active(char) or poor_level(char) >= 3):
        return True
    return False


def poor_rating_eligible(char: dict[str, Any], new_rating: int) -> bool:
    if background_type_dots(char, "resources") > 0:
        return False
    haven_dots = background_type_dots(char, "haven")
    haven_adv = total_haven_advantage_dots(char)
    if new_rating >= 3 and haven_dots > 0:
        return False
    if new_rating >= 1 and haven_dots > 1:
        return False
    if new_rating >= 2 and haven_adv > 0:
        return False
    if new_rating >= 1 and haven_adv > 1:
        return False
    return True


def haven_advantage_blocked(char: dict[str, Any]) -> bool:
    cap = max_haven_advantage_dots_allowed(char)
    if cap is None:
        return False
    return total_haven_advantage_dots(char) >= cap
