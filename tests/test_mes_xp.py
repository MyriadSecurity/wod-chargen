"""MES XP chart tests."""

from wod_chargen.venues import mes_xp_for_month
from wod_chargen.core.data_loader import load_json_cached


def test_mes_xp_chart_jun_2026():
    chart = load_json_cached("wod_chargen.venues", "mes_xp_chart.json")
    assert mes_xp_for_month("2026-06", chart) == 185


def test_mes_xp_extension():
    chart = load_json_cached("wod_chargen.venues", "mes_xp_chart.json")
    assert mes_xp_for_month("2029-01", chart) == 340
