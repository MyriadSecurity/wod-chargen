"""Weight mind-map explorer — archetypes, feed types, clans, catalogs, categories."""

from __future__ import annotations

import json
from typing import Any
from urllib.parse import quote

from pyscript import document, window

from app.components.footer import dark_pack_footer
from app.nav import app_nav
from app.weight_map_data import (
    LENSES,
    build_tree,
    picker_for_lens,
    predator_picker_options,
)

_MAX_RENDER_ATTEMPTS = 40
_RENDER_RETRY_MS = 100


class WeightMapApp:
    def __init__(self, root: Any) -> None:
        self.root = root
        self.state: dict[str, Any] = {
            "lens": "archetype",
            "mode": "overview",
            "arch": "diplomat",
            "sub": "silver_tongue",
            "type": "vampire",
            "id": "brujah",
            "predator": "alleycat",
            "clan": "brujah",
        }
        self._render_attempts = 0
        self._parse_hash()

    def _parse_hash(self) -> None:
        raw = (window.location.hash or "").lstrip("#")
        if not raw.startswith("weights"):
            return
        query = raw.split("?", 1)[1] if "?" in raw else ""
        for part in query.split("&"):
            if "=" not in part:
                continue
            key, val = part.split("=", 1)
            if val and key in (
                "lens",
                "mode",
                "arch",
                "sub",
                "type",
                "id",
                "predator",
                "clan",
            ):
                self.state[key] = val

    def _sync_hash(self) -> None:
        parts = [f"lens={quote(self.state['lens'])}", f"mode={quote(self.state['mode'])}"]
        if self.state["mode"] == "profile":
            if self.state["lens"] == "archetype":
                parts.extend(
                    [
                        f"arch={quote(self.state['arch'])}",
                        f"sub={quote(self.state['sub'])}",
                        f"type={quote(self.state['type'])}",
                    ]
                )
            elif self.state["lens"] == "combo":
                parts.extend(
                    [
                        f"arch={quote(self.state['arch'])}",
                        f"sub={quote(self.state['sub'])}",
                        f"type={quote(self.state['type'])}",
                        f"predator={quote(self.state['predator'])}",
                        f"clan={quote(self.state['clan'])}",
                    ]
                )
            elif self.state["lens"] in ("predator", "clan", "category"):
                parts.append(f"id={quote(self.state['id'])}")
        fragment = f"weights?{'&'.join(parts)}"
        path = f"{window.location.pathname}{window.location.search}#{fragment}"
        window.history.replaceState(None, "", path)

    def mount(self) -> None:
        self._render()

    def _render(self) -> None:
        self.root.innerHTML = ""
        self.root.appendChild(app_nav("weights"))

        wrap = document.createElement("div")
        wrap.className = "weight-map-page mx-auto w-full px-4 py-6 max-w-6xl"

        header = document.createElement("div")
        header.className = "mb-4"
        h1 = document.createElement("h1")
        h1.className = "text-2xl font-bold text-blood"
        h1.innerText = "Generation weight map"
        header.appendChild(h1)
        blurb = document.createElement("p")
        blurb.className = "text-stone-400 text-sm mt-2 max-w-3xl"
        blurb.innerText = (
            "Explore procedural bias weights by source: archetypes, predator feed types, clans, "
            "catalog defaults, and trait categories. Use Archetype + feed + clan for the merged "
            "profile the generator applies. Values show boosts (green) and suppressions (red). "
            "Click nodes in overview to drill down. Scroll to zoom, drag to pan."
        )
        header.appendChild(blurb)
        wrap.appendChild(header)

        wrap.appendChild(self._controls())
        wrap.appendChild(self._legend())

        canvas = document.createElement("div")
        canvas.id = "weight-map-canvas"
        canvas.className = "weight-map-canvas"
        wrap.appendChild(canvas)

        self.root.appendChild(wrap)
        dark_pack_footer()

        self._render_attempts = 0
        self._draw(canvas)

    def _controls(self) -> Any:
        bar = document.createElement("div")
        bar.className = "weight-map-controls"

        lens_label = document.createElement("label")
        lens_label.innerText = "Source"
        lens_sel = document.createElement("select")

        def on_lens_change(_=None):
            self.state["lens"] = lens_sel.value
            if self.state["lens"] == "catalog":
                self.state["mode"] = "overview"
            self._sync_hash()
            self._render()

        for lens_id, lens_name in LENSES.items():
            o = document.createElement("option")
            o.value = lens_id
            o.innerText = lens_name
            if lens_id == self.state["lens"]:
                o.selected = True
            lens_sel.appendChild(o)
        lens_sel.onchange = on_lens_change
        lens_label.appendChild(lens_sel)
        bar.appendChild(lens_label)

        tabs = document.createElement("div")
        tabs.className = "weight-map-tabs"
        lens = self.state["lens"]

        if lens != "catalog":

            def set_mode(mode: str) -> None:
                self.state["mode"] = mode
                self._sync_hash()
                self._render()

            for mode, label in (("overview", "Overview"), ("profile", "Single profile")):
                btn = document.createElement("button")
                btn.type = "button"
                btn.className = "weight-map-tab" + (" active" if self.state["mode"] == mode else "")
                btn.innerText = label

                def on_click(_=None, m=mode):
                    set_mode(m)

                btn.onclick = on_click
                tabs.appendChild(btn)
        bar.appendChild(tabs)

        if self.state["mode"] == "profile" and lens != "catalog":
            bar.appendChild(self._profile_pickers())

        return bar

    def _profile_pickers(self) -> Any:
        wrap = document.createElement("div")
        wrap.className = "weight-map-profile-pickers"
        lens = self.state["lens"]

        if lens in ("archetype", "combo"):
            label = document.createElement("label")
            label.innerText = "Archetype"
            sel = document.createElement("select")
            options = picker_for_lens("archetype")
            current = f"{self.state['arch']}:{self.state['sub']}"
            for opt in options:
                o = document.createElement("option")
                o.value = opt["id"]
                o.innerText = opt["label"]
                if o.value == current:
                    o.selected = True
                sel.appendChild(o)

            def on_arch_change(_=None):
                arch, sub = sel.value.split(":", 1)
                self.state["arch"] = arch
                self.state["sub"] = sub
                match = next(x for x in options if x["arch"] == arch and x["sub"] == sub)
                self.state["type"] = match["type"]
                self._sync_hash()
                self._render()

            sel.onchange = on_arch_change
            label.appendChild(sel)
            wrap.appendChild(label)

        if lens == "combo":
            plabel = document.createElement("label")
            plabel.innerText = "Feed type"
            psel = document.createElement("select")
            for opt in predator_picker_options():
                o = document.createElement("option")
                o.value = opt["id"]
                o.innerText = opt["label"]
                if o.value == self.state["predator"]:
                    o.selected = True
                psel.appendChild(o)

            def on_pred_change(_=None):
                self.state["predator"] = psel.value
                self._sync_hash()
                self._render()

            psel.onchange = on_pred_change
            plabel.appendChild(psel)
            wrap.appendChild(plabel)

            clabel = document.createElement("label")
            clabel.innerText = "Domitor clan" if self.state.get("type") == "ghoul" else "Clan"
            csel = document.createElement("select")
            for opt in picker_for_lens("clan"):
                o = document.createElement("option")
                o.value = opt["id"]
                o.innerText = opt["label"]
                if o.value == self.state["clan"]:
                    o.selected = True
                csel.appendChild(o)

            def on_clan_change(_=None):
                self.state["clan"] = csel.value
                self._sync_hash()
                self._render()

            csel.onchange = on_clan_change
            clabel.appendChild(csel)
            wrap.appendChild(clabel)

        if lens in ("predator", "clan", "category"):
            label = document.createElement("label")
            labels = {"predator": "Feed type", "clan": "Clan", "category": "Category"}
            label.innerText = labels.get(lens, "Profile")
            sel = document.createElement("select")
            options = picker_for_lens(lens)
            for opt in options:
                o = document.createElement("option")
                o.value = opt["id"]
                o.innerText = opt["label"]
                if o.value == self.state["id"]:
                    o.selected = True
                sel.appendChild(o)

            def on_id_change(_=None):
                self.state["id"] = sel.value
                self._sync_hash()
                self._render()

            sel.onchange = on_id_change
            label.appendChild(sel)
            wrap.appendChild(label)

        return wrap

    def _legend(self) -> Any:
        leg = document.createElement("div")
        leg.className = "weight-map-legend"
        leg.innerHTML = (
            "<span><i style='background:#4ade80'></i> Strong boost (≥1.35)</span>"
            "<span><i style='background:#a3e635'></i> Mild boost</span>"
            "<span><i style='background:#9ca3af'></i> Neutral (~1.0)</span>"
            "<span><i style='background:#fb923c'></i> Soft oppose</span>"
            "<span><i style='background:#ef4444'></i> Hard suppress</span>"
        )
        return leg

    def _tree_params(self) -> dict[str, str]:
        return {
            "arch": str(self.state.get("arch", "")),
            "sub": str(self.state.get("sub", "")),
            "type": str(self.state.get("type", "vampire")),
            "id": str(self.state.get("id", "")),
            "predator": str(self.state.get("predator", "")),
            "clan": str(self.state.get("clan", "")),
        }

    def _show_draw_error(self, canvas: Any, message: str) -> None:
        canvas.innerHTML = ""
        box = document.createElement("div")
        box.className = "weight-map-error"
        box.innerText = message
        canvas.appendChild(box)

    def _assets_ready(self) -> bool:
        if hasattr(window, "weightMapAssetsReady"):
            return bool(window.weightMapAssetsReady())
        return hasattr(window, "renderWeightMap") and hasattr(window, "d3")

    def _draw(self, canvas: Any) -> None:
        if self._render_attempts >= _MAX_RENDER_ATTEMPTS:
            self._show_draw_error(
                canvas,
                "Could not load the weight map renderer (D3). Reload the page or check your network.",
            )
            return

        self._render_attempts += 1

        if not self._assets_ready():
            window.setTimeout(lambda: self._draw(canvas), _RENDER_RETRY_MS)
            return

        try:
            tree = build_tree(
                self.state["lens"],
                self.state["mode"],
                **self._tree_params(),
            )
            payload = json.dumps(tree)
            ok = window.renderWeightMap(canvas, payload)
            if ok is False:
                self._show_draw_error(canvas, "Weight map renderer returned an error.")
        except Exception as exc:
            self._show_draw_error(canvas, f"Weight map failed to render: {exc}")
