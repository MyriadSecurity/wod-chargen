"""Humanity convictions — pick from master list using an independent seed.

Conviction text sourced from the r/vtm community master list:
https://www.reddit.com/r/vtm/comments/1ecdulq/convictions_master_list/
"""

from __future__ import annotations

from typing import Any

from wod_chargen.core.data_loader import load_json_cached
from wod_chargen.core.rng import SeededRng

from wod_chargen.games.lotn_v5.paths import DATA_PKG as DATA


def load_convictions_catalog() -> dict[str, Any]:
    return load_json_cached(DATA, "convictions.json")


def pick_convictions(seed: int, *, count: int | None = None) -> list[dict[str, str]]:
    """Return `count` distinct convictions chosen deterministically from `seed`."""
    catalog = load_convictions_catalog()
    pool = list(catalog["convictions"])
    pick_count = int(count if count is not None else catalog.get("pick_count", 3))
    if pick_count <= 0:
        return []
    if pick_count >= len(pool):
        return [{"id": c["id"], "text": c["text"]} for c in pool]

    rng = SeededRng(seed)
    shuffled = rng.shuffle(pool)
    return [{"id": c["id"], "text": c["text"]} for c in shuffled[:pick_count]]
