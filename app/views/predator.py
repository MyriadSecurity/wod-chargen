"""Predator type wizard step."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pyscript import document

if TYPE_CHECKING:
    from app.wizard import WizardApp


def append_card_list(parent: Any, title: str, items: list[str], item_class: str) -> None:
    if not items:
        return
    heading = document.createElement("div")
    heading.className = "predator-card__section-title"
    heading.innerText = title
    parent.appendChild(heading)
    ul = document.createElement("ul")
    ul.className = "predator-card__list"
    for text in items:
        li = document.createElement("li")
        li.className = item_class
        li.innerText = text
        ul.appendChild(li)
    parent.appendChild(ul)


def render_predator(app: WizardApp) -> Any:
    el = document.createElement("div")
    copy = app.system.get_wizard_copy()

    intro = document.createElement("p")
    intro.className = "text-stone-400 mb-4"
    intro.innerText = copy.get("predator_intro", "")
    el.appendChild(intro)

    picker = app.system.get_predator_picker()
    grid = document.createElement("div")
    grid.className = "predator-grid"
    selected = app.state.get("predator") or picker[0]["id"]
    for entry in picker:
        pid = entry["id"]
        btn = document.createElement("button")
        btn.className = (
            "archetype-card archetype-card--pickable predator-card "
            f"{'archetype-card--active' if selected == pid else ''}"
        )
        btn.setAttribute("type", "button")

        label = document.createElement("span")
        label.className = "archetype-card__label"
        label.innerText = entry["label"]
        btn.appendChild(label)

        if entry.get("summary"):
            desc = document.createElement("p")
            desc.className = "archetype-card__desc"
            desc.innerText = entry["summary"]
            btn.appendChild(desc)

        pool = entry.get("feeding_pool")
        if pool:
            pool_block = document.createElement("div")
            pool_block.className = "predator-card__pool-block"
            pool_title = document.createElement("div")
            pool_title.className = "predator-card__section-title"
            pool_title.innerText = "Feeding pool"
            pool_value = document.createElement("div")
            pool_value.className = "predator-card__pool"
            pool_value.innerText = pool
            pool_block.appendChild(pool_title)
            pool_block.appendChild(pool_value)
            btn.appendChild(pool_block)

        append_card_list(btn, "Benefits", entry.get("benefits", []), "predator-card__benefit")
        append_card_list(btn, "Restrictions", entry.get("restrictions", []), "predator-card__restriction")
        append_card_list(btn, "Drawbacks", entry.get("drawbacks", []), "predator-card__drawback")

        def pick(e, p=pid):
            app.state["predator"] = p
            app._finish_step("predator")
            app._render()

        btn.onclick = pick
        grid.appendChild(btn)
    el.appendChild(grid)
    return el
