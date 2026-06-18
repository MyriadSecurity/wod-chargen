"""Signature skill selection — merged profile bias for creation reserve and XP pushes."""

from __future__ import annotations

from typing import Any

from wod_chargen.core.models import LogEntry
from wod_chargen.core.rng import SeededRng
from wod_chargen.core.xp_strategy import creation_pick_weight
from wod_chargen.games.lotn_v5.trait_biases import resolve_trait_bias

# Minimum merged bias (arch + sub + clan + predator tags, etc.) to count as signature.
SIGNATURE_SKILL_BIAS_THRESHOLD = 1.35
# Top-N skills considered signature when several clear the threshold.
SIGNATURE_SKILL_MAX_CANDIDATES = 3


def skill_biases(profile: Any, items: list[str]) -> dict[str, float]:
    return {item: resolve_trait_bias(profile, item, "skills") for item in items}


def signature_skill_candidates(
    profile: Any,
    items: list[str],
    *,
    threshold: float = SIGNATURE_SKILL_BIAS_THRESHOLD,
    max_candidates: int = SIGNATURE_SKILL_MAX_CANDIDATES,
    ratings: dict[str, int] | None = None,
    unused_only: bool = False,
) -> list[str]:
    """Top merged-bias skills above threshold; else top unused overall."""
    ratings = ratings or {}
    blocked = {item for item, rating in ratings.items() if unused_only and rating > 0}
    pool = [item for item in items if item not in blocked]
    biases = skill_biases(profile, pool)
    ranked = sorted(pool, key=lambda item: (-biases[item], item))
    qualified = [item for item in ranked if biases[item] >= threshold]
    if qualified:
        return qualified[:max_candidates]
    return ranked[: max(1, max_candidates)]


def assign_reserved_signature_skill(
    rng: SeededRng,
    profile: Any,
    items: list[str],
    target: dict[str, int],
    log: list[LogEntry],
    pool: dict[int, int],
    *,
    max_rating: int,
    threshold: float,
) -> None:
    """Hold one creation @3 slot for a signature skill before the general skill pass."""
    if pool.get(3, 0) <= 0:
        return
    candidates = [
        item
        for item in signature_skill_candidates(
            profile, items, threshold=threshold, ratings=target, unused_only=True
        )
        if target.get(item, 0) == 0 and 3 <= max_rating
    ]
    if not candidates:
        return
    biases = skill_biases(profile, candidates)
    if len(candidates) == 1:
        pick = candidates[0]
    else:
        weights = [
            creation_pick_weight(biases[item], 0, max_rating, 3) for item in candidates
        ]
        pick = rng.weighted_choice(candidates, weights)
    target[pick] = 3
    log.append(
        LogEntry(
            phase="base",
            message=f"Skill {pick} +3 → 3 (signature reserve)",
            detail={
                "pool_rating": 3,
                "rating": 3,
                "previous": 0,
                "signature_reserve": True,
                "bias": biases[pick],
            },
        )
    )
    pool[3] -= 1
