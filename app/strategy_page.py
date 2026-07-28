"""Creation & weighting strategy reference page."""

from __future__ import annotations

import html
import re
from typing import Any
from urllib.parse import quote

from pyscript import document, window
from pyscript.ffi import create_proxy

from app.components.footer import dark_pack_footer
from app.nav import app_nav
from app.strategy_content import resolve_guide
from wod_chargen.games.registry import load_game_catalog

_INLINE_BOLD_RE = re.compile(r"\*\*(.+?)\*\*")


def _inline_html(text: str) -> str:
    """Render **bold** markers in strategy copy as <strong> tags."""
    parts: list[str] = []
    last = 0
    for match in _INLINE_BOLD_RE.finditer(text):
        parts.append(html.escape(text[last : match.start()]))
        parts.append(f"<strong>{html.escape(match.group(1))}</strong>")
        last = match.end()
    parts.append(html.escape(text[last:]))
    return "".join(parts)


def _set_rich_text(element: Any, text: str) -> None:
    if "**" in text:
        element.innerHTML = _inline_html(text)
    else:
        element.innerText = text


class StrategyPageApp:
    def __init__(self, root: Any) -> None:
        self.root = root
        self.state: dict[str, str] = {"tab": "overview", "game": ""}
        self._parse_hash()

    def _parse_hash(self) -> None:
        raw = (window.location.hash or "").lstrip("#")
        if not raw.startswith("strategy"):
            return
        query = raw.split("?", 1)[1] if "?" in raw else ""
        for part in query.split("&"):
            if "=" not in part:
                continue
            key, val = part.split("=", 1)
            if key == "tab" and val:
                self.state["tab"] = val
            elif key == "game" and val:
                self.state["game"] = val

    def _sync_hash(self) -> None:
        parts = [f"tab={quote(self.state['tab'])}"]
        if self.state.get("game"):
            parts.insert(0, f"game={quote(self.state['game'])}")
        fragment = f"strategy?{'&'.join(parts)}"
        path = f"{window.location.pathname}{window.location.search}#{fragment}"
        window.history.replaceState(None, "", path)

    def mount(self) -> None:
        self._render()

    def _render(self) -> None:
        self.root.innerHTML = ""
        self.root.appendChild(app_nav("strategy"))

        wrap = document.createElement("div")
        wrap.className = "strategy-page mx-auto w-full px-4 py-6 max-w-4xl"

        if not self.state.get("game"):
            wrap.appendChild(self._venue_picker())
            self.root.appendChild(wrap)
            dark_pack_footer()
            return

        guide = resolve_guide(self.state["game"])
        header = document.createElement("div")
        header.className = "mb-4"
        h1 = document.createElement("h1")
        h1.className = "text-2xl font-bold text-blood"
        h1.innerText = guide["title"]
        header.appendChild(h1)
        blurb = document.createElement("p")
        blurb.className = "text-stone-400 text-sm mt-2"
        blurb.innerText = guide["blurb"]
        header.appendChild(blurb)
        wrap.appendChild(header)

        wrap.appendChild(self._tabs(guide["tabs"]))
        wrap.appendChild(self._body(guide["sections"]))
        self.root.appendChild(wrap)
        dark_pack_footer()

    def _venue_picker(self) -> Any:
        box = document.createElement("div")
        h1 = document.createElement("h1")
        h1.className = "text-2xl font-bold text-blood mb-2"
        h1.innerText = "Build guide"
        box.appendChild(h1)
        p = document.createElement("p")
        p.className = "text-stone-400 mb-4"
        p.innerText = "Choose a Venue to open its build guide."
        box.appendChild(p)
        catalog = load_game_catalog()
        for gid, game in catalog.items():
            if not game.get("implemented"):
                continue
            btn = document.createElement("button")
            btn.type = "button"
            btn.className = "card p-4 w-full text-left mb-3"

            def pick(_=None, game_id=gid):
                self.state["game"] = game_id
                self.state["tab"] = "overview"
                self._sync_hash()
                self._render()

            btn.innerHTML = (
                f"<div class='font-semibold'>{game['label']}</div>"
                f"<p class='text-stone-400 text-sm mt-1'>{game['tagline']}</p>"
            )
            btn.onclick = create_proxy(pick)
            box.appendChild(btn)
        return box

    def _tabs(self, tabs: tuple[tuple[str, str], ...]) -> Any:
        bar = document.createElement("div")
        bar.className = "strategy-tabs"
        for tab_id, label in tabs:

            def on_click(_=None, tid=tab_id):
                self.state["tab"] = tid
                self._sync_hash()
                self._render()

            btn = document.createElement("button")
            btn.type = "button"
            btn.className = "strategy-tab" + (" active" if self.state["tab"] == tab_id else "")
            btn.innerText = label
            btn.onclick = create_proxy(on_click)
            bar.appendChild(btn)
        return bar

    def _body(self, sections_by_tab: dict[str, list[dict[str, Any]]]) -> Any:
        body = document.createElement("div")
        body.className = "strategy-body"
        sections = sections_by_tab.get(self.state["tab"], [])
        if not sections:
            self.state["tab"] = "overview"
            sections = sections_by_tab["overview"]
        for block in sections:
            body.appendChild(self._section(block))
        return body

    def _section(self, block: dict[str, Any]) -> Any:
        sec = document.createElement("section")
        sec.className = "strategy-section mb-8"
        if block.get("title"):
            h = document.createElement("h2")
            h.className = "text-lg font-semibold text-stone-100 mb-2"
            h.innerText = block["title"]
            sec.appendChild(h)
        for para in block.get("paragraphs", []):
            p = document.createElement("p")
            p.className = "text-stone-300 text-sm mb-2"
            _set_rich_text(p, para)
            sec.appendChild(p)
        if block.get("steps"):
            ol = document.createElement("ol")
            ol.className = "list-decimal ml-5 text-stone-300 text-sm mb-2"
            for step in block["steps"]:
                li = document.createElement("li")
                li.className = "mb-1"
                _set_rich_text(li, step)
                ol.appendChild(li)
            sec.appendChild(ol)
        for formula in block.get("formulas", []):
            fig = document.createElement("figure")
            fig.className = "strategy-formula mb-3"
            if formula.get("caption"):
                cap = document.createElement("figcaption")
                cap.className = "text-stone-400 text-xs mb-1"
                cap.innerText = formula["caption"]
                fig.appendChild(cap)
            pre = document.createElement("pre")
            pre.className = "strategy-formula__body"
            pre.innerText = formula.get("body", "")
            fig.appendChild(pre)
            sec.appendChild(fig)
        table = block.get("table")
        if table:
            tbl = document.createElement("table")
            tbl.className = "strategy-table w-full text-sm mb-2"
            thead = document.createElement("thead")
            tr = document.createElement("tr")
            for h in table.get("headers", []):
                th = document.createElement("th")
                th.innerText = h
                tr.appendChild(th)
            thead.appendChild(tr)
            tbl.appendChild(thead)
            tbody = document.createElement("tbody")
            for row in table.get("rows", []):
                tr = document.createElement("tr")
                for cell in row:
                    td = document.createElement("td")
                    td.innerText = cell
                    tr.appendChild(td)
                tbody.appendChild(tr)
            tbl.appendChild(tbody)
            sec.appendChild(tbl)
        return sec
