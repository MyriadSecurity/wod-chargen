"""Shared app navigation."""

from __future__ import annotations

from typing import Any

from pyscript import document, window
from pyscript.ffi import create_proxy


def _nav_click(page: str, event: Any = None) -> None:
    if event is not None:
        event.preventDefault()
    navigate = getattr(window, "wodAppNavigate", None)
    if navigate is not None:
        navigate(page)
    elif page == "weights":
        window.location.hash = "weights"
    else:
        window.location.hash = ""


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
        link.onclick = create_proxy(lambda e, p=key: _nav_click(p, e))
        nav.appendChild(link)

    return nav
