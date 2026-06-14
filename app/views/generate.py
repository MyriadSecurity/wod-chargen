"""Generate character wizard step."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pyscript import document

if TYPE_CHECKING:
    from app.wizard import WizardApp


def render_generate(app: WizardApp) -> Any:
    el = document.createElement("div")
    seed_lbl = document.createElement("label")
    seed_lbl.className = "block text-stone-400"
    seed_lbl.innerText = "Seed (reproducible)"
    seed_inp = document.createElement("input")
    seed_inp.type = "number"
    seed_inp.value = str(app.state["seed"])
    seed_inp.className = "bg-ash border border-stone-700 rounded px-3 py-2 w-full mt-1 mb-4"

    def on_seed(e):
        app.state["seed"] = int(seed_inp.value or 0)

    seed_inp.oninput = on_seed
    el.appendChild(seed_lbl)
    el.appendChild(seed_inp)

    gen = document.createElement("button")
    gen.className = "btn-primary"

    def do_gen(_=None):
        try:
            app.state["seed"] = int(seed_inp.value) if str(seed_inp.value).strip() else int(app.state["seed"])
        except (ValueError, TypeError):
            app.state["error"] = "Enter a valid numeric seed."
            app._render()
            return
        app._generate()
        if app.state.get("result"):
            app._goto_results()
        app._render()

    gen.innerText = "Generate character"
    gen.onclick = do_gen
    el.appendChild(gen)

    if app.state.get("error"):
        err = document.createElement("p")
        err.className = "text-red-400 mt-4"
        err.innerText = app.state["error"]
        el.appendChild(err)
    return el
