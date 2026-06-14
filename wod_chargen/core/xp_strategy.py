"""XP spend strategy — efficient dot buys and category budget mix."""

from __future__ import annotations

from wod_chargen.core.rng import SeededRng

# Macro buckets for budget tracking (values vary per character via roll_category_targets).
BASE_CATEGORY_TARGETS = {
    "disciplines": 0.34,
    "attributes": 0.20,
    "skills": 0.20,
    "backgrounds": 0.12,
    "merits_flaws": 0.14,
}

SPEND_GROUP_MACRO = {
    "physical_attrs": "attributes",
    "social_attrs": "attributes",
    "mental_attrs": "attributes",
    "skills": "skills",
    "in_clan_disciplines": "disciplines",
    "ghoul_powers": "disciplines",
    "thin_blood_formulas": "disciplines",
    "background_connections": "backgrounds",
    "background_modifiers": "backgrounds",
    "background_disadvantages": "backgrounds",
    "backgrounds": "backgrounds",
    "merits": "merits_flaws",
    "loresheets": "merits_flaws",
    "blood_potency": "merits_flaws",
}

DEFICIT_SCALE = 4.5
MIN_GROUP_BOOST = 0.25
MAX_GROUP_BOOST = 4.0


def macro_for_spend_group(spend_group: str) -> str:
    return SPEND_GROUP_MACRO.get(spend_group, "merits_flaws")


def roll_category_targets(rng: SeededRng) -> dict[str, float]:
    """Jitter base targets so each character has a slightly different XP mix."""
    jittered = {
        key: value * (0.82 + 0.36 * rng.uniform()) for key, value in BASE_CATEGORY_TARGETS.items()
    }
    total = sum(jittered.values())
    return {key: value / total for key, value in jittered.items()}


def efficiency_item_bias(current_level: int, new_level: int) -> float:
    """Favor finishing 5-dots and shallow picks on new traits."""
    if current_level == 4 and new_level == 5:
        return 5.0
    if current_level == 0:
        if new_level == 1:
            return 2.5
        if new_level == 2:
            return 1.6
        return 0.1
    if current_level == 1 and new_level == 2:
        return 1.4
    if current_level <= 2 and new_level == 3:
        return 0.35
    if current_level == 3 and new_level == 4:
        return 1.1
    return 0.75


def loresheet_efficiency_bias(current_level: int, new_level: int) -> float:
    """Favor taking a loresheet and completing 2–3 dots."""
    if current_level == 0 and new_level == 1:
        return 3.2
    if current_level == 1 and new_level == 2:
        return 3.6
    if current_level == 2 and new_level == 3:
        return 2.8
    return 1.0


def budget_efficiency_scale(
    spend_group: str,
    *,
    category_targets: dict[str, float],
    spent_by_macro: dict[str, int],
    xp_spent: int,
) -> float:
    """Dampen efficient picks in categories already above their target spend share."""
    if xp_spent <= 0:
        return 1.0
    macro = macro_for_spend_group(spend_group)
    target = category_targets.get(macro, 0.1)
    actual = spent_by_macro.get(macro, 0) / xp_spent
    if actual > target * 1.1:
        return max(0.15, 1.0 - (actual - target) * 5.0)
    if actual < target * 0.9:
        return min(2.0, 1.0 + (target - actual) * 3.0)
    return 1.0


def creation_pick_weight(bias: float, current: int, max_rating: int, pool_dots: int) -> float:
    """Bias free creation dots toward 4s (setup for cheap 5th) and shallow spreads."""
    room = max_rating - current
    if room <= 0:
        return 0.0
    weight = bias * room
    if pool_dots == 4:
        weight *= 2.0
    elif pool_dots == 3:
        weight *= 1.3
    elif pool_dots <= 2:
        weight *= 1.15
    return weight


def macro_deficit_boost(
    macro: str,
    *,
    category_targets: dict[str, float],
    spent_by_macro: dict[str, int],
    xp_spent: int,
    budget: int,
) -> float:
    if budget <= 0 or xp_spent <= 0:
        return 1.0
    target = category_targets.get(macro, 0.0)
    expected = target * xp_spent
    actual = spent_by_macro.get(macro, 0)
    deficit = (expected - actual) / budget
    boost = 1.0 + DEFICIT_SCALE * deficit
    return max(MIN_GROUP_BOOST, min(MAX_GROUP_BOOST, boost))


def budget_deficit_boost(
    spend_group: str,
    *,
    category_targets: dict[str, float],
    spent_by_macro: dict[str, int],
    xp_spent: int,
    budget: int,
) -> float:
    """Raise weight for macro categories that are behind their target spend share."""
    return macro_deficit_boost(
        macro_for_spend_group(spend_group),
        category_targets=category_targets,
        spent_by_macro=spent_by_macro,
        xp_spent=xp_spent,
        budget=budget,
    )
