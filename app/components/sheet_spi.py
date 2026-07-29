"""SPI character sheet DOM renderer."""

from __future__ import annotations

from typing import Any

from pyscript import document

from app.components.sheet import (
    _dot_row,
    _meta_item,
    _section_heading,
    _stat_line,
    _trait_panel,
)
from wod_chargen.games.spi.sheet_model import RatedTraitsSection, SpiSheetModel


def _rated_stat(stat) -> Any:
    """Render a rated trait; include flavor blurb when present (merits/powers)."""
    if not getattr(stat, "description", None):
        return _stat_line(stat)
    card = document.createElement("div")
    card.className = "sheet-stat sheet-stat--described"
    head = document.createElement("div")
    head.className = "sheet-stat__head"
    label = document.createElement("span")
    label.className = "sheet-stat__name"
    label.innerText = stat.label
    head.appendChild(label)
    head.appendChild(_dot_row(stat.dots))
    card.appendChild(head)
    blurb = document.createElement("p")
    blurb.className = "sheet-stat__blurb"
    blurb.innerText = stat.description
    card.appendChild(blurb)
    return card


def _rated_section(section: RatedTraitsSection) -> Any:
    el = document.createElement("section")
    el.className = "sheet-rated-traits"
    el.appendChild(_section_heading(section.title))
    if not section.stats:
        empty = document.createElement("p")
        empty.className = "text-stone-500 text-sm"
        empty.innerText = "None"
        el.appendChild(empty)
        return el
    has_blurbs = any(getattr(s, "description", None) for s in section.stats)
    grid = document.createElement("div")
    grid.className = (
        "sheet-rated-traits__grid sheet-rated-traits__grid--described"
        if has_blurbs
        else "sheet-rated-traits__grid"
    )
    for stat in section.stats:
        grid.appendChild(_rated_stat(stat))
    el.appendChild(grid)
    return el


def render_spi_sheet(model: SpiSheetModel) -> Any:
    root = document.createElement("div")
    root.className = "character-sheet character-sheet--spi"

    header = document.createElement("header")
    header.className = "sheet-header"
    meta = document.createElement("div")
    meta.className = "sheet-meta"
    for item in model.header.meta:
        meta.appendChild(_meta_item(item))
    header.appendChild(meta)
    root.appendChild(header)

    root.appendChild(_trait_panel(model.attributes))
    root.appendChild(_trait_panel(model.skills))

    if model.specialties:
        specs = document.createElement("section")
        specs.className = "sheet-rated-traits"
        specs.appendChild(_section_heading("Specialties"))
        ul = document.createElement("ul")
        ul.className = "sheet-specialty-list"
        for sp in model.specialties:
            li = document.createElement("li")
            li.innerText = sp
            ul.appendChild(li)
        specs.appendChild(ul)
        root.appendChild(specs)

    root.appendChild(_rated_section(model.affinities))
    root.appendChild(_rated_section(model.merits_general))
    root.appendChild(_rated_section(model.merits_affinity))

    adv = document.createElement("section")
    adv.className = "sheet-advantages"
    adv.appendChild(_section_heading("Advantages"))
    grid = document.createElement("div")
    grid.className = "sheet-meta"
    for item in model.advantages:
        grid.appendChild(_meta_item(item))
    adv.appendChild(grid)
    root.appendChild(adv)

    return root
