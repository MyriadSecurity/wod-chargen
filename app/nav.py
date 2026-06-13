"""Shared app navigation."""

from __future__ import annotations

from typing import Any

from pyscript import document


def app_nav(active: str) -> Any:
    """Top nav: generator vs weight map. active is 'generator' or 'weights'."""
    nav = document.createElement("nav")
    nav.className = "app-nav max-w-6xl mx-auto px-4 pt-4"

    for href, label, key in (
        ("#", "Character generator", "generator"),
        ("#weights", "Archetype weight map", "weights"),
    ):
        link = document.createElement("a")
        link.href = href
        link.innerText = label
        if key == active:
            link.className = "active"
        nav.appendChild(link)

    return nav
