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
    "merit": "Merits",
    "ghoul_power": "Ghoul Powers",
    "thin_blood_formula": "Thin-Blood Formulas",
    "loresheet": "Loresheets",
    "blood_potency": "Blood Potency",
}


def _sorted_entries(entries: list[XpLogEntry]) -> list[XpLogEntry]:
    return sorted(entries, key=lambda e: (e.item, e.new_level))


def format_xp_log(entries: list[XpLogEntry]) -> str:
    if not entries:
        return "No XP purchases."

    by_category: dict[str, list[XpLogEntry]] = defaultdict(list)
    for entry in entries:
        by_category[entry.category].append(entry)

    purchase_lines: list[str] = ["Purchases", ""]
    debug_lines: list[str] = ["Debug (internal weights)", ""]

    ordered_categories = [c for c in CATEGORY_ORDER if c in by_category]
    ordered_categories.extend(sorted(c for c in by_category if c not in CATEGORY_ORDER))

    for category in ordered_categories:
        group = _sorted_entries(by_category[category])
        label = CATEGORY_LABELS.get(category, category.replace("_", " ").title())
        purchase_lines.append(f"── {label} " + "─" * max(0, 36 - len(label)))
        for entry in group:
            purchase_lines.append(f"  {entry.item} → {entry.new_level} ({entry.cost} XP)")
            debug_lines.append(
                f"  [{category}] {entry.item} → {entry.new_level} | "
                f"group_w={entry.group_weight:.2f} item_bias={entry.item_bias:.2f} "
                f"clan={entry.clan_factor:.2f} eff={entry.efficiency_bias:.2f} "
                f"roll={entry.roll:.2f} score={entry.score:.2f}"
            )
        purchase_lines.append("")
        debug_lines.append("")

    return "\n".join(purchase_lines + debug_lines).rstrip()
