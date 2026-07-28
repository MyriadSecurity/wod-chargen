"""SPI wizard picker steps (division, faction, archetype, affinity)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pyscript import document

if TYPE_CHECKING:
    from app.wizard import WizardApp


def _option_list(app: WizardApp, options: list[dict[str, str]], state_key: str, step: str) -> Any:
    el = document.createElement("div")
    for opt in options:
        oid = opt["id"]
        btn = document.createElement("button")
        btn.type = "button"
        selected = app.state.get(state_key) == oid
        btn.className = f"card p-4 w-full text-left mb-3 {'card--selected' if selected else ''}"
        title = document.createElement("div")
        title.className = "font-semibold"
        title.innerText = opt.get("label", oid)
        btn.appendChild(title)
        desc = opt.get("description") or ""
        if desc:
            p = document.createElement("p")
            p.className = "text-stone-400 text-sm mt-1"
            p.innerText = desc
            btn.appendChild(p)

        def pick(_=None, value=oid):
            app.state[state_key] = value
            app._finish_step(step)
            app._render()

        btn.onclick = pick
        el.appendChild(btn)
    return el


def render_division(app: WizardApp) -> Any:
    return _option_list(app, app.system.get_division_options(), "division", "division")


def render_faction(app: WizardApp) -> Any:
    return _option_list(app, app.system.get_faction_options(), "faction", "faction")


def render_archetype(app: WizardApp) -> Any:
    """Primary archetype cards with subtype preview; defaults sub to first listed."""
    el = document.createElement("div")
    el.className = "archetype-grid"
    for opt in app.system.get_archetypes():
        oid = opt["id"]
        btn = document.createElement("button")
        btn.type = "button"
        selected = app.state.get("archetype") == oid
        btn.className = (
            f"archetype-card archetype-card--pickable "
            f"{'archetype-card--active' if selected else ''}"
        )

        title = document.createElement("span")
        title.className = "archetype-card__label"
        title.innerText = opt.get("label", oid)
        btn.appendChild(title)

        desc = opt.get("description") or ""
        if desc:
            p = document.createElement("p")
            p.className = "archetype-card__desc"
            p.innerText = desc
            btn.appendChild(p)

        subs = opt.get("sub_archetypes") or []
        if subs:
            preview = document.createElement("p")
            preview.className = "archetype-card__subs-preview"
            preview.innerText = " · ".join(s.get("label", s["id"]) for s in subs)
            btn.appendChild(preview)

        def pick(_=None, value=oid, subtypes=subs):
            app.state["archetype"] = value
            if subtypes:
                app.state["sub"] = subtypes[0]["id"]
            app._finish_step("archetype")
            app._render()

        btn.onclick = pick
        el.appendChild(btn)
    return el


def render_sub_archetype(app: WizardApp) -> Any:
    arch_id = str(app.state.get("archetype") or "investigator")
    options = app.system.get_sub_archetypes(arch_id)
    return _option_list(app, options, "sub", "sub_archetype")


def render_affinity(app: WizardApp) -> Any:
    return _option_list(app, app.system.get_affinity_options(), "affinity", "affinity")


def render_generate_options(app: WizardApp) -> Any:
    """Multi-affinity toggle + seed/generate (SPI generate strip extras)."""
    from app.views import generate as generate_view

    el = document.createElement("div")
    copy = app.system.get_wizard_copy()

    toggle_wrap = document.createElement("label")
    toggle_wrap.className = "flex items-center gap-2 mb-4 text-stone-300 cursor-pointer"
    checkbox = document.createElement("input")
    checkbox.type = "checkbox"
    checkbox.checked = bool(app.state.get("multi_affinity"))

    def on_toggle(_=None):
        app.state["multi_affinity"] = bool(checkbox.checked)

    checkbox.onchange = on_toggle
    toggle_wrap.appendChild(checkbox)
    text = document.createElement("span")
    text.innerText = copy.get("multi_affinity_label", "Allow multiple Affinities")
    toggle_wrap.appendChild(text)
    el.appendChild(toggle_wrap)
    el.appendChild(generate_view.render_generate(app))
    return el
