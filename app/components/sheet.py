"""LoTN V5 character sheet DOM renderer."""

from __future__ import annotations

from typing import Any

from pyscript import document

from wod_chargen.games.lotn_v5.sheet_model import (
    BackgroundCard,
    BackgroundModifier,
    BackgroundsSection,
    ConvictionsSection,
    DisciplineCard,
    DisciplinesSection,
    DotRow,
    LoresheetSection,
    MetaItem,
    NamedItemsSection,
    RatedTraitsSection,
    SheetHeader,
    SheetModel,
    StatLine,
    TraitColumn,
    TraitPanel,
)


def _dot_row(dots: DotRow) -> Any:
    row = document.createElement("span")
    row.className = "sheet-dots"
    filled = max(0, int(dots.value))
    max_dots = dots.max_dots
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


def _stat_line(stat: StatLine) -> Any:
    line = document.createElement("div")
    line.className = "sheet-stat"
    label = document.createElement("span")
    label.className = "sheet-stat__name"
    label.innerText = stat.label
    line.appendChild(label)
    line.appendChild(_dot_row(stat.dots))
    return line


def _section_heading(text: str) -> Any:
    head = document.createElement("h3")
    head.className = "sheet-section__title"
    head.innerText = text
    return head


def _meta_item(item: MetaItem) -> Any:
    wrap = document.createElement("div")
    wrap.className = "sheet-meta__item"
    dt = document.createElement("span")
    dt.className = "sheet-meta__label"
    dt.innerText = item.label
    dd = document.createElement("span")
    dd.className = "sheet-meta__value"
    dd.innerText = item.value
    wrap.appendChild(dt)
    wrap.appendChild(dd)
    return wrap


def _category_stat_column(column: TraitColumn) -> Any:
    col = document.createElement("div")
    col.className = "sheet-trait-col"

    head = document.createElement("h4")
    head.className = "sheet-trait-col__title"
    head.innerText = column.title
    col.appendChild(head)

    stat_list = document.createElement("div")
    stat_list.className = "sheet-stat-list"
    for stat in column.stats:
        stat_list.appendChild(_stat_line(stat))
    col.appendChild(stat_list)
    return col


def _trait_panel(panel: TraitPanel) -> Any:
    section = document.createElement("section")
    section.className = "sheet-trait-panel"
    section.appendChild(_section_heading(panel.title))

    columns = document.createElement("div")
    columns.className = "sheet-trait-panel__columns"
    for column in panel.columns:
        columns.appendChild(_category_stat_column(column))
    section.appendChild(columns)
    return section


def _discipline_card(card: DisciplineCard) -> Any:
    card_el = document.createElement("div")
    card_el.className = "sheet-discipline-card"
    head = document.createElement("div")
    head.className = "sheet-discipline-card__head"
    name = document.createElement("span")
    name.className = "sheet-stat__name"
    name.innerText = card.name
    head.appendChild(name)
    head.appendChild(_dot_row(card.rating))
    card_el.appendChild(head)
    if card.powers:
        powers = document.createElement("ul")
        powers.className = (
            "sheet-discipline-card__powers sheet-discipline-card__powers--ghoul"
            if card.ghoul_powers
            else "sheet-discipline-card__powers"
        )
        for power_text in card.powers:
            item = document.createElement("li")
            item.innerText = power_text
            powers.appendChild(item)
        card_el.appendChild(powers)
    return card_el


def _disciplines_section(section: DisciplinesSection, *, css_class: str = "sheet-disciplines") -> Any:
    el = document.createElement("section")
    el.className = css_class
    el.appendChild(_section_heading(section.title))
    list_el = document.createElement("div")
    list_el.className = "sheet-discipline-list"
    for card in section.cards:
        list_el.appendChild(_discipline_card(card))
    el.appendChild(list_el)
    return el


def _named_items_section(section: NamedItemsSection) -> Any:
    el = document.createElement("section")
    el.className = "sheet-rated-traits"
    el.appendChild(_section_heading(section.title))
    grid = document.createElement("div")
    grid.className = "sheet-rated-traits__grid"
    for label in section.items:
        line = document.createElement("div")
        line.className = "sheet-stat"
        name = document.createElement("span")
        name.className = "sheet-stat__name"
        name.innerText = label
        line.appendChild(name)
        grid.appendChild(line)
    el.appendChild(grid)
    return el


