"""Multi-step creation wizard."""

from __future__ import annotations

import json
import random
from typing import Any

from pyscript import document, window

from app.components.footer import dark_pack_footer
from app.components.sheet import render_lotn_v5_sheet
from app.nav import app_nav
from wod_chargen.core.xp_log_format import format_xp_log
from wod_chargen.core.share import (
    SharePayload,
    browser_share_url,
    decode_query,
    wizard_share_options,
)
from wod_chargen.core.data_loader import load_json_cached
from wod_chargen.games.lotn_v5.archetypes import archetypes_for_type, get_archetype
from wod_chargen.games.lotn_v5.convictions import pick_convictions
from wod_chargen.games.lotn_v5.generator import generate_character
from wod_chargen.games.lotn_v5.system import LotnV5System
from wod_chargen.games.registry import load_game_catalog
from wod_chargen.venues import load_venue


def _format_disciplines(entry: dict[str, Any]) -> str:
    if entry.get("discipline_note"):
        return entry["discipline_note"]
    discipline_ids = entry.get("disciplines", [])
    if not discipline_ids:
        return "No in-clan disciplines"
    return " · ".join(d.replace("_", " ").title() for d in discipline_ids)


class WizardApp:
    def __init__(self, root) -> None:
        self.root = root
        self.system = LotnV5System()
        self._venue_picker = {v["id"]: v for v in self.system.get_venue_picker()}
        self.state: dict[str, Any] = {
            "game": "lotn_v5",
            "type": "vampire",
            "clan": "brujah",
            "domitor_clan": "tremere",
            "arch": "diplomat",
            "sub": "silver_tongue",
            "predator": "",
            "venue": "mes_end_to_dawn",
            "approval": "2026-06",
            "seed": random.randint(1, 999_999),
            "convictions_seed": random.randint(1, 999_999),
            "step": "game",
            "result": None,
            "error": None,
            "tab": "sheet",
        }
        self._parse_url()

    def _parse_url(self) -> None:
        try:
            qs = window.location.search
            if not qs:
                return
            payload = decode_query(qs)
            self.state["seed"] = payload.seed
            if payload.convictions_seed is not None:
                self.state["convictions_seed"] = payload.convictions_seed
            self.state["game"] = payload.game
            self.state["venue"] = payload.venue
            opts = payload.options
            for key in ("type", "clan", "domitor_clan", "arch", "sub", "predator", "approval"):
                if key in opts:
                    self.state[key] = opts[key]
            self._validate_selection()
            self._generate()
            self.state["step"] = "results" if self.state.get("result") else "generate"
        except Exception as exc:
            self.state["error"] = str(exc)
            self.state["step"] = "game"

    def _type_uses_predator(self) -> bool:
        return self.system.type_uses_predator(self.state["type"])

    def _options(self) -> dict[str, str]:
        return wizard_share_options(
            character_type=self.state["type"],
            arch=self.state["arch"],
            sub=self.state["sub"],
            clan=self.state.get("clan", ""),
            domitor_clan=self.state.get("domitor_clan", ""),
            predator=self.state.get("predator", ""),
            approval=self.state.get("approval", ""),
            venue_requires_approval_month=bool(
                self._venue_picker.get(self.state["venue"], {}).get("requires_approval_month")
            ),
            type_uses_predator=self._type_uses_predator(),
        )

    def _share_payload(self) -> SharePayload:
        return SharePayload(
            seed=int(self.state["seed"]),
            convictions_seed=int(self.state["convictions_seed"]),
            game=self.state["game"],
            venue=self.state["venue"],
            options=self._options(),
        )

    def _convictions(self) -> list[dict[str, str]]:
        return pick_convictions(int(self.state["convictions_seed"]))

    def _reroll_convictions(self, _=None) -> None:
        self.state["convictions_seed"] = random.randint(1, 999_999)
        try:
            self._sync_url()
        except Exception:
            pass
        self._render()

    def _share_url(self) -> str:
        return browser_share_url(window.location.pathname, self._share_payload())

    def _sync_url(self) -> None:
        window.history.replaceState(None, "", self._share_url())

    def _validate_selection(self) -> None:
        """Ensure arch/sub still exist after data changes or stale share URLs."""
        profiles = archetypes_for_type(self.state["type"])
        valid_arch = {p.id for p in profiles}
        if self.state["arch"] not in valid_arch:
            self.state["arch"] = profiles[0].id
        profile = get_archetype(self.state["arch"])
        valid_sub = {s.id for s in profile.sub_archetypes}
        if self.state["sub"] not in valid_sub:
            self.state["sub"] = profile.sub_archetypes[0].id
        if self._type_uses_predator():
            valid_pred = {p["id"] for p in self.system.get_predator_picker()}
            pred = self.state.get("predator") or ""
            if pred and pred not in valid_pred:
                self.state["predator"] = self.system.get_predator_picker()[0]["id"]

    def _generate(self) -> None:
        import traceback

        try:
            self._validate_selection()
            venue = load_venue(self.state["venue"])
            result = generate_character(
                int(self.state["seed"]),
                self._options(),
                venue,
            )
            self.state["result"] = result
            self.state["error"] = None
            try:
                self._sync_url()
            except Exception as sync_exc:
                self.state["error"] = f"Share URL sync failed: {sync_exc}"
        except Exception as exc:
            self.state["error"] = f"{exc}\n\n{traceback.format_exc()}"
            self.state["result"] = None

    def mount(self) -> None:
        self._render()

    def _render(self) -> None:
        self.root.innerHTML = ""
        self.root.appendChild(app_nav("generator"))
        step = self.state["step"]
        container = document.createElement("div")
        container.className = "flex-1 mx-auto w-full px-4 py-8"
        if step in ("faction", "archetype", "sub_archetype"):
            container.className += " max-w-6xl"
        else:
            container.className += " max-w-4xl"

        if step == "game":
            container.appendChild(self._view_game())
        elif step == "type":
            container.appendChild(self._view_type())
        elif step == "faction":
            container.appendChild(self._view_faction())
        elif step == "archetype":
            container.appendChild(self._view_archetype())
        elif step == "sub_archetype":
            container.appendChild(self._view_sub_archetype())
        elif step == "predator":
            container.appendChild(self._view_predator())
        elif step == "venue":
            container.appendChild(self._view_venue())
        elif step == "generate":
            container.appendChild(self._view_generate())
        elif step == "results":
            container.appendChild(self._view_results())

        self.root.appendChild(container)
        dark_pack_footer()

    def _header(self, title: str, back_step: str | None = None) -> Any:
        wrap = document.createElement("div")
        wrap.className = "mb-6"
        if back_step:

            def go_back(_=None):
                self.state["step"] = back_step
                self._render()

            btn = document.createElement("button")
            btn.className = "btn-secondary mb-4 text-sm"
            btn.innerText = "← Back"
            btn.onclick = go_back
            wrap.appendChild(btn)
        h = document.createElement("h1")
        h.className = "text-2xl font-bold text-blood"
        h.innerText = title
        wrap.appendChild(h)
        return wrap

    def _append_card_list(self, parent: Any, title: str, items: list[str], item_class: str) -> None:
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

    def _view_game(self) -> Any:
        el = document.createElement("div")
        el.appendChild(self._header("WoD Character Generator"))
        p = document.createElement("p")
        p.className = "text-stone-400 mb-6"
        p.innerText = self.system.get_wizard_copy().get(
            "landing_blurb",
            "Pick lineage and build. Same seed gives the same sheet.",
        )
        el.appendChild(p)

        map_link = document.createElement("a")
        map_link.href = "#weights"
        map_link.className = "inline-block mb-6 text-blood hover:underline text-sm"
        map_link.innerText = "Explore weight map →"
        from pyscript.ffi import create_proxy

        from app.nav import _nav_click

        map_link.onclick = create_proxy(lambda e: _nav_click("weights", e))
        el.appendChild(map_link)

        catalog = load_game_catalog()
        for game_id, game in catalog.items():
            card = document.createElement("div")
            if game.get("implemented"):
                card.className = "card p-6 cursor-pointer hover:border-blood transition"
                card.innerHTML = (
                    f"<h2 class='text-xl font-semibold'>{game['label']}</h2>"
                    f"<p class='text-stone-400 mt-2'>{game['tagline']}</p>"
                )

                def start(_=None, gid=game_id):
                    self.state["game"] = gid
                    self.state["step"] = "type"
                    self._render()

                card.onclick = start
            else:
                card.className = "card p-6 mt-4 opacity-50"
                card.innerHTML = (
                    f"<h2 class='text-lg font-semibold'>{game['label']}</h2>"
                    f"<p class='text-stone-500 mt-2'>{game['tagline']}</p>"
                )
            el.appendChild(card)

        if self.state.get("error"):
            err = document.createElement("p")
            err.className = "text-red-400 mt-4"
            err.innerText = f"URL error: {self.state['error']}"
            el.appendChild(err)
        return el

    def _view_type(self) -> Any:
        el = document.createElement("div")
        el.appendChild(self._header("Character type", "game"))
        for entry in self.system.get_character_type_picker():
            tid = entry["id"]
            label = entry["label"]
            btn = document.createElement("button")
            active = (tid == "vampire" and self.state["type"] in ("vampire", "thin_blood")) or self.state["type"] == tid
            btn.className = f"card p-4 w-full text-left mb-3 {'border-blood' if active else ''}"

            def pick(e, t=tid):
                self.state["type"] = t
                profiles = archetypes_for_type(t)
                if profiles:
                    self.state["arch"] = profiles[0].id
                    self.state["sub"] = profiles[0].sub_archetypes[0].id
                self.state["step"] = "faction"
                self._render()

            btn.innerText = label
            btn.onclick = pick
            el.appendChild(btn)
        return el

    def _faction_role(self) -> str:
        return "ghoul" if self.state["type"] == "ghoul" else "vampire"

    def _view_faction(self) -> Any:
        el = document.createElement("div")
        role = self._faction_role()
        el.appendChild(self._header(self.system.get_faction_picker_title(role), "type"))
        options = self.system.get_faction_options(role)
        clan_key = "clan" if role == "vampire" else "domitor_clan"

        grid = document.createElement("div")
        grid.className = "clan-grid"
        for c in options:
            btn = document.createElement("button")
            is_thin = c.get("kind") == "thin_blood"
            if is_thin:
                active = self.state["type"] == "thin_blood"
            else:
                active = self.state["type"] != "thin_blood" and self.state[clan_key] == c["id"]
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
            discs.innerText = _format_disciplines(c)
            btn.appendChild(discs)

            def pick(e, entry=c, k=clan_key, r=role):
                if entry.get("kind") == "thin_blood":
                    self.state["type"] = "thin_blood"
                    profiles = archetypes_for_type("thin_blood")
                    if profiles:
                        self.state["arch"] = profiles[0].id
                        self.state["sub"] = profiles[0].sub_archetypes[0].id
                else:
                    self.state["type"] = r
                    self.state[k] = entry["id"]
                self.state["step"] = "archetype"
                self._render()

            btn.onclick = pick
            grid.appendChild(btn)
        el.appendChild(grid)
        return el

    def _view_archetype(self) -> Any:
        el = document.createElement("div")
        copy = self.system.get_wizard_copy()
        el.appendChild(self._header(copy.get("archetype_title", "Archetype"), "faction"))
        profiles = archetypes_for_type(self.state["type"])

        grid = document.createElement("div")
        grid.className = "archetype-grid"
        for p in profiles:
            btn = document.createElement("button")
            active = self.state["arch"] == p.id
            btn.className = f"archetype-card archetype-card--pickable {'archetype-card--active' if active else ''}"
            btn.setAttribute("type", "button")

            label = document.createElement("span")
            label.className = "archetype-card__label"
            label.innerText = p.label
            btn.appendChild(label)

            desc = document.createElement("p")
            desc.className = "archetype-card__desc"
            desc.innerText = p.description
            btn.appendChild(desc)

            subs = document.createElement("p")
            subs.className = "archetype-card__subs-preview"
            subs.innerText = " · ".join(s.label for s in p.sub_archetypes)
            btn.appendChild(subs)

            def pick(e, aid=p.id):
                self.state["arch"] = aid
                profile = get_archetype(aid)
                if profile.sub_archetypes:
                    self.state["sub"] = profile.sub_archetypes[0].id
                self.state["step"] = "sub_archetype"
                self._render()

            btn.onclick = pick
            grid.appendChild(btn)
        el.appendChild(grid)
        return el

    def _view_sub_archetype(self) -> Any:
        el = document.createElement("div")
        copy = self.system.get_wizard_copy()
        el.appendChild(self._header(copy.get("sub_archetype_title", "Subtype"), "archetype"))
        profile = get_archetype(self.state["arch"])

        intro = document.createElement("p")
        intro.className = "text-stone-400 mb-4"
        intro.innerText = copy.get("sub_archetype_intro", "")
        el.appendChild(intro)

        picked = document.createElement("p")
        picked.className = "text-stone-500 text-sm mb-4"
        picked.innerText = profile.label
        el.appendChild(picked)

        grid = document.createElement("div")
        grid.className = "sub-archetype-grid"
        for s in profile.sub_archetypes:
            btn = document.createElement("button")
            active = self.state["sub"] == s.id
            btn.className = f"archetype-card archetype-card--pickable {'archetype-card--active' if active else ''}"
            btn.setAttribute("type", "button")

            label = document.createElement("span")
            label.className = "archetype-card__label"
            label.innerText = s.label
            btn.appendChild(label)

            if s.description:
                desc = document.createElement("p")
                desc.className = "archetype-card__desc"
                desc.innerText = s.description
                btn.appendChild(desc)

            def pick(e, sid=s.id):
                self.state["sub"] = sid
                self.state["step"] = "predator" if self._type_uses_predator() else "venue"
                self._render()

            btn.onclick = pick
            grid.appendChild(btn)
        el.appendChild(grid)
        return el

    def _view_predator(self) -> Any:
        el = document.createElement("div")
        copy = self.system.get_wizard_copy()
        el.appendChild(self._header(copy.get("predator_title", "Predator type"), "sub_archetype"))

        intro = document.createElement("p")
        intro.className = "text-stone-400 mb-4"
        intro.innerText = copy.get("predator_intro", "")
        el.appendChild(intro)

        picker = self.system.get_predator_picker()
        grid = document.createElement("div")
        grid.className = "predator-grid"
        selected = self.state.get("predator") or picker[0]["id"]
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

            self._append_card_list(btn, "Benefits", entry.get("benefits", []), "predator-card__benefit")
            self._append_card_list(btn, "Restrictions", entry.get("restrictions", []), "predator-card__restriction")
            self._append_card_list(btn, "Drawbacks", entry.get("drawbacks", []), "predator-card__drawback")

            def pick(e, p=pid):
                self.state["predator"] = p
                self.state["step"] = "venue"
                self._render()

            btn.onclick = pick
            grid.appendChild(btn)
        el.appendChild(grid)
        return el

    def _view_venue(self) -> Any:
        el = document.createElement("div")
        back = "predator" if self._type_uses_predator() else "sub_archetype"
        el.appendChild(self._header("Venue & XP", back))
        for venue in self.system.get_venue_picker():
            vid = venue["id"]
            label = venue["label"]
            btn = document.createElement("button")
            btn.className = f"card p-4 w-full text-left mb-3 {'border-blood' if self.state['venue'] == vid else ''}"

            def pick(e, v=vid):
                self.state["venue"] = v
                self._render()

            btn.innerText = label
            btn.onclick = pick
            el.appendChild(btn)

        if self._venue_picker.get(self.state["venue"], {}).get("requires_approval_month"):
            lbl = document.createElement("label")
            lbl.className = "block mt-4 text-stone-400"
            lbl.innerText = "Approval month (YYYY-MM)"
            inp = document.createElement("input")
            inp.type = "text"
            inp.value = self.state["approval"]
            inp.className = "bg-ash border border-stone-700 rounded px-3 py-2 w-full mt-1"

            def on_change(e):
                self.state["approval"] = inp.value

            inp.oninput = on_change
            el.appendChild(lbl)
            el.appendChild(inp)

        go = document.createElement("button")
        go.className = "btn-primary mt-6"

        def next_step(_=None):
            self.state["step"] = "generate"
            self._render()

        go.innerText = "Continue"
        go.onclick = next_step
        el.appendChild(go)
        return el

    def _view_generate(self) -> Any:
        el = document.createElement("div")
        el.appendChild(self._header("Generate", "venue"))
        seed_lbl = document.createElement("label")
        seed_lbl.className = "block text-stone-400"
        seed_lbl.innerText = "Seed (reproducible)"
        seed_inp = document.createElement("input")
        seed_inp.type = "number"
        seed_inp.value = str(self.state["seed"])
        seed_inp.className = "bg-ash border border-stone-700 rounded px-3 py-2 w-full mt-1 mb-4"

        def on_seed(e):
            self.state["seed"] = int(seed_inp.value or 0)

        seed_inp.oninput = on_seed
        el.appendChild(seed_lbl)
        el.appendChild(seed_inp)

        gen = document.createElement("button")
        gen.className = "btn-primary"

        def do_gen(_=None):
            try:
                self.state["seed"] = int(seed_inp.value) if str(seed_inp.value).strip() else int(self.state["seed"])
            except (ValueError, TypeError):
                self.state["error"] = "Enter a valid numeric seed."
                self._render()
                return
            self._generate()
            if self.state.get("result"):
                self.state["step"] = "results"
            self._render()

        gen.innerText = "Generate character"
        gen.onclick = do_gen
        el.appendChild(gen)

        if self.state.get("error"):
            err = document.createElement("p")
            err.className = "text-red-400 mt-4"
            err.innerText = self.state["error"]
            el.appendChild(err)
        return el

    def _view_results(self) -> Any:
        el = document.createElement("div")
        header = self._header("Results", "generate")
        header.className += " no-print"
        el.appendChild(header)
        result = self.state.get("result")
        if not result:
            if not self.state.get("error"):
                self._generate()
                result = self.state.get("result")
        if not result:
            err = self.state.get("error")
            if err:
                msg = document.createElement("pre")
                msg.className = "text-red-400 mb-4 text-sm whitespace-pre-wrap font-mono"
                msg.innerText = f"Generation failed:\n{err}"
                el.appendChild(msg)
            else:
                msg = document.createElement("p")
                msg.className = "text-red-400 mb-4"
                msg.innerText = "No result. Go back and generate."
                el.appendChild(msg)

            retry = document.createElement("button")
            retry.className = "btn-primary mr-3"

            def try_again(_=None):
                self._generate()
                if self.state.get("result"):
                    self._render()

            retry.innerText = "Try again"
            retry.onclick = try_again
            el.appendChild(retry)
            return el

        tabs = document.createElement("div")
        tabs.className = "flex gap-4 mb-4 border-b border-stone-800 no-print"
        for tid, label in [("sheet", "Sheet"), ("log", "Creation Log"), ("xp", "XP Log")]:
            tbtn = document.createElement("button")
            tbtn.className = f"pb-2 px-2 {'tab-active' if self.state['tab'] == tid else 'text-stone-500'}"

            def switch(e, t=tid):
                self.state["tab"] = t
                self._render()

            tbtn.innerText = label
            tbtn.onclick = switch
            tabs.appendChild(tbtn)
        el.appendChild(tabs)

        panel = document.createElement("div")
        panel.className = "card p-6 results-print-root"

        sheet_panel = document.createElement("div")
        sheet_panel.className = "results-tab-panel sheet-panel"
        if self.state["tab"] != "sheet":
            sheet_panel.className += " results-tab-hidden"
        sheet_panel.appendChild(
            render_lotn_v5_sheet(
                result.character,
                convictions=self._convictions(),
                convictions_seed=int(self.state["convictions_seed"]),
                on_reroll_convictions=self._reroll_convictions,
            )
        )
        panel.appendChild(sheet_panel)

        creation_lines = [f"[{e.phase}] {e.message}" for e in result.creation_log]
        log_panel = document.createElement("div")
        log_panel.className = "results-tab-panel results-log-panel font-mono text-sm"
        if self.state["tab"] != "log":
            log_panel.className += " results-tab-hidden"
        log_heading = document.createElement("h2")
        log_heading.className = "results-print-heading"
        log_heading.innerText = "Creation Log"
        log_panel.appendChild(log_heading)
        log_body = document.createElement("pre")
        log_body.className = "results-log-body whitespace-pre-wrap"
        log_body.innerText = "\n".join(creation_lines)
        log_panel.appendChild(log_body)
        panel.appendChild(log_panel)

        xp_panel = document.createElement("div")
        xp_panel.className = "results-tab-panel results-xp-panel font-mono text-sm"
        if self.state["tab"] != "xp":
            xp_panel.className += " results-tab-hidden"
        xp_heading = document.createElement("h2")
        xp_heading.className = "results-print-heading"
        xp_heading.innerText = "XP Log"
        xp_panel.appendChild(xp_heading)
        xp_body = document.createElement("pre")
        xp_body.className = "results-log-body whitespace-pre-wrap"
        xp_body.innerText = format_xp_log(result.xp_log)
        xp_panel.appendChild(xp_body)
        panel.appendChild(xp_panel)

        el.appendChild(panel)

        actions = document.createElement("div")
        actions.className = "flex flex-wrap gap-3 mt-6 no-print"

        def copy_link(_=None):
            link = self._share_url()
            try:
                self._sync_url()
            except Exception:
                pass
            window.navigator.clipboard.writeText(link)

        def reroll(_=None):
            self.state["seed"] = random.randint(1, 999_999)
            self._generate()
            self._render()

        def export_json(_=None):
            payload = result.to_dict()
            payload["convictions_seed"] = int(self.state["convictions_seed"])
            payload["convictions"] = self._convictions()
            blob = json.dumps(payload, indent=2)
            window.navigator.clipboard.writeText(blob)

        for label, fn in [("Copy Share Link", copy_link), ("Re-roll", reroll), ("Copy JSON", export_json)]:
            b = document.createElement("button")
            b.className = "btn-secondary"
            b.innerText = label
            b.onclick = fn
            actions.appendChild(b)

        print_btn = document.createElement("button")
        print_btn.className = "btn-secondary"
        print_btn.innerText = "Print"
        print_btn.onclick = lambda _: window.print()
        actions.appendChild(print_btn)
        el.appendChild(actions)

        meta = document.createElement("p")
        meta.className = "text-stone-500 text-sm mt-4"
        meta.innerText = (
            f"Seed {result.seed} · Convictions seed {self.state['convictions_seed']} · "
            f"XP {result.xp_spent}/{result.xp_budget} spent · {result.xp_remaining} banked"
        )
        el.appendChild(meta)
        return el
