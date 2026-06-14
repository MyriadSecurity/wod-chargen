"""Weighted procedural XP spend loop."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Callable

from wod_chargen.core.models import LogEntry, XpLogEntry
from wod_chargen.core.rng import SeededRng
from wod_chargen.core.xp_strategy import (
    budget_efficiency_scale,
    efficiency_item_bias,
    loresheet_efficiency_bias,
    macro_deficit_boost,
    macro_for_spend_group,
    roll_category_targets,
)

MAX_ITERATIONS = 500


@dataclass
class PurchaseCandidate:
    item_id: str
    category: str
    spend_group: str
    new_level: int
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


def _pick_candidate(
    rng: SeededRng,
    candidates: list[PurchaseCandidate],
    *,
    category_targets: dict[str, float],
    spent_by_macro: dict[str, int],
    xp_spent: int,
    budget: int,
) -> tuple[PurchaseCandidate, float, float, float]:
    """Pick macro category mix, spend group, then item by bias and efficiency."""
    by_group: dict[str, list[PurchaseCandidate]] = defaultdict(list)
    for cand in candidates:
        by_group[cand.spend_group].append(cand)

    macro_strength: dict[str, float] = defaultdict(float)
    macro_group_count: dict[str, int] = defaultdict(int)
    for spend_group in sorted(by_group):
        pool = by_group[spend_group]
        macro = macro_for_spend_group(spend_group)
        macro_strength[macro] += pool[0].weight
        macro_group_count[macro] += 1

    macro_weights: dict[str, float] = {}
    for macro in sorted(macro_strength):
        total_strength = macro_strength[macro]
        avg_strength = total_strength / macro_group_count[macro]
        target = category_targets.get(macro, 0.1)
        deficit = macro_deficit_boost(
            macro,
            category_targets=category_targets,
            spent_by_macro=spent_by_macro,
            xp_spent=xp_spent,
            budget=budget,
        )
        macro_weights[macro] = target * avg_strength * deficit

    macros = sorted(macro_weights.keys())
    chosen_macro = rng.weighted_choice(macros, [macro_weights[m] for m in macros])

    eligible_groups = sorted(g for g in by_group if macro_for_spend_group(g) == chosen_macro)
    group_weights = [by_group[g][0].weight for g in eligible_groups]
    chosen_group = rng.weighted_choice(eligible_groups, group_weights)
    pool = by_group[chosen_group]
    scored: list[tuple[PurchaseCandidate, float, float, float]] = []
    for cand in pool:
        cur = cand.new_level - 1
        if cand.category == "loresheet":
            eff = loresheet_efficiency_bias(cur, cand.new_level)
        else:
            eff = efficiency_item_bias(cur, cand.new_level)
        eff *= budget_efficiency_scale(
            cand.spend_group,
            category_targets=category_targets,
            spent_by_macro=spent_by_macro,
            xp_spent=xp_spent,
        )
        item_roll = rng.uniform()
        score = cand.item_weight() * eff * item_roll
        scored.append((cand, eff, score, item_roll))
    best, eff, score, roll = max(scored, key=lambda pair: (pair[2], pair[0].item_id))
    return best, roll, score, eff


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
    category_targets = roll_category_targets(rng)
    spent_by_macro: dict[str, int] = defaultdict(int)
    xp_spent = 0

    logs.append(
        LogEntry(
            phase="xp",
            message="XP category targets",
            detail={k: round(v, 3) for k, v in category_targets.items()},
        )
    )

    while remaining > 0 and iterations < MAX_ITERATIONS:
        iterations += 1
        candidates = [c for c in enumerate_fn() if 0 < c.cost <= remaining]
        if not candidates:
            break

        best, roll, score, eff = _pick_candidate(
            rng,
            candidates,
            category_targets=category_targets,
            spent_by_macro=spent_by_macro,
            xp_spent=xp_spent,
            budget=budget,
        )
        best.apply()
        remaining -= best.cost
        xp_spent += best.cost
        spent_by_macro[macro_for_spend_group(best.spend_group)] += best.cost
        xp_log.append(
            XpLogEntry(
                item=best.item_id,
                category=best.category,
                spend_group=best.spend_group,
                new_level=best.new_level,
                cost=best.cost,
                group_weight=best.weight,
                item_bias=best.item_bias,
                clan_factor=best.clan_factor,
                efficiency_bias=eff,
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
