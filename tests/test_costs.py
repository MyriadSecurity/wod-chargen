"""XP cost table tests."""

from wod_chargen.core.costs import cost_for, lookup_cost


def test_cost_table_helpers():
    assert cost_for({"kind": "flat", "amount": 5}) == 5
    assert cost_for({"kind": "multiply", "factor": 3}, new_level=4) == 12
    table = {"attribute": {"kind": "multiply", "factor": 4}}
    assert lookup_cost(table, "attribute", new_level=2) == 8
