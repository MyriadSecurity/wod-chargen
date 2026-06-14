"""Venue / starting XP wizard step."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pyscript import document

from app.wizard_state import venue_continue_error

if TYPE_CHECKING:
    from app.wizard import WizardApp


def render_venue(app: WizardApp) -> Any:
    el = document.createElement("div")
    copy = app.system.get_wizard_copy()

    intro = document.createElement("p")
    intro.className = "text-stone-400 mb-4"
    intro.innerText = copy.get(
        "xp_intro",
        "Choose how much experience the character has to spend.",
    )
    el.appendChild(intro)

    for venue in app.system.get_venue_picker():
        vid = venue["id"]
        label = venue["label"]
        btn = document.createElement("button")
        btn.className = f"card p-4 w-full text-left mb-3 {'card--selected' if app.state['venue'] == vid else ''}"

        def pick(e, v=vid):
            app.state["venue"] = v
            app.state["error"] = None
            app._render()

        btn.innerText = label
        btn.onclick = pick
        el.appendChild(btn)

    if app._venue_picker.get(app.state["venue"], {}).get("requires_approval_month"):
        lbl = document.createElement("label")
        lbl.className = "block mt-4 text-stone-400"
        lbl.innerText = "Approval month (YYYY-MM)"
        inp = document.createElement("input")
        inp.type = "text"
        inp.value = app.state["approval"]
        inp.className = "bg-ash border border-stone-700 rounded px-3 py-2 w-full mt-1"

        def on_change(e):
            app.state["approval"] = inp.value

        inp.oninput = on_change
        el.appendChild(lbl)
        el.appendChild(inp)

    xp_inp: Any | None = None
    if app.state.get("venue") == "custom_xp":
        lbl = document.createElement("label")
        lbl.className = "block mt-4 text-stone-400"
        lbl.innerText = copy.get("xp_custom_label", "XP amount")
        xp_inp = document.createElement("input")
        xp_inp.type = "number"
        xp_inp.min = "0"
        xp_inp.step = "1"
        xp_inp.value = str(app.state.get("xp_custom", "100"))
        xp_inp.className = "bg-ash border border-stone-700 rounded px-3 py-2 w-full mt-1"

        def on_xp_change(e):
            app.state["xp_custom"] = xp_inp.value

        xp_inp.oninput = on_xp_change
        el.appendChild(lbl)
        el.appendChild(xp_inp)

    go = document.createElement("button")
    go.className = "btn-primary mt-6"

    def next_step(_=None):
        if xp_inp is not None:
            app.state["xp_custom"] = str(xp_inp.value).strip()
        err = venue_continue_error(app)
        if err:
            app.state["error"] = err
            app._render()
            return
        app.state["error"] = None
        app._finish_step("venue")
        app._render()

    go.innerText = "Continue"
    go.onclick = next_step
    el.appendChild(go)
    return el