def _formula_section(section: NamedItemsSection) -> Any:
    el = document.createElement("section")
    el.className = "sheet-disciplines"
    el.appendChild(_section_heading(section.title))
    list_el = document.createElement("div")
    list_el.className = "sheet-discipline-list"
    for label in section.items:
        card = document.createElement("div")
        card.className = "sheet-discipline-card"
        name = document.createElement("span")
        name.className = "sheet-stat__name"
        name.innerText = label
        card.appendChild(name)
        list_el.appendChild(card)
    el.appendChild(list_el)
    return el


def _rated_traits_section(section: RatedTraitsSection, *, css_class: str = "sheet-rated-traits") -> Any:
    el = document.createElement("section")
    el.className = css_class
    el.appendChild(_section_heading(section.title))
    grid = document.createElement("div")
    grid.className = "sheet-rated-traits__grid"
    for stat in section.stats:
        grid.appendChild(_stat_line(stat))
    el.appendChild(grid)
    return el


def _loresheet_section(section: LoresheetSection) -> Any:
    el = document.createElement("section")
    el.className = "sheet-rated-traits"
    el.appendChild(_section_heading("Loresheet"))
    grid = document.createElement("div")
    grid.className = "sheet-rated-traits__grid"
    for stat in section.stats:
        grid.appendChild(_stat_line(stat))
    el.appendChild(grid)
    if section.notes:
        notes = document.createElement("div")
        notes.className = "sheet-loresheet-notes"
        for text in section.notes:
            p = document.createElement("p")
            p.className = "sheet-loresheet-notes__item"
            p.textContent = text
            notes.appendChild(p)
        el.appendChild(notes)
    return el


def _modifier_tag(modifier: BackgroundModifier, css: str) -> Any:
    tag = document.createElement("span")
    tag.className = f"sheet-bg-modifier sheet-bg-modifier--{css}"
    name = document.createElement("span")
    name.className = "sheet-bg-modifier__label"
    name.innerText = modifier.label
    tag.appendChild(name)
    dots_el = _dot_row(modifier.dots)
    dots_el.classList.add("sheet-dots--compact")
    tag.appendChild(dots_el)
    return tag


def _modifier_list(modifiers: tuple[BackgroundModifier, ...], css: str) -> Any:
    wrap = document.createElement("div")
    wrap.className = f"sheet-bg-modifiers sheet-bg-modifiers--{css}"
    for modifier in modifiers:
        wrap.appendChild(_modifier_tag(modifier, css))
    return wrap


def _background_card_title_el(card: BackgroundCard) -> Any:
    wrap = document.createElement("span")
    wrap.className = "sheet-background-card__title"
    type_line = document.createElement("span")
    type_line.className = "sheet-background-card__type"
    type_line.innerText = card.type_label
    wrap.appendChild(type_line)
    if card.sphere_label:
        sep = document.createElement("span")
        sep.className = "sheet-background-card__sep"
        sep.setAttribute("aria-hidden", "true")
        sep.innerText = "·"
        wrap.appendChild(sep)
        sphere = document.createElement("span")
        sphere.className = "sheet-background-card__sphere"
        sphere.innerText = card.sphere_label
        wrap.appendChild(sphere)
    return wrap


def _background_section(section: BackgroundsSection) -> Any:
    el = document.createElement("section")
    el.className = "sheet-backgrounds"
    el.appendChild(_section_heading("Backgrounds"))
    list_el = document.createElement("div")
    list_el.className = "sheet-background-list"
    for card in section.cards:
        card_el = document.createElement("div")
        card_el.className = "sheet-background-card"

        head = document.createElement("div")
        head.className = "sheet-background-card__head"
        head.appendChild(_background_card_title_el(card))
        head.appendChild(_dot_row(card.dots))
        card_el.appendChild(head)

        lvl = document.createElement("p")
        lvl.className = "sheet-background-card__level"
        lvl.innerText = card.level_text
        card_el.appendChild(lvl)

        if card.advantages:
            card_el.appendChild(_modifier_list(card.advantages, "adv"))
        if card.disadvantages:
            card_el.appendChild(_modifier_list(card.disadvantages, "dis"))

        list_el.appendChild(card_el)
    el.appendChild(list_el)
    return el


