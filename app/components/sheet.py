"""LoTN V5 character sheet DOM renderer."""

from __future__ import annotations

from typing import Any

from pyscript import document

from wod_chargen.core.data_loader import load_json_cached
from wod_chargen.games.lotn_v5.clan_symbols import clan_symbol_path
from wod_chargen.games.lotn_v5.archetypes import get_archetype
from wod_chargen.games.lotn_v5.merits_flaws import trait_display_label
from wod_chargen.games.lotn_v5.disciplines import power_label
from wod_chargen.games.lotn_v5.backgrounds import (
    background_defs,
    background_label,
    level_label,
    level_summary,
    modifier_max_dots,
    sphere_label,
)

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


def _category_stat_column(title: str, trait_ids: list[str], values: dict[str, int]) -> Any:
    col = document.createElement("div")
    col.className = "sheet-trait-col"

    head = document.createElement("h4")
    head.className = "sheet-trait-col__title"
    head.innerText = title
    col.appendChild(head)

    stat_list = document.createElement("div")
    stat_list.className = "sheet-stat-list"
    for trait_id in trait_ids:
        stat_list.appendChild(_stat_line(trait_id, values.get(trait_id, 0)))
    col.appendChild(stat_list)
    return col


def _trait_panel(
    panel_title: str,
    categories: list[tuple[str, list[str]]],
    values: dict[str, int],
) -> Any:
    panel = document.createElement("section")
    panel.className = "sheet-trait-panel"
    panel.appendChild(_section_heading(panel_title))

    columns = document.createElement("div")
    columns.className = "sheet-trait-panel__columns"
    for category_title, trait_ids in categories:
        columns.appendChild(_category_stat_column(category_title, trait_ids, values))
    panel.appendChild(columns)
    return panel


def _disciplines_section(character: dict[str, Any]) -> Any | None:
    discs = {k: v for k, v in character.get("disciplines", {}).items() if v > 0}
    if not discs:
        return None
    picks = character.get("discipline_powers", {})
    section = document.createElement("section")
    section.className = "sheet-disciplines"
    section.appendChild(_section_heading("Disciplines"))
    list_el = document.createElement("div")
    list_el.className = "sheet-discipline-list"
    for disc_id, rating in sorted(discs.items()):
        card = document.createElement("div")
        card.className = "sheet-discipline-card"
        head = document.createElement("div")
        head.className = "sheet-discipline-card__head"
        name = document.createElement("span")
        name.className = "sheet-stat__name"
        name.innerText = _title(disc_id)
        head.appendChild(name)
        head.appendChild(_dot_row(int(rating), max_dots=5))
        card.appendChild(head)
        levels = picks.get(disc_id, {})
        if levels:
            powers = document.createElement("ul")
            powers.className = "sheet-discipline-card__powers"
            for level in sorted(levels.keys(), key=lambda x: int(x)):
                item = document.createElement("li")
                pid = levels[level]
                item.innerText = f"•{level} {power_label(pid)}"
                powers.appendChild(item)
            card.appendChild(powers)
        list_el.appendChild(card)
    section.appendChild(list_el)
    return section


def _power_id_list_section(title: str, power_ids: list[str]) -> Any | None:
    if not power_ids:
        return None
    section = document.createElement("section")
    section.className = "sheet-rated-traits"
    section.appendChild(_section_heading(title))
    grid = document.createElement("div")
    grid.className = "sheet-rated-traits__grid"
    for pid in sorted(power_ids):
        line = document.createElement("div")
        line.className = "sheet-stat"
        label = document.createElement("span")
        label.className = "sheet-stat__name"
        label.innerText = power_label(pid)
        line.appendChild(label)
        grid.appendChild(line)
    section.appendChild(grid)
    return section


def _formula_section(character: dict[str, Any]) -> Any | None:
    formulas = {k: v for k, v in character.get("thin_blood_formulas", {}).items() if v > 0}
    if not formulas:
        return None
    fp = character.get("formula_powers", {})
    section = document.createElement("section")
    section.className = "sheet-disciplines"
    section.appendChild(_section_heading("Thin-Blood Formulas"))
    list_el = document.createElement("div")
    list_el.className = "sheet-discipline-list"
    for fid in sorted(formulas.keys()):
        card = document.createElement("div")
        card.className = "sheet-discipline-card"
        name = document.createElement("span")
        name.className = "sheet-stat__name"
        name.innerText = power_label(fid)
        card.appendChild(name)
        list_el.appendChild(card)
    section.appendChild(list_el)
    return section


