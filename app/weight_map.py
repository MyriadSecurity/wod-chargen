"""Weight mind-map explorer — archetypes, feed types, clans, catalogs, categories."""

from __future__ import annotations

import json
from typing import Any
from urllib.parse import quote

from pyscript import document, window

from app.components.footer import dark_pack_footer
from app.nav import app_nav
from app.venue_dispatch import IMPLEMENTED_UI_GAMES, UnknownVenueError, weight_data_for
from wod_chargen.games.registry import load_game_catalog

_MAX_RENDER_ATTEMPTS = 40
_RENDER_RETRY_MS = 100


class WeightMapApp:
    def __init__(self, root: Any) -> None:
        self.root = root
        self.state: dict[str, Any] = {
            "game": "",
            "lens": "archetype",
            "mode": "overview",
            "arch": "diplomat",
            "sub": "silver_tongue",
            "type": "vampire",
            "id": "brujah",
            "predator": "alleycat",
            "clan": "brujah",
            "division": "adventure",
            "faction": "higher_ground",
        }
        self._render_attempts = 0
        self._parse_hash()

    def _data(self):
        return weight_data_for(str(self.state.get("game") or ""))

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
                "game",
                "lens",
                "mode",
                "arch",
                "sub",
                "type",
                "id",
                "predator",
                "clan",
                "division",
                "faction",
            ):
                self.state[key] = val
        game = str(self.state.get("game") or "")
        if game and game in IMPLEMENTED_UI_GAMES:
            try:
                data = weight_data_for(game)
            except UnknownVenueError:
                return
            if self.state["lens"] not in data.LENSES:
                self.state["lens"] = "archetype"
            if game == "spi":
                self._ensure_spi_defaults(data)

    def _sync_hash(self) -> None:
        parts = [f"lens={quote(self.state['lens'])}", f"mode={quote(self.state['mode'])}"]
        if self.state.get("game"):
            parts.insert(0, f"game={quote(self.state['game'])}")
        if self.state["mode"] == "profile":
            if self.state["game"] == "spi":
                if self.state["lens"] == "archetype":
                    parts.append(f"id={quote(self.state.get('id') or self.state['arch'])}")
                elif self.state["lens"] == "combo":
                    parts.extend(
                        [
                            f"arch={quote(self.state['arch'])}",
                            f"division={quote(self.state['division'])}",
                            f"faction={quote(self.state['faction'])}",
                        ]
                    )
                elif self.state["lens"] in ("division", "faction", "affinity"):
                    parts.append(f"id={quote(self.state['id'])}")
            elif self.state["lens"] == "archetype":
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

        if not self.state.get("game"):
            wrap.appendChild(self._venue_picker())
            self.root.appendChild(wrap)
            dark_pack_footer()
            return

        try:
            data = self._data()
        except UnknownVenueError:
            wrap.appendChild(self._unknown_venue_message(str(self.state.get("game"))))
            wrap.appendChild(self._venue_picker())
            self.root.appendChild(wrap)
            dark_pack_footer()
            return

        header = document.createElement("div")
        header.className = "mb-4"
        h1 = document.createElement("h1")
        h1.className = "text-2xl font-bold text-blood"
        h1.innerText = "Weight Map"
        header.appendChild(h1)
        blurb = document.createElement("p")
        blurb.className = "text-stone-400 text-sm mt-2 max-w-3xl"
        if self.state["game"] == "spi":
            blurb.innerText = (
                "Explore SPI bias weights by archetype, Division, Faction, Affinity, and "
                "combined profiles. Values show boosts (green) and suppressions (red). "
                "Click nodes in overview to drill down. Scroll to zoom, drag to pan."
            )
        else:
            blurb.innerText = (
                "Explore procedural bias weights by source: archetypes, predator feed types, clans, "
                "catalog defaults, and trait categories. Use Archetype + feed + clan for the merged "
                "profile the generator applies. Values show boosts (green) and suppressions (red). "
                "Click nodes in overview to drill down. Scroll to zoom, drag to pan."
            )
        header.appendChild(blurb)
        wrap.appendChild(header)

        wrap.appendChild(self._controls(data))
        wrap.appendChild(self._legend())

        canvas = document.createElement("div")
        canvas.id = "weight-map-canvas"
        canvas.className = "weight-map-canvas"
        wrap.appendChild(canvas)

        self.root.appendChild(wrap)
        dark_pack_footer()

        self._render_attempts = 0
        self._draw(canvas)

    def _unknown_venue_message(self, game_id: str) -> Any:
        box = document.createElement("div")
        box.className = "mb-4"
        h1 = document.createElement("h1")
        h1.className = "text-2xl font-bold text-blood mb-2"
        h1.innerText = "Weight Map"
        box.appendChild(h1)
        p = document.createElement("p")
        p.className = "text-red-400 text-sm mb-2"
        p.innerText = f"Unknown Venue {game_id!r}. Pick an implemented Venue below."
        box.appendChild(p)
        return box

    def _venue_picker(self) -> Any:
        from pyscript.ffi import create_proxy

        box = document.createElement("div")
        h1 = document.createElement("h1")
        h1.className = "text-2xl font-bold text-blood mb-2"
        h1.innerText = "Weight Map"
        box.appendChild(h1)
        p = document.createElement("p")
        p.className = "text-stone-400 mb-4"
        p.innerText = "Choose a Venue to explore its weight map."
        box.appendChild(p)
        catalog = load_game_catalog()
        for gid, game in catalog.items():
            if not game.get("implemented") or gid not in IMPLEMENTED_UI_GAMES:
                continue
            btn = document.createElement("button")
            btn.type = "button"
            btn.className = "card p-4 w-full text-left mb-3"

            def pick(_=None, game_id=gid):
                self.state["game"] = game_id
                if game_id == "spi":
                    self.state["lens"] = "archetype"
                    self.state["mode"] = "overview"
                    self._ensure_spi_defaults(weight_data_for("spi"))
                self._sync_hash()
                self._render()

            btn.innerHTML = (
                f"<div class='font-semibold'>{game['label']}</div>"
                f"<p class='text-stone-400 text-sm mt-1'>{game['tagline']}</p>"
            )
            btn.onclick = create_proxy(pick)
            box.appendChild(btn)
        return box

    def _controls(self, data: Any) -> Any:
        bar = document.createElement("div")
        bar.className = "weight-map-controls"

        lens_label = document.createElement("label")
        lens_label.innerText = "Source"
        lens_sel = document.createElement("select")

        def on_lens_change(_=None):
            self.state["lens"] = lens_sel.value
            if self.state["lens"] == "catalog":
                self.state["mode"] = "overview"
            if self.state.get("game") == "spi":
                self._ensure_spi_defaults(data)
            self._sync_hash()
            self._render()

        for lens_id, lens_name in data.LENSES.items():
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
                if self.state.get("game") == "spi":
                    self._ensure_spi_defaults(data)
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
            bar.appendChild(self._profile_pickers(data))

        return bar

    def _profile_pickers(self, data: Any) -> Any:
        wrap = document.createElement("div")
        wrap.className = "weight-map-profile-pickers"
        lens = self.state["lens"]

        if self.state.get("game") == "spi":
            if lens in ("archetype", "division", "faction", "affinity"):
                label = document.createElement("label")
                label.innerText = data.LENSES.get(lens, "Profile")
                sel = document.createElement("select")
                options = data.picker_for_lens(lens)
                current = self.state.get("id") or self.state.get("arch")
                for opt in options:
                    o = document.createElement("option")
                    o.value = opt["id"]
                    o.innerText = opt["label"]
                    if o.value == current:
                        o.selected = True
                    sel.appendChild(o)

                def on_id_change(_=None):
                    self.state["id"] = sel.value
                    if lens == "archetype":
                        self.state["arch"] = sel.value
                    self._sync_hash()
                    self._render()

                sel.onchange = on_id_change
                label.appendChild(sel)
                wrap.appendChild(label)
            if lens == "combo":
                for key, lens_name in (
                    ("arch", "archetype"),
                    ("division", "division"),
                    ("faction", "faction"),
                ):
                    label = document.createElement("label")
                    label.innerText = data.LENSES.get(lens_name, key)
                    sel = document.createElement("select")
                    for opt in data.picker_for_lens(lens_name):
                        o = document.createElement("option")
                        o.value = opt["id"]
                        o.innerText = opt["label"]
                        if o.value == self.state.get(key):
                            o.selected = True
                        sel.appendChild(o)

                    def on_change(_=None, state_key=key, select=sel):
                        self.state[state_key] = select.value
                        self._sync_hash()
                        self._render()

                    sel.onchange = on_change
                    label.appendChild(sel)
                    wrap.appendChild(label)
            return wrap

        if lens in ("archetype", "combo"):
            label = document.createElement("label")
            label.innerText = "Archetype"
            sel = document.createElement("select")
            options = data.picker_for_lens("archetype")
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
            for opt in data.predator_picker_options():
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
            for opt in data.picker_for_lens("clan"):
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
            options = data.picker_for_lens(lens)
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

    def _ensure_spi_defaults(self, data: Any) -> None:
        """Replace leftover LotN ids with valid SPI picker values."""
        arch_opts = data.picker_for_lens("archetype")
        default_arch = (
            arch_opts[0]["id"]
            if arch_opts
            else getattr(data, "default_arch_picker_id", lambda: "investigator:detective")()
        )
        arch = str(self.state.get("arch") or "")
        if not arch or ":" not in arch or not any(o["id"] == arch for o in arch_opts):
            # Bare primary id (investigator) or LotN leftover (diplomat without SPI sub).
            if arch and ":" not in arch and any(o["id"].startswith(f"{arch}:") for o in arch_opts):
                self.state["arch"] = next(o["id"] for o in arch_opts if o["id"].startswith(f"{arch}:"))
            else:
                self.state["arch"] = default_arch

        lens = str(self.state.get("lens") or "archetype")
        if lens in ("archetype", "division", "faction", "affinity"):
            opts = data.picker_for_lens(lens)
            valid = {o["id"] for o in opts}
            current = str(self.state.get("id") or "")
            if lens == "archetype":
                if current not in valid:
                    self.state["id"] = self.state["arch"]
            elif current not in valid:
                self.state["id"] = opts[0]["id"] if opts else current

        for key, lens_name, fallback in (
            ("division", "division", "adventure"),
            ("faction", "faction", "higher_ground"),
        ):
            opts = data.picker_for_lens(lens_name)
            valid = {o["id"] for o in opts}
            if str(self.state.get(key) or "") not in valid:
                self.state[key] = opts[0]["id"] if opts else fallback

    def _tree_params(self) -> dict[str, str]:
        return {
            "arch": str(self.state.get("arch", "")),
            "sub": str(self.state.get("sub", "")),
            "type": str(self.state.get("type", "vampire")),
            "id": str(self.state.get("id", "")),
            "predator": str(self.state.get("predator", "")),
            "clan": str(self.state.get("clan", "")),
            "division": str(self.state.get("division", "")),
            "faction": str(self.state.get("faction", "")),
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
            tree = self._data().build_tree(
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
