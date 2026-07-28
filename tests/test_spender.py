"""XP spend loop tests."""

from wod_chargen.core.models import LogEntry
from wod_chargen.core.rng import SeededRng
from wod_chargen.core.spender import MAX_ITERATIONS, PurchaseCandidate, spend_xp


def _candidate(item_id: str, cost: int) -> PurchaseCandidate:
    state = {"value": 0}

    def apply() -> None:
        state["value"] += 1

    return PurchaseCandidate(
        item_id=item_id,
        category="skill",
        spend_group="skills",
        new_level=1,
        cost=cost,
        weight=1.0,
        item_bias=1.0,
        clan_factor=1.0,
        source="test",
        apply=apply,
    )


def test_spend_xp_stops_at_budget():
    rng = SeededRng(1)
    calls = {"n": 0}

    def enumerate() -> list[PurchaseCandidate]:
        calls["n"] += 1
        return [_candidate("brawl", 5)]

    remaining, xp_log, logs = spend_xp(rng, 12, enumerate, source="test")
    assert remaining == 2
    assert sum(e.cost for e in xp_log) == 10
    assert isinstance(logs[0], LogEntry)


def test_package_merit_uses_opening_efficiency():
    """Fixed-rating multi-dot buys should not inherit jump / finish-5 heuristics."""
    from wod_chargen.core.xp_strategy import efficiency_item_bias

    def enumerate() -> list[PurchaseCandidate]:
        return [
            PurchaseCandidate(
                item_id="fixed_three",
                category="merit",
                spend_group="merits",
                new_level=3,
                cost=3,
                weight=1.0,
                item_bias=1.0,
                clan_factor=1.0,
                source="test",
                apply=lambda: None,
                current_level=0,
                package=True,
            ),
            PurchaseCandidate(
                item_id="range_one",
                category="merit",
                spend_group="merits",
                new_level=1,
                cost=1,
                weight=1.0,
                item_bias=1.0,
                clan_factor=1.0,
                source="test",
                apply=lambda: None,
                current_level=0,
            ),
        ]

    # Without package=True, cur would be inferred as 2 and efficiency_item_bias(2,3)=0.35
    assert efficiency_item_bias(2, 3) == 0.35
    assert efficiency_item_bias(0, 1) == 2.5

    saw_package = False
    for seed in range(30):
        remaining, xp_log, _ = spend_xp(SeededRng(seed), 3, enumerate, source="test")
        if any(e.item == "fixed_three" for e in xp_log):
            saw_package = True
            assert next(e.cost for e in xp_log if e.item == "fixed_three") == 3
            assert remaining == 0
            break
    assert saw_package
