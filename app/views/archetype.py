"""Archetype and subtype wizard steps."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pyscript import document

from wod_chargen.games.lotn_v5.archetypes import (
    THIN_BLOOD_ONLY_SUFFIX,
    archetype_display_label,
    archetypes_for_type,
    get_archetype,
    is_thin_blood_only,
)

if TYPE_CHECKING:
    from app.wizard import WizardApp


def append_archetype_label(parent: Any, profile: Any) -> None:
    label = document.createElement("span")
    label.className = "archetype-card__label"
    name = document.createElement("span")
    name.innerText = profile.label
    label.appendChild(name)
    if is_thin_blood_only(profile):
        note = document.createElement("span")
        note.className = "archetype-card__type-note"
        note.innerText = THIN_BLOOD_ONLY_SUFFIX
        label.appendChild(note)
    parent.appendChild(label)


def render_archetype(app: WizardApp) -> Any:
    el = document.createElement("div")
    profiles = archetypes_for_type(app.state["type"])

    grid = document.createElement("div")
    grid.className = "archetype-grid"
    for p in profiles:
        btn = document.createElement("button")
        active = app.state["arch"] == p.id
        btn.className = f"archetype-card archetype-card--pickable {'archetype-card--active' if active else ''}"
        btn.setAttribute("type", "button")

        append_archetype_label(btn, p)

        desc = document.createElement("p")
        desc.className = "archetype-card__desc"
        desc.innerText = p.description
        btn.appendChild(desc)

        subs = document.createElement("p")
        subs.className = "archetype-card__subs-preview"
        subs.innerText = " · ".join(s.label for s in p.sub_archetypes)
        btn.appendChild(subs)

        def pick(e, aid=p.id):
            app.state["arch"] = aid
            profile = get_archetype(aid)
            if profile.sub_archetypes:
                app.state["sub"] = profile.sub_archetypes[0].id
            app._finish_step("archetype")
            app._render()

        btn.onclick = pick
        grid.appendChild(btn)
    el.appendChild(grid)
    return el


def render_sub_archetype(app: WizardApp) -> Any:
    el = document.createElement("div")
    copy = app.system.get_wizard_copy()
    profile = get_archetype(app.state["arch"])

    intro = document.createElement("p")
    intro.className = "text-stone-400 mb-4"
    intro.innerText = copy.get("sub_archetype_intro", "")
    el.appendChild(intro)

    picked = document.createElement("p")
    picked.className = "text-stone-500 text-sm mb-4"
    picked.innerText = archetype_display_label(profile)
    el.appendChild(picked)

    grid = document.createElement("div")
    grid.className = "sub-archetype-grid"
    for s in profile.sub_archetypes:
        btn = document.createElement("button")
        active = app.state["sub"] == s.id
        btn.className = f"archetype-card archetype-card--pickable {'archetype-card--active' if active else ''}"
        btn.setAttribute("type", "button")

        label = document.createElement("span")
        label.className = "archetype-card__label"
        label.innerText = s.label
        btn.appendChild(label)

        if s.description:
            desc = document.createElement("p")
            desc.className = "archetype-card__desc"
            desc.innerText = s.description
            btn.appendChild(desc)

        def pick(e, sid=s.id):
            app.state["sub"] = sid
            app._finish_step("sub_archetype")
            app._render()

        btn.onclick = pick
        grid.appendChild(btn)
    el.appendChild(grid)
    return el
