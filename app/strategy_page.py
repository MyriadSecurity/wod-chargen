"""Creation & weighting strategy reference page."""

from __future__ import annotations

import html
import re
from typing import Any
from urllib.parse import quote

from pyscript import document, window
from pyscript.ffi import create_proxy

from app.components.footer import dark_pack_footer
from app.nav import _nav_click, app_nav
from app.strategy_content import (
    STRATEGY_BLURB,
    STRATEGY_PAGE_TITLE,
    STRATEGY_TABS,
    strategy_sections,
)

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
        self.state: dict[str, str] = {"tab": "overview"}
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

    def _sync_hash(self) -> None:
        fragment = f"strategy?tab={quote(self.state['tab'])}"
        path = f"{window.location.pathname}{window.location.search}#{fragment}"
        window.history.replaceState(None, "", path)

    def mount(self) -> None:
        self._render()

    def _render(self) -> None:
        self.root.innerHTML = ""
        self.root.appendChild(app_nav("strategy"))

        wrap = document.createElement("div")
        wrap.className = "strategy-page mx-auto w-full px-4 py-6 max-w-4xl"

        header = document.createElement("div")
        header.className = "mb-4"
        h1 = document.createElement("h1")
        h1.className = "text-2xl font-bold text-blood"
        h1.innerText = STRATEGY_PAGE_TITLE
        header.appendChild(h1)
        blurb = document.createElement("p")
        blurb.className = "text-stone-400 text-sm mt-2"
        blurb.innerText = STRATEGY_BLURB
        header.appendChild(blurb)
        wrap.appendChild(header)

        wrap.appendChild(self._tabs())
        wrap.appendChild(self._body())
        self.root.appendChild(wrap)
        dark_pack_footer()

    def _tabs(self) -> Any:
        bar = document.createElement("div")
        bar.className = "strategy-tabs"
        for tab_id, label in STRATEGY_TABS:

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

    def _body(self) -> Any:
        body = document.createElement("div")
        body.className = "strategy-body"
        sections = strategy_sections().get(self.state["tab"], [])
        if not sections:
            self.state["tab"] = "overview"
            sections = strategy_sections()["overview"]
        for block in sections:
            body.appendChild(self._section(block))
        return body

    def _section(self, block: dict[str, Any]) -> Any:
        sec = document.createElement("section")
        sec.className = "strategy-section"

        h2 = document.createElement("h2")
        h2.innerText = block["title"]
        sec.appendChild(h2)

        for para in block.get("paragraphs", []):
            p = document.createElement("p")
            _set_rich_text(p, para)
            sec.appendChild(p)

        for spec in block.get("formulas", []):
            sec.appendChild(self._formula(spec))

        if block.get("code") and not block.get("formulas"):
            sec.appendChild(self._formula({"caption": "Formula", "body": block["code"]}))

        if block.get("bullets"):
            ul = document.createElement("ul")
            for item in block["bullets"]:
                li = document.createElement("li")
                _set_rich_text(li, item)
                ul.appendChild(li)
            sec.appendChild(ul)

        if block.get("steps"):
            ol = document.createElement("ol")
            for item in block["steps"]:
                li = document.createElement("li")
                _set_rich_text(li, item)
                ol.appendChild(li)
            sec.appendChild(ol)

        table_spec = block.get("table")
        if table_spec:
            sec.appendChild(self._table(table_spec))

        link = block.get("link")
        if link:
            a = document.createElement("a")
            a.href = f"#{link['page']}"
            a.className = "strategy-inline-link"
            a.innerText = link["label"] + " →"

            def on_nav(_=None, page=link["page"]):
                _nav_click(page, _)

            a.onclick = create_proxy(on_nav)
            sec.appendChild(a)

        return sec

    def _formula(self, spec: dict[str, Any]) -> Any:
        wrap = document.createElement("div")
        wrap.className = "strategy-formula"
        caption = spec.get("caption") or "Formula"
        label = document.createElement("p")
        label.className = "strategy-formula-caption"
        label.innerText = caption
        wrap.appendChild(label)
        pre = document.createElement("pre")
        pre.className = "strategy-code"
        pre.innerText = spec["body"]
        wrap.appendChild(pre)
        return wrap

    def _table(self, spec: dict[str, Any]) -> Any:
        wrap = document.createElement("div")
        wrap.className = "strategy-table-wrap"
        table = document.createElement("table")
        table.className = "strategy-table"
        thead = document.createElement("thead")
        head_row = document.createElement("tr")
        for col in spec["headers"]:
            th = document.createElement("th")
            th.innerText = col
            head_row.appendChild(th)
        thead.appendChild(head_row)
        table.appendChild(thead)
        tbody = document.createElement("tbody")
        for row in spec["rows"]:
            tr = document.createElement("tr")
            for cell in row:
                td = document.createElement("td")
                _set_rich_text(td, cell)
                tr.appendChild(td)
            tbody.appendChild(tr)
        table.appendChild(tbody)
        wrap.appendChild(table)
        return wrap
