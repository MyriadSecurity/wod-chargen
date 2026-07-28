"""Signature skill selection for SPI creation floor and XP efficiency."""

from __future__ import annotations

from typing import Any

from wod_chargen.core.models import LogEntry
from wod_chargen.core.rng import SeededRng

# Minimum merged skill bias to count as signature.
SIGNATURE_SKILL_BIAS_THRESHOLD = 1.35
# Top-N skills considered signature when several clear the threshold.
SIGNATURE_SKILL_MAX_CANDIDATES = 3
# Creation floor for one chosen signature skill.
SIGNATURE_SKILL_CREATION_FLOOR = 3


def signature_skill_candidates(
    biases: dict[str, float],
    items: list[str],
    *,
    threshold: float = SIGNATURE_SKILL_BIAS_THRESHOLD,
    max_candidates: int = SIGNATURE_SKILL_MAX_CANDIDATES,
) -> list[str]:
    """Top bias skills above threshold; else top overall."""
    pool = list(items)
    ranked = sorted(pool, key=lambda item: (-float(biases.get(item, 1.0)), item))
    qualified = [item for item in ranked if float(biases.get(item, 1.0)) >= threshold]
    if qualified:
        return qualified[:max_candidates]
    return ranked[: max(1, max_candidates)]


def _skill_category(skill: str, categories: dict[str, list[str]]) -> str | None:
    for cid, traits in categories.items():
        if skill in traits:
            return cid
    return None


def ensure_signature_skill_floor(
    rng: SeededRng,
    ratings: dict[str, int],
    biases: dict[str, float],
    categories: dict[str, list[str]],
    log: list[LogEntry],
    *,
    floor: int = SIGNATURE_SKILL_CREATION_FLOOR,
    max_rating: int = 5,
    threshold: float = SIGNATURE_SKILL_BIAS_THRESHOLD,
) -> frozenset[str]:
    """Raise one signature skill to ``floor`` by stealing dots in its category.

    Returns the full signature candidate set (for XP ``is_signature`` marking).
    """
    items = [s for traits in categories.values() for s in traits]
    candidates = signature_skill_candidates(
        biases, items, threshold=threshold, max_candidates=SIGNATURE_SKILL_MAX_CANDIDATES
    )
    if not candidates:
        return frozenset()

    # Prefer signatures still below the floor, weighted by bias.
    below = [c for c in candidates if int(ratings.get(c, 0)) < floor]
    pick_pool = below or list(candidates)
    weights = [max(0.01, float(biases.get(c, 1.0))) for c in pick_pool]
    pick = str(rng.weighted_choice(pick_pool, weights))

    cur = int(ratings.get(pick, 0))
    need = min(floor, max_rating) - cur
    if need <= 0:
        return frozenset(candidates)

    cat = _skill_category(pick, categories)
    if cat is None:
        return frozenset(candidates)

    donors = [
        s
        for s in categories[cat]
        if s != pick and int(ratings.get(s, 0)) > 0
    ]
    # Steal from lowest-biased first; prefer non-signature donors.
    sig_set = set(candidates)
    donors.sort(
        key=lambda s: (
            0 if s not in sig_set else 1,
            float(biases.get(s, 1.0)),
            -int(ratings.get(s, 0)),
            s,
        )
    )

    raised = 0
    while raised < need and donors:
        donor = donors[0]
        if int(ratings[donor]) <= 0:
            donors.pop(0)
            continue
        ratings[donor] -= 1
        ratings[pick] = int(ratings.get(pick, 0)) + 1
        raised += 1
        log.append(
            LogEntry(
                phase="creation_skills",
                message=(
                    f"Signature floor: {_title(pick)} +1 → {ratings[pick]} "
                    f"(from {_title(donor)})"
                ),
                detail={
                    "trait": pick,
                    "donor": donor,
                    "signature_floor": True,
                    "bias": float(biases.get(pick, 1.0)),
                },
            )
        )
        if int(ratings[donor]) <= 0:
            donors.pop(0)

    # If still short (category too empty), grant remaining dots without donors.
    while int(ratings.get(pick, 0)) < min(floor, max_rating):
        ratings[pick] = int(ratings.get(pick, 0)) + 1
        log.append(
            LogEntry(
                phase="creation_skills",
                message=f"Signature floor: {_title(pick)} +1 → {ratings[pick]}",
                detail={
                    "trait": pick,
                    "signature_floor": True,
                    "granted": True,
                    "bias": float(biases.get(pick, 1.0)),
                },
            )
        )

    return frozenset(candidates)


def _title(key: str) -> str:
    return key.replace("_", " ").title()
