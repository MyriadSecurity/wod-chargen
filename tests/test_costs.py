"""XP cost table tests."""

from wod_chargen.core.costs import cost_for, lookup_cost


def test_flat_cost():
    assert cost_for({"kind": "flat", "amount": 5}) == 5


def test_multiply_cost():
    assert cost_for({"kind": "multiply", "factor": 3}, new_level=4) == 12


def test_lookup_attribute_tier():
    table = {"attribute": {"kind": "multiply", "factor": 4}}
    assert lookup_cost(table, "attribute", new_level=2) == 8
