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


def test_spend_xp_respects_max_iterations():
    rng = SeededRng(99)

    def enumerate() -> list[PurchaseCandidate]:
        return [_candidate("cheap", 1)]

    remaining, _, _ = spend_xp(rng, MAX_ITERATIONS + 50, enumerate, source="test")
    assert remaining >= 0
