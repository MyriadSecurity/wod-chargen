"""XP spend strategy tests."""

from __future__ import annotations

from collections import defaultdict

import pytest

from wod_chargen.core.rng import SeededRng
from wod_chargen.core.xp_strategy import (
    BASE_CATEGORY_TARGETS,
    efficiency_item_bias,
    macro_for_spend_group,
    roll_category_targets,
)
from wod_chargen.games.lotn_v5.generator import generate_character


def _venue():
    from wod_chargen.core.data_loader import load_json_cached

    return load_json_cached("wod_chargen.venues", "mes_end_to_dawn.json")


def _opts(**kwargs):
    base = {
        "type": "vampire",
        "clan": "brujah",
        "arch": "diplomat",
        "sub": "silver_tongue",
        "approval": "2026-06",
    }
    base.update(kwargs)
    return base


def test_efficiency_item_bias_favors_finish_and_shallow_new():
    assert efficiency_item_bias(4, 5) > efficiency_item_bias(3, 4)
    assert efficiency_item_bias(0, 1) > efficiency_item_bias(0, 3)
    assert efficiency_item_bias(0, 3) < efficiency_item_bias(1, 2)


def test_roll_category_targets_vary_and_sum_to_one():
    rng = SeededRng(99)
    a = roll_category_targets(rng)
    b = roll_category_targets(rng)
    assert abs(sum(a.values()) - 1.0) < 1e-9
    assert a != b
    for key in BASE_CATEGORY_TARGETS:
        assert key in a


def test_xp_log_records_category_targets():
    result = generate_character(77, _opts(), _venue())
    target_logs = [e for e in result.creation_log if e.message == "XP category targets"]
    assert len(target_logs) == 1
    detail = target_logs[0].detail
    assert abs(sum(detail.values()) - 1.0) < 0.01


def test_xp_spend_rough_category_mix_with_variance():
    """Targets guide mix; archetype and efficiency allow wide per-character variance."""
    per_seed_mixes: list[dict[str, float]] = []
    for seed in range(40):
        result = generate_character(seed, _opts(), _venue())
        if result.xp_spent < 50:
            continue
        spent = defaultdict(int)
        for entry in result.xp_log:
            spent[macro_for_spend_group(entry.spend_group)] += entry.cost
        per_seed_mixes.append({k: v / result.xp_spent for k, v in spent.items()})

    assert len(per_seed_mixes) >= 30

    macros_seen = {macro for mix in per_seed_mixes for macro in mix}
    assert {"disciplines", "attributes", "skills"}.issubset(macros_seen)
    assert macros_seen & {"backgrounds", "merits_flaws"}

    avg = {
        macro: sum(mix.get(macro, 0) for mix in per_seed_mixes) / len(per_seed_mixes)
        for macro in ("disciplines", "attributes", "skills", "backgrounds", "merits_flaws")
    }
    assert avg["disciplines"] > avg["backgrounds"]
    assert avg["disciplines"] > 0.20
    assert avg["backgrounds"] + avg["merits_flaws"] < 0.25


def test_xp_prefers_dot_five_and_shallow_buys():
    fifth_dots = 0
    shallow = 0
    deep_third = 0
    for seed in range(80):
        result = generate_character(seed, _opts(), _venue())
        for entry in result.xp_log:
            cur = entry.new_level - 1
            if entry.new_level == 5:
                fifth_dots += 1
            if cur == 0 and entry.new_level <= 2:
                shallow += 1
            if cur == 2 and entry.new_level == 3:
                deep_third += 1
    assert fifth_dots >= 10
    assert shallow > deep_third
