"""Clan symbol assets from the VTM wiki."""

from __future__ import annotations

import json
from pathlib import Path

from wod_chargen.games.lotn_v5.clan_symbols import clan_symbol_path

ROOT = Path(__file__).resolve().parents[1]
CLANS_DIR = ROOT / "static" / "img" / "clans"


def test_clan_symbol_paths_resolve_to_existing_files():
    manifest = json.loads((CLANS_DIR / "manifest.json").read_text(encoding="utf-8"))
    for clan_id, rel in manifest.items():
        assert clan_symbol_path(clan_id) == rel
        assert (ROOT / rel).is_file()
        assert (ROOT / rel).read_bytes()[:4] == b"\x89PNG"

    thin = clan_symbol_path("thin_blood")
    assert thin.endswith(".svg")
    assert (ROOT / thin).is_file()
