"""Venue loading and XP budget resolution."""

from __future__ import annotations
from functools import lru_cache
from typing import Any

from wod_chargen.core.data_loader import load_json_cached

VENUE_PACKAGE = "wod_chargen.venues"


@lru_cache(maxsize=16)
def load_venue(venue_id: str) -> dict[str, Any]:
    return load_json_cached(VENUE_PACKAGE, f"{venue_id}.json")


def mes_xp_for_month(approval: str, chart: dict[str, Any]) -> int:
    """Return Game XP for YYYY-MM approval month."""
    if approval in chart.get("lookup", {}):
        return int(chart["lookup"][approval])

    base = chart.get("extension", {})
    anchor_year = int(base.get("anchor_year", 2025))
    anchor_month = int(base.get("anchor_month", 1))
    start_xp = int(base.get("start_xp", 100))
    increment = int(base.get("monthly_increment", 5))

    year, month = map(int, approval.split("-"))
    months = (year - anchor_year) * 12 + (month - anchor_month)
    if months < 0:
        raise ValueError(f"Approval month {approval} is before chart anchor")
    return start_xp + months * increment


def resolve_xp_budget(venue_id: str, options: dict[str, Any]) -> tuple[int, list[str]]:
    venue = load_venue(venue_id)
    method = venue.get("xp_method", "fixed")
    log_lines: list[str] = []

    if method == "mes_approval_month":
        approval = options.get("approval")
        if not approval:
            raise ValueError("approval month (YYYY-MM) required for MES venue")
        chart_ref = venue.get("xp_config", {}).get("chart_ref", "mes_xp_chart.json")
        chart = load_json_cached(VENUE_PACKAGE, chart_ref)
        xp = mes_xp_for_month(approval, chart)
        log_lines.append(f"Game XP ({approval} approval): {xp}")
        return xp, log_lines

    if method == "fixed":
        total = int(venue.get("xp_config", {}).get("total", 100))
        log_lines.append(f"Fixed starting XP: {total}")
        return total, log_lines

    if method == "custom":
        raw = options.get("xp")
        if raw is None or str(raw).strip() == "":
            raise ValueError("XP amount required for custom XP")
        try:
            xp = int(raw)
        except (TypeError, ValueError) as exc:
            raise ValueError("XP must be a whole number") from exc
        if xp < 0:
            raise ValueError("XP must be zero or greater")
        log_lines.append(f"Custom starting XP: {xp}")
        return xp, log_lines

    raise ValueError(f"Unknown xp_method: {method}")