def _convictions_section(section: ConvictionsSection, *, on_reroll=None) -> Any:
    el = document.createElement("section")
    el.className = "sheet-convictions"
    el.appendChild(_section_heading("Convictions"))

    list_el = document.createElement("ol")
    list_el.className = "sheet-convictions__list"
    for text in section.items:
        item = document.createElement("li")
        item.className = "sheet-convictions__item"
        item.innerText = text
        list_el.appendChild(item)
    el.appendChild(list_el)

    footer = document.createElement("div")
    footer.className = "sheet-convictions__footer no-print"

    seed_note = document.createElement("p")
    seed_note.className = "sheet-convictions__seed"
    seed_note.innerText = f"Convictions seed {section.seed}"
    footer.appendChild(seed_note)

    if on_reroll is not None:
        btn = document.createElement("button")
        btn.type = "button"
        btn.className = "btn-secondary sheet-convictions__reroll"
        btn.innerText = "Re-roll convictions"
        btn.onclick = on_reroll
        footer.appendChild(btn)

    el.appendChild(footer)
    return el


def _render_header(header: SheetHeader) -> Any:
    header_el = document.createElement("header")
    header_el.className = "sheet-header"

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

    if header.clan_symbol_src:
        symbol = document.createElement("img")
        symbol.className = "sheet-header__clan"
        symbol.src = header.clan_symbol_src
        symbol.alt = header.clan_symbol_alt or ""
        title_row.appendChild(symbol)

    header_el.appendChild(title_row)

    meta = document.createElement("div")
    meta.className = "sheet-meta"
    for item in header.meta:
        meta.appendChild(_meta_item(item))
    header_el.appendChild(meta)
    return header_el


def render_lotn_v5_sheet(model: SheetModel, *, on_reroll_convictions=None) -> Any:
    """Build a printable LoTN-style sheet element from a sheet view-model."""
    sheet = document.createElement("article")
    sheet.className = "character-sheet"
    sheet.appendChild(_render_header(model.header))

    if model.convictions:
        sheet.appendChild(_convictions_section(model.convictions, on_reroll=on_reroll_convictions))

    if model.attributes:
        sheet.appendChild(_trait_panel(model.attributes))
    if model.skills:
        sheet.appendChild(_trait_panel(model.skills))

    for section in (model.merits, model.flaws):
        if section:
            sheet.appendChild(_rated_traits_section(section))

    for section in (model.thin_blood_merits, model.thin_blood_flaws):
        if section:
            sheet.appendChild(
                _rated_traits_section(section, css_class="sheet-rated-traits sheet-rated-traits--thin-blood")
            )

    if model.loresheet:
        sheet.appendChild(_loresheet_section(model.loresheet))

    if model.resonance_discipline:
        sheet.appendChild(
            _disciplines_section(model.resonance_discipline, css_class="sheet-disciplines sheet-disciplines--resonance")
        )

    if model.disciplines:
        sheet.appendChild(_disciplines_section(model.disciplines))

    for section in (model.rituals, model.ceremonies):
        if section:
            sheet.appendChild(_named_items_section(section))

    if model.formulas:
        sheet.appendChild(_formula_section(model.formulas))

    if model.specialties:
        spec_section = document.createElement("section")
        spec_section.className = "sheet-rated-traits"
        spec_section.appendChild(_section_heading("Specialties"))
        grid = document.createElement("div")
        grid.className = "sheet-rated-traits__grid"
        for label in model.specialties:
            line = document.createElement("div")
            line.className = "sheet-stat"
            name = document.createElement("span")
            name.className = "sheet-stat__name"
            name.innerText = label
            line.appendChild(name)
            grid.appendChild(line)
        spec_section.appendChild(grid)
        sheet.appendChild(spec_section)

    if model.backgrounds:
        sheet.appendChild(_background_section(model.backgrounds))

    return sheet
