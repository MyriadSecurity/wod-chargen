"""Clan symbol asset paths (official VTM wiki PNGs, inverted for dark UI)."""

from __future__ import annotations

# Re-fetch: uv run python scripts/fetch_clan_symbols_wiki.py


def clan_symbol_path(clan_id: str) -> str:
    return f"static/img/clans/{clan_id}.png"
