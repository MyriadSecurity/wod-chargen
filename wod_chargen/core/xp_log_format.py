"""Format XP purchase logs for display."""

from __future__ import annotations

from collections import defaultdict

from wod_chargen.core.models import XpLogEntry

CATEGORY_ORDER = (
    "attribute",
    "skill",
    "discipline",
    "background",
    "background_modifier",
    "background_disadvantage",
    "merit",
    "ghoul_power",
    "thin_blood_formula",
    "loresheet",
    "blood_potency",
)

CATEGORY_LABELS = {
    "attribute": "Attributes",
    "skill": "Skills",
    "discipline": "Disciplines",
    "background": "Backgrounds",
    "background_modifier": "Background Modifiers",
    "background_disadvantage": "Background Disadvantages",
    "merit": "Merits",
    "ghoul_power": "Discipline Powers",
    "thin_blood_formula": "Thin-Blood Formulas",
    "loresheet": "Loresheets",
    "blood_potency": "Blood Potency",
}


def _sorted_entries(entries: list[XpLogEntry]) -> list[XpLogEntry]:
    return sorted(entries, key=lambda e: (e.item, e.new_level))


def _format_cost(entry: XpLogEntry) -> str:
    if entry.cost > 0:
        return f"{entry.cost} XP"
    if entry.source == "disadv_trade":
        return "free (disadv trade)"
    if entry.source == "free":
        return "free"
    return "0 XP"


def _format_item(entry: XpLogEntry) -> str:
    if entry.category == "ghoul_power":
        from wod_chargen.games.lotn_v5.disciplines import power_by_id, power_label

        power = power_by_id(entry.item)
        if power:
            disc_id = power.get("discipline_id", "")
            label = power_label(entry.item)
            if disc_id:
                disc = disc_id.replace("_", " ").title()
                return f"{label} ({disc})"
            return label
    return entry.item


def format_xp_log(entries: list[XpLogEntry]) -> str:
    if not entries:
        return "No XP purchases."

    by_category: dict[str, list[XpLogEntry]] = defaultdict(list)
    for entry in entries:
        by_category[entry.category].append(entry)

    purchase_lines: list[str] = ["Purchases", ""]

    ordered_categories = [c for c in CATEGORY_ORDER if c in by_category]
    ordered_categories.extend(sorted(c for c in by_category if c not in CATEGORY_ORDER))

    for category in ordered_categories:
        group = _sorted_entries(by_category[category])
        label = CATEGORY_LABELS.get(category, category.replace("_", " ").title())
        purchase_lines.append(f"── {label} " + "─" * max(0, 36 - len(label)))
        for entry in group:
            purchase_lines.append(f"  {_format_item(entry)} → {entry.new_level} ({_format_cost(entry)})")
        purchase_lines.append("")

    return "\n".join(purchase_lines).rstrip()
