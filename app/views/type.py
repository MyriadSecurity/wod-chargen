"""Character type wizard step."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pyscript import document

if TYPE_CHECKING:
    from app.wizard import WizardApp


def render_type(app: WizardApp) -> Any:
    el = document.createElement("div")
    copy = app.system.get_wizard_copy()
    random_wrap = document.createElement("label")
    random_wrap.className = "card p-4 mb-4 flex items-start gap-3 cursor-pointer"
    random_cb = document.createElement("input")
    random_cb.type = "checkbox"
    random_cb.className = "mt-1"
    random_cb.checked = bool(app.state.get("full_random"))

    def on_random_toggle(_=None):
        app.state["full_random"] = bool(random_cb.checked)

    random_cb.onchange = on_random_toggle
    random_wrap.appendChild(random_cb)
    random_text = document.createElement("div")
    random_title = document.createElement("div")
    random_title.className = "font-semibold"
    random_title.innerText = copy.get("full_random_label", "Full random")
    random_hint = document.createElement("p")
    random_hint.className = "text-stone-400 text-sm mt-1"
    random_hint.innerText = copy.get(
        "full_random_hint",
        "Skip the build steps — randomly pick clan, archetype, subtype, and predator type, then generate.",
    )
    random_text.appendChild(random_title)
    random_text.appendChild(random_hint)
    random_wrap.appendChild(random_text)
    el.appendChild(random_wrap)

    grid = document.createElement("div")
    grid.className = "wizard-type-grid"
    for entry in app.system.get_character_type_picker():
        tid = entry["id"]
        btn = document.createElement("button")
        btn.type = "button"
        active = app.state["type"] == tid
        btn.className = f"wizard-type-card {'wizard-type-card--active' if active else ''}"

        label_el = document.createElement("span")
        label_el.className = "wizard-type-card__label"
        label_el.innerText = entry["label"]
        btn.appendChild(label_el)
        summary = entry.get("summary")
        if summary:
            summary_el = document.createElement("p")
            summary_el.className = "wizard-type-card__summary"
            summary_el.innerText = summary
            btn.appendChild(summary_el)

        def pick(e, t=tid):
            if app.state.get("full_random"):
                app._apply_full_random(t)
                app._generate()
                if app.state.get("result"):
                    app._goto_results()
                else:
                    app.state["phase"] = "build"
                    app.state["unlocked_through"] = "generate"
            else:
                app._on_type_selected(t)
            app._render()

        btn.onclick = pick
        grid.appendChild(btn)
    el.appendChild(grid)
    return el
