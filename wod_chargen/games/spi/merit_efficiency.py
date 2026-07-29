"""SPI-only merit XP efficiency (deepen owned merits, especially CoD mundanes)."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from wod_chargen.core.data_loader import load_json_cached
from wod_chargen.core.xp_strategy import efficiency_item_bias
from wod_chargen.games.spi.paths import DATA_PKG


@lru_cache(maxsize=1)
def _priors_payload() -> dict[str, Any]:
    return load_json_cached(DATA_PKG, "merit_priors.json")


def clear_merit_priors_cache() -> None:
    _priors_payload.cache_clear()


def deepen_merit_ids() -> frozenset[str]:
    return frozenset(_priors_payload().get("deepen_ids") or [])


def spi_merit_efficiency(merit_id: str, current_level: int, new_level: int) -> float:
    """Favor buying up owned merits; ``deepen_ids`` get a stronger curve.

    Soft-damps brand-new 0→1 opens so XP prefers deepening what creation already
    granted, especially Status / Resources-class infrastructure.
    """
    base = efficiency_item_bias(current_level, new_level)
    priority = merit_id in deepen_merit_ids()

    if current_level == 0 and new_level == 1:
        # Slightly less hungry for brand-new 1-dots than the global 2.5 opener.
        return 2.15 if priority else 1.85

    if priority:
        if current_level == 1 and new_level == 2:
            return max(base, 2.45)
        if current_level == 2 and new_level == 3:
            return max(base, 2.05)
        if current_level == 3 and new_level == 4:
            return max(base, 1.85)
        if current_level == 4 and new_level == 5:
            return max(base, 5.0)
        return base

    # Mild buy-up for other scalable merits (undo the harsh 2→3 cliff a bit).
    if current_level == 1 and new_level == 2:
        return max(base, 1.75)
    if current_level == 2 and new_level == 3:
        return max(base, 0.95)
    if current_level == 3 and new_level == 4:
        return max(base, 1.25)
    return base
