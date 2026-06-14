"""Display formatting helpers for wizard UI."""

from __future__ import annotations

from typing import Any


def titleize_id(s: str) -> str:
    return s.replace("_", " ").title()


def format_disciplines(entry: dict[str, Any]) -> str:
    if entry.get("discipline_note"):
        return entry["discipline_note"]
    discipline_ids = entry.get("disciplines", [])
    if not discipline_ids:
        return "No in-clan disciplines"
    return " · ".join(titleize_id(d) for d in discipline_ids)
