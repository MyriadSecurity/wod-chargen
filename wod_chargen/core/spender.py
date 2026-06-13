"""Weighted procedural XP spend loop."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Callable

from wod_chargen.core.models import LogEntry, XpLogEntry
from wod_chargen.core.rng import SeededRng

MAX_ITERATIONS = 500


@dataclass
class PurchaseCandidate:
    item_id: str
    category: str
    spend_group: str
    cost: int
    weight: float
    item_bias: float
    clan_factor: float
    source: str
    apply: Callable[[], None]

    @property
    def effective_weight(self) -> float:
        return self.weight * self.item_bias * self.clan_factor

    def item_weight(self) -> float:
        return self.item_bias * self.clan_factor


def _pick_candidate(rng: SeededRng, candidates: list[PurchaseCandidate]) -> tuple[PurchaseCandidate, float, float]:
    """Pick spend group by archetype weight, then item within that group."""
    by_group: dict[str, list[PurchaseCandidate]] = defaultdict(list)
    group_weights: dict[str, float] = {}
    for cand in candidates:
        by_group[cand.spend_group].append(cand)
        group_weights[cand.spend_group] = cand.weight

    groups = list(by_group.keys())
    chosen_group = rng.weighted_choice(groups, [group_weights[g] for g in groups])
    pool = by_group[chosen_group]
    roll = rng.uniform()
    scored = [(cand, cand.item_weight() * roll) for cand in pool]
    best, score = max(scored, key=lambda pair: pair[1])
    return best, roll, score


def spend_xp(
    rng: SeededRng,
    budget: int,
    enumerate_fn: Callable[[], list[PurchaseCandidate]],
    *,
    source: str = "archetype",
) -> tuple[int, list[XpLogEntry], list[LogEntry]]:
    remaining = budget
    xp_log: list[XpLogEntry] = []
    logs: list[LogEntry] = []
    iterations = 0

    while remaining > 0 and iterations < MAX_ITERATIONS:
        iterations += 1
        candidates = [c for c in enumerate_fn() if c.cost <= remaining and c.cost > 0]
        if not candidates:
            break

        best, roll, score = _pick_candidate(rng, candidates)
        best.apply()
        remaining -= best.cost
        xp_log.append(
            XpLogEntry(
                item=best.item_id,
                category=best.category,
                cost=best.cost,
                weight=best.effective_weight,
                roll=roll,
                score=score,
                source=best.source or source,
            )
        )

    if iterations >= MAX_ITERATIONS:
        logs.append(
            LogEntry(
                phase="xp",
                message="Spend loop stopped at iteration cap",
                detail={"iterations": iterations, "remaining": remaining},
            )
        )

    return remaining, xp_log, logs
