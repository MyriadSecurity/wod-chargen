"""LoTN V5 character sheet DOM renderer."""

from __future__ import annotations

from typing import Any

from pyscript import document

from wod_chargen.core.data_loader import load_json_cached
from wod_chargen.games.lotn_v5.archetypes import get_archetype

DATA = "wod_chargen.games.lotn_v5.data"


def _title(key: str) -> str:
    return key.replace("_", " ").title()


def _lookup_label(mapping: dict[str, Any], item_id: str | None) -> str:
    if not item_id:
        return "—"
    entry = mapping.get(item_id)
    if isinstance(entry, dict):
        return entry.get("label", _title(item_id))
    return _title(item_id)


def _dot_row(value: int, *, max_dots: int = 5) -> Any:
    row = document.createElement("span")
    row.className = "sheet-dots"
    filled = max(0, int(value))
    for i in range(1, max_dots + 1):
        dot = document.createElement("span")
        dot.className = "sheet-dot sheet-dot--filled" if i <= min(filled, max_dots) else "sheet-dot"
        dot.setAttribute("aria-hidden", "true")
        row.appendChild(dot)
    if filled > max_dots:
        extra = document.createElement("span")
        extra.className = "sheet-dot-extra"
        extra.innerText = f"+{filled - max_dots}"
        row.appendChild(extra)
    return row


def _stat_line(name: str, value: int) -> Any:
    line = document.createElement("div")
    line.className = "sheet-stat"
    label = document.createElement("span")
    label.className = "sheet-stat__name"
    label.innerText = _title(name)
    line.appendChild(label)
    line.appendChild(_dot_row(value))
    return line


def _section_heading(text: str) -> Any:
    head = document.createElement("h3")
    head.className = "sheet-section__title"
    head.innerText = text
    return head


def _meta_item(label: str, value: str) -> Any:
    wrap = document.createElement("div")
    wrap.className = "sheet-meta__item"
    dt = document.createElement("span")
    dt.className = "sheet-meta__label"
    dt.innerText = label
    dd = document.createElement("span")
    dd.className = "sheet-meta__value"
    dd.innerText = value
    wrap.appendChild(dt)
    wrap.appendChild(dd)
    return wrap


def _trait_column(title: str, attrs: list[str], skills: list[str], character: dict[str, Any]) -> Any:
    col = document.createElement("section")
    col.className = "sheet-column"

    col.appendChild(_section_heading(title))

    attr_block = document.createElement("div")
    attr_block.className = "sheet-block"
    attr_head = document.createElement("h4")
    attr_head.className = "sheet-block__title"
    attr_head.innerText = "Attributes"
    attr_block.appendChild(attr_head)
    attr_list = document.createElement("div")
    attr_list.className = "sheet-stat-list"
    for attr in attrs:
        attr_list.appendChild(_stat_line(attr, character["attributes"].get(attr, 0)))
    attr_block.appendChild(attr_list)
    col.appendChild(attr_block)

    skill_block = document.createElement("div")
    skill_block.className = "sheet-block"
    skill_head = document.createElement("h4")
    skill_head.className = "sheet-block__title"
    skill_head.innerText = "Skills"
    skill_block.appendChild(skill_head)
    skill_list = document.createElement("div")
    skill_list.className = "sheet-stat-list"
    for skill in skills:
        skill_list.appendChild(_stat_line(skill, character["skills"].get(skill, 0)))
    skill_block.appendChild(skill_list)
    col.appendChild(skill_block)

    return col


def _advantage_section(title: str, items: dict[str, int]) -> Any | None:
    rated = {k: v for k, v in items.items() if v > 0}
    if not rated:
        return None
    section = document.createElement("section")
    section.className = "sheet-advantages"
    section.appendChild(_section_heading(title))
    grid = document.createElement("div")
    grid.className = "sheet-advantage-grid"
    for key, value in sorted(rated.items()):
        grid.appendChild(_stat_line(key, value))
    section.appendChild(grid)
    return section


def render_lotn_v5_sheet(character: dict[str, Any]) -> Any:
    """Build a printable LoTN-style sheet element from generated character data."""
    attrs = load_json_cached(DATA, "attributes.json")
    skills = load_json_cached(DATA, "skills.json")
    clans = load_json_cached(DATA, "clans.json")
    types = load_json_cached(DATA, "character_types.json")
    predators = {t["id"]: t["label"] for t in load_json_cached(DATA, "predator_types.json")["types"]}

    ctype = character.get("character_type", "vampire")
    arch_id = character.get("archetype", "")
    sub_id = character.get("sub_archetype", "")
    arch = get_archetype(arch_id)
    sub = next((s for s in arch.sub_archetypes if s.id == sub_id), None)

    sheet = document.createElement("article")
    sheet.className = "character-sheet"

    header = document.createElement("header")
    header.className = "sheet-header"

    title_row = document.createElement("div")
    title_row.className = "sheet-header__top"
    title = document.createElement("h2")
    title.className = "sheet-header__title"
    title.innerText = "Laws of the Night"
    subtitle = document.createElement("p")
    subtitle.className = "sheet-header__subtitle"
    subtitle.innerText = "Character Sheet"
    title_row.appendChild(title)
    title_row.appendChild(subtitle)

    clan_id = character.get("clan") or character.get("domitor_clan")
    if clan_id and clan_id in clans:
        symbol = document.createElement("img")
        symbol.className = "sheet-header__clan"
        symbol.src = clans[clan_id].get("symbol", f"static/img/clans/{clan_id}.svg")
        symbol.alt = clans[clan_id]["label"]
        title_row.appendChild(symbol)

    header.appendChild(title_row)

    meta = document.createElement("div")
    meta.className = "sheet-meta"
    meta.appendChild(_meta_item("Type", types.get(ctype, {}).get("label", _title(ctype))))
    if character.get("clan"):
        meta.appendChild(_meta_item("Clan", _lookup_label(clans, character["clan"])))
    if character.get("domitor_clan"):
        meta.appendChild(_meta_item("Domitor", _lookup_label(clans, character["domitor_clan"])))
    meta.appendChild(_meta_item("Archetype", arch.label))
    if sub:
        meta.appendChild(_meta_item("Subtype", sub.label))
    if character.get("predator"):
        meta.appendChild(_meta_item("Predator", predators.get(character["predator"], _title(character["predator"]))))
    meta.appendChild(_meta_item("Generation", str(character.get("generation", "—"))))
    meta.appendChild(_meta_item("Blood Potency", str(character.get("blood_potency", 0))))
    meta.appendChild(_meta_item("Humanity", str(character.get("humanity", "—"))))
    header.appendChild(meta)
    sheet.appendChild(header)

    columns = document.createElement("div")
    columns.className = "sheet-columns"
    columns.appendChild(_trait_column("Physical", attrs["physical"], skills["physical"], character))
    columns.appendChild(_trait_column("Social", attrs["social"], skills["social"], character))
    columns.appendChild(_trait_column("Mental", attrs["mental"], skills["mental"], character))
    sheet.appendChild(columns)

    for section_title, block in (
        ("Disciplines", character.get("disciplines", {})),
        ("Backgrounds", character.get("backgrounds", {})),
        ("Merits", character.get("merits", {})),
        ("Loresheets", character.get("loresheets", {})),
        ("Ghoul Powers", character.get("ghoul_powers", {})),
        ("Thin-Blood Formulas", character.get("thin_blood_formulas", {})),
    ):
        section = _advantage_section(section_title, block)
        if section:
            sheet.appendChild(section)

    return sheet
