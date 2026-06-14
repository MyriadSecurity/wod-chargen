"""MES XP chart tests."""

from wod_chargen.core.data_loader import load_json_cached
from wod_chargen.venues import load_venue, mes_xp_for_month, resolve_xp_budget


def test_mes_xp_chart_jun_2026():
    chart = load_json_cached("wod_chargen.venues", "mes_xp_chart.json")
    assert mes_xp_for_month("2026-06", chart) == 185


def test_mes_xp_extension():
    chart = load_json_cached("wod_chargen.venues", "mes_xp_chart.json")
    assert mes_xp_for_month("2029-01", chart) == 340


def test_resolve_custom_xp_budget():
    venue = load_venue("custom_xp")
    xp, lines = resolve_xp_budget("custom_xp", {"xp": "250"})
    assert xp == 250
    assert any("Custom starting XP" in line for line in lines)


def test_resolve_custom_xp_requires_amount():
    import pytest

    with pytest.raises(ValueError, match="XP amount required"):
        resolve_xp_budget("custom_xp", {})
