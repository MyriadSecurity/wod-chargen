"""Faction / lineage wizard step."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pyscript import document

from app.formatting import format_disciplines
from wod_chargen.games.lotn_v5.archetypes import archetypes_for_type

if TYPE_CHECKING:
    from app.wizard import WizardApp


def faction_role(app: WizardApp) -> str:
    return "ghoul" if app.state["type"] == "ghoul" else "vampire"


def render_faction(app: WizardApp) -> Any:
    el = document.createElement("div")
    role = faction_role(app)
    options = app.system.get_faction_options(role)
    clan_key = "clan" if role == "vampire" else "domitor_clan"

    grid = document.createElement("div")
    grid.className = "clan-grid"
    for c in options:
        btn = document.createElement("button")
        is_thin = c.get("kind") == "thin_blood"
        if is_thin:
            active = app.state["type"] == "thin_blood"
        else:
            active = app.state["type"] != "thin_blood" and app.state[clan_key] == c["id"]
        btn.className = f"clan-card {'clan-card--active' if active else ''}"
        btn.setAttribute("type", "button")
        btn.setAttribute("aria-label", c["label"])
        btn.setAttribute("aria-pressed", "true" if active else "false")

        img = document.createElement("img")
        img.src = c["symbol"]
        img.alt = ""
        img.className = "clan-card__symbol"
        img.setAttribute("aria-hidden", "true")
        btn.appendChild(img)

        label = document.createElement("span")
        label.className = "clan-card__label"
        label.innerText = c["label"]
        btn.appendChild(label)

        desc = document.createElement("p")
        desc.className = "clan-card__desc"
        desc.innerText = c["description"]
        btn.appendChild(desc)

        discs = document.createElement("p")
        discs.className = "clan-card__disciplines"
        discs.innerText = format_disciplines(c)
        btn.appendChild(discs)

        def pick(e, entry=c, k=clan_key, r=role):
            if entry.get("kind") == "thin_blood":
                app.state["type"] = "thin_blood"
                profiles = archetypes_for_type("thin_blood")
                if profiles:
                    app.state["arch"] = profiles[0].id
                    app.state["sub"] = profiles[0].sub_archetypes[0].id
            else:
                app.state["type"] = r
                app.state[k] = entry["id"]
            app._finish_step("faction")
            app._render()

        btn.onclick = pick
        grid.appendChild(btn)
    el.appendChild(grid)
    return el