def _rated_traits_section(title: str, items: dict[str, int], *, kind: str | None = None) -> Any | None:
    rated = {k: v for k, v in items.items() if v > 0}
    if not rated:
        return None
    section = document.createElement("section")
    section.className = "sheet-rated-traits"
    section.appendChild(_section_heading(title))
    grid = document.createElement("div")
    grid.className = "sheet-rated-traits__grid"
    for key, value in sorted(rated.items()):
        label = trait_display_label(key, kind) if kind in ("merit", "flaw") else _title(key)
        grid.appendChild(_stat_line(label, value))
    section.appendChild(grid)
    return section


def _loresheet_section(character: dict[str, Any]) -> Any | None:
    sheets = character.get("loresheets") or {}
    rated = {k: v for k, v in sheets.items() if int(v) > 0}
    if not rated:
        return None
    catalog = {
        ls["id"]: ls["label"]
        for ls in load_json_cached(DATA, "loresheets.json").get("loresheets", [])
    }
    section = document.createElement("section")
    section.className = "sheet-rated-traits"
    section.appendChild(_section_heading("Loresheet"))
    grid = document.createElement("div")
    grid.className = "sheet-rated-traits__grid"
    for ls_id, dots in sorted(rated.items()):
        label = catalog.get(ls_id, _title(ls_id))
        grid.appendChild(_stat_line(label, int(dots)))
    section.appendChild(grid)
    meta = character.get("loresheet_meta") or {}
    narratives = meta.get("narratives") or []
    if narratives:
        notes = document.createElement("div")
        notes.className = "sheet-loresheet-notes"
        for entry in narratives:
            p = document.createElement("p")
            p.className = "sheet-loresheet-notes__item"
            p.textContent = f"{entry.get('label', entry.get('id', ''))}: {entry.get('narrative', '')}"
            notes.appendChild(p)
        section.appendChild(notes)
    return section


def _modifier_list(items: list[Any], catalog: list[dict[str, Any]], css: str) -> Any:
    wrap = document.createElement("div")
    wrap.className = f"sheet-bg-modifiers sheet-bg-modifiers--{css}"
    catalog_by_id = {entry["id"]: entry for entry in catalog}
    for raw in items:
        if isinstance(raw, dict):
            mod_id = raw.get("id", "")
            dots = int(raw.get("dots", 1))
        else:
            mod_id = str(raw)
            dots = 1
        mod_def = catalog_by_id.get(mod_id, {})
        label = mod_def.get("label", mod_id.replace("_", " ").title())
        max_dots = modifier_max_dots(mod_def) if mod_def else max(dots, 1)

        tag = document.createElement("span")
        tag.className = f"sheet-bg-modifier sheet-bg-modifier--{css}"
        name = document.createElement("span")
        name.className = "sheet-bg-modifier__label"
        name.innerText = label
        tag.appendChild(name)
        dots_el = _dot_row(dots, max_dots=max_dots)
        dots_el.classList.add("sheet-dots--compact")
        tag.appendChild(dots_el)
        wrap.appendChild(tag)
    return wrap


def _background_card_title_el(entry: dict[str, Any], bg_type: str) -> Any:
    wrap = document.createElement("span")
    wrap.className = "sheet-background-card__title"
    type_line = document.createElement("span")
    type_line.className = "sheet-background-card__type"
    type_line.innerText = background_label(bg_type)
    wrap.appendChild(type_line)
    sphere_id = entry.get("sphere")
    if sphere_id:
        sep = document.createElement("span")
        sep.className = "sheet-background-card__sep"
        sep.setAttribute("aria-hidden", "true")
        sep.innerText = "·"
        wrap.appendChild(sep)
        sphere = document.createElement("span")
        sphere.className = "sheet-background-card__sphere"
        sphere.innerText = sphere_label(sphere_id)
        wrap.appendChild(sphere)
    return wrap


def _background_section(entries: list[dict[str, Any]]) -> Any | None:
    rated = [e for e in entries if int(e.get("dots", 0)) > 0]
    if not rated:
        return None
    section = document.createElement("section")
    section.className = "sheet-backgrounds"
    section.appendChild(_section_heading("Backgrounds"))
    list_el = document.createElement("div")
    list_el.className = "sheet-background-list"

    defs = background_defs()
    for entry in rated:
        bg_type = entry.get("type", "")
        spec = defs.get(bg_type, {})
        card = document.createElement("div")
        card.className = "sheet-background-card"

        head = document.createElement("div")
        head.className = "sheet-background-card__head"
        head.appendChild(_background_card_title_el(entry, bg_type))
        head.appendChild(_dot_row(int(entry.get("dots", 0)), max_dots=int(spec.get("max_dots", 3))))
        card.appendChild(head)

        lvl = document.createElement("p")
        lvl.className = "sheet-background-card__level"
        dots = int(entry.get("dots", 0))
        lvl.innerText = f"{level_label(bg_type, dots)} — {level_summary(bg_type, dots)}"
        card.appendChild(lvl)

        if entry.get("advantages"):
            card.appendChild(_modifier_list(entry["advantages"], spec.get("advantages", []), "adv"))
        if entry.get("disadvantages"):
            card.appendChild(_modifier_list(entry["disadvantages"], spec.get("disadvantages", []), "dis"))

        list_el.appendChild(card)
    section.appendChild(list_el)
    return section


def _convictions_section(
    convictions: list[dict[str, str]],
    *,
    convictions_seed: int,
    on_reroll=None,
) -> Any:
    section = document.createElement("section")
    section.className = "sheet-convictions"
    section.appendChild(_section_heading("Convictions"))

    list_el = document.createElement("ol")
    list_el.className = "sheet-convictions__list"
    for idx, entry in enumerate(convictions, start=1):
        item = document.createElement("li")
        item.className = "sheet-convictions__item"
        item.innerText = entry["text"]
        list_el.appendChild(item)
    section.appendChild(list_el)

    footer = document.createElement("div")
    footer.className = "sheet-convictions__footer no-print"

    seed_note = document.createElement("p")
    seed_note.className = "sheet-convictions__seed"
    seed_note.innerText = f"Convictions seed {convictions_seed}"
    footer.appendChild(seed_note)

    if on_reroll is not None:
        btn = document.createElement("button")
        btn.type = "button"
        btn.className = "btn-secondary sheet-convictions__reroll"
        btn.innerText = "Re-roll convictions"
        btn.onclick = on_reroll
        footer.appendChild(btn)

    section.appendChild(footer)
    return section


def render_lotn_v5_sheet(
    character: dict[str, Any],
    *,
    convictions: list[dict[str, str]] | None = None,
    convictions_seed: int | None = None,
    on_reroll_convictions=None,
) -> Any:
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
        symbol.src = clans[clan_id].get("symbol", clan_symbol_path(clan_id))
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

    if convictions and convictions_seed is not None:
        sheet.appendChild(
            _convictions_section(
                convictions,
                convictions_seed=convictions_seed,
                on_reroll=on_reroll_convictions,
            )
        )

    trait_categories = [
        ("Physical", "physical"),
        ("Social", "social"),
        ("Mental", "mental"),
    ]
    sheet.appendChild(
        _trait_panel(
            "Attributes",
            [(label, attrs[cat_id]) for label, cat_id in trait_categories],
            character["attributes"],
        )
    )
    sheet.appendChild(
        _trait_panel(
            "Skills",
            [(label, skills[cat_id]) for label, cat_id in trait_categories],
            character["skills"],
        )
    )

    for section_title, block, trait_kind in (
        ("Merits", character.get("merits", {}), "merit"),
        ("Flaws", character.get("flaws", {}), "flaw"),
        ("Ghoul Powers", character.get("ghoul_powers", {}), None),
    ):
        section = _rated_traits_section(section_title, block, kind=trait_kind)
        if section:
            sheet.appendChild(section)

    ls_section = _loresheet_section(character)
    if ls_section:
        sheet.appendChild(ls_section)

    disc_section = _disciplines_section(character)
    if disc_section:
        sheet.appendChild(disc_section)

    ritual_section = _power_id_list_section("Rituals", character.get("rituals", []))
    if ritual_section:
        sheet.appendChild(ritual_section)

    ceremony_section = _power_id_list_section("Ceremonies", character.get("ceremonies", []))
    if ceremony_section:
        sheet.appendChild(ceremony_section)

    formula_section = _formula_section(character)
    if formula_section:
        sheet.appendChild(formula_section)

    specialties = character.get("specialties", [])
    if specialties:
        spec_section = document.createElement("section")
        spec_section.className = "sheet-rated-traits"
        spec_section.appendChild(_section_heading("Specialties"))
        grid = document.createElement("div")
        grid.className = "sheet-rated-traits__grid"
        for spec in specialties:
            line = document.createElement("div")
            line.className = "sheet-stat"
            label = document.createElement("span")
            label.className = "sheet-stat__name"
            label.innerText = f"{_title(spec['skill'])} ({spec['name']})"
            line.appendChild(label)
            grid.appendChild(line)
        spec_section.appendChild(grid)
        sheet.appendChild(spec_section)

    bg_section = _background_section(character.get("backgrounds", []))
    if bg_section:
        sheet.appendChild(bg_section)

    return sheet
