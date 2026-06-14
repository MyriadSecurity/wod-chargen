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
from wod_chargen.games.lotn_v5.archetypes import (
    THIN_BLOOD_ONLY_SUFFIX,
    archetypes_for_type,
    archetype_display_label,
    get_archetype,
    is_thin_blood_only,
)
from wod_chargen.defaults import DEFAULT_GAME_ID
from wod_chargen.games.lotn_v5.convictions import pick_convictions
from wod_chargen.games.lotn_v5.generator import generate_character
from wod_chargen.games.registry import get_game, load_game_catalog
from wod_chargen.venues import load_venue


def _format_disciplines(entry: dict[str, Any]) -> str:
    if entry.get("discipline_note"):
        return entry["discipline_note"]
    discipline_ids = entry.get("disciplines", [])
    if not discipline_ids:
        return "No in-clan disciplines"
    return " · ".join(d.replace("_", " ").title() for d in discipline_ids)


def _flash_button(btn, message: str = "Copied!", *, reset_ms: int = 1600) -> None:
    original = btn.innerText
    btn.innerText = message
    if "btn-secondary--flash" not in btn.className:
        btn.className += " btn-secondary--flash"

    def reset() -> None:
        btn.innerText = original
        btn.className = btn.className.replace(" btn-secondary--flash", "").strip()

    from pyscript.ffi import create_proxy

    window.setTimeout(create_proxy(reset), reset_ms)


def _render_generation_error(el, err: str) -> None:
    box = document.createElement("div")
    box.className = "results-error"
    lines = err.strip().splitlines()
    summary = document.createElement("p")
    summary.className = "results-error__summary"
    summary.innerText = lines[0] if lines else "Generation failed."
    box.appendChild(summary)
    if len(lines) > 1:
        details = document.createElement("pre")
        details.className = "results-error__details"
        details.innerText = err.strip()
        box.appendChild(details)
    el.appendChild(box)


class WizardApp:
    def __init__(self, root) -> None:
        self.root = root
        self.state: dict[str, Any] = {
            "game": DEFAULT_GAME_ID,
            "type": "vampire",
            "clan": "brujah",
            "domitor_clan": "tremere",
            "arch": "diplomat",
            "sub": "silver_tongue",
            "predator": "",
            "venue": "mes_end_to_dawn",
            "approval": "2026-06",
            "xp_custom": "100",
            "seed": random.randint(1, 999_999),
            "convictions_seed": random.randint(1, 999_999),
            "phase": "landing",
            "unlocked_through": "venue",
            "scroll_to_step": None,
            "expanded_sections": [],
            "result": None,
            "error": None,
            "tab": "sheet",
            "full_random": False,
        }
        self.system = get_game(self.state["game"])
        self._venue_picker = {v["id"]: v for v in self.system.get_venue_picker()}
        self._parse_url()

    def _build_steps(self) -> list[str]:
        return self.system.get_wizard_steps()

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
            self.system = get_game(payload.game)
            self._venue_picker = {v["id"]: v for v in self.system.get_venue_picker()}
            self.state["venue"] = payload.venue
            opts = payload.options
            for key in ("type", "clan", "domitor_clan", "arch", "sub", "predator", "approval"):
                if key in opts:
                    self.state[key] = opts[key]
            if "xp" in opts:
                self.state["xp_custom"] = opts["xp"]
                self.state["venue"] = "custom_xp"
            self._validate_selection()
            self._generate()
            self.state["phase"] = "results" if self.state.get("result") else "build"
            self.state["unlocked_through"] = "generate"
        except Exception as exc:
            self.state["error"] = str(exc)
            self.state["phase"] = "landing"

    def _type_uses_predator(self) -> bool:
        return self.system.type_uses_predator(self.state["type"])

    def _options(self) -> dict[str, str]:
        opts = wizard_share_options(
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
        if self.state.get("venue") == "custom_xp":
            opts["xp"] = str(self.state.get("xp_custom", "")).strip()
        return opts

    def _venue_continue_error(self) -> str | None:
        venue_id = self.state.get("venue", "")
        if venue_id == "custom_xp":
            raw = str(self.state.get("xp_custom", "")).strip()
            if not raw:
                return "Enter an XP amount."
            try:
                xp = int(raw)
            except ValueError:
                return "XP must be a whole number."
            if xp < 0:
                return "XP must be zero or greater."
            return None
        if self._venue_picker.get(venue_id, {}).get("requires_approval_month"):
            approval = str(self.state.get("approval", "")).strip()
            if not approval:
                return "Enter an approval month (YYYY-MM)."
        return None

    def _step_index(self, step: str) -> int:
        return self._build_steps().index(step)

    def _is_unlocked(self, step: str) -> bool:
        through = self.state.get("unlocked_through", "venue")
        return self._step_index(step) <= self._step_index(through)

    def _step_visible(self, step: str) -> bool:
        if step == "predator":
            return self._type_uses_predator()
        return True

    def _advance_unlock(self, step: str) -> None:
        through = self.state.get("unlocked_through", "venue")
        if self._step_index(step) > self._step_index(through):
            self.state["unlocked_through"] = step

    def _next_step_after(self, step: str) -> str:
        steps = self._build_steps()
        idx = self._step_index(step)
        while idx + 1 < len(steps):
            idx += 1
            candidate = steps[idx]
            if not self._step_visible(candidate):
                continue
            return candidate
        return "generate"

    def _advance_from(self, step: str) -> None:
        self._advance_unlock(self._next_step_after(step))

    def _active_step(self) -> str:
        return self.state.get("unlocked_through", "venue")

    def _finish_step(self, completed_step: str) -> None:
        """Unlock the next step, collapse prior choices, and scroll into view."""
        self._advance_from(completed_step)
        self.state["scroll_to_step"] = self._active_step()
        self.state["expanded_sections"] = []

    def _is_section_collapsed(self, step: str) -> bool:
        if step == self._active_step():
            return False
        if step in self.state.get("expanded_sections", []):
            return False
        return self._step_index(step) < self._step_index(self._active_step())

    def _toggle_section(self, step: str) -> None:
        if step == self._active_step():
            return
        expanded = list(self.state.get("expanded_sections", []))
        if step in expanded:
            expanded.remove(step)
        else:
            expanded.append(step)
            self.state["scroll_to_step"] = step
        self.state["expanded_sections"] = expanded
        self._render()

    def _step_summary(self, step: str) -> str:
        if step == "venue":
            venue_id = self.state.get("venue", "")
            if venue_id == "custom_xp":
                xp = str(self.state.get("xp_custom", "")).strip()
                return f"{xp} XP" if xp else "Custom XP"
            label = self._venue_picker.get(venue_id, {}).get("label", venue_id)
            approval = str(self.state.get("approval", "")).strip()
            if self._venue_picker.get(venue_id, {}).get("requires_approval_month") and approval:
                return f"{label} · {approval}"
            return label
        if step == "type":
            labels = {entry["id"]: entry["label"] for entry in self.system.get_character_type_picker()}
            if self.state.get("type") == "thin_blood":
                return "Thin-Blood"
            return labels.get(self.state.get("type", ""), self.state.get("type", ""))
        if step == "faction":
            role = self._faction_role()
            if self.state.get("type") == "thin_blood":
                return "Thin-Blood"
            key = "clan" if role == "vampire" else "domitor_clan"
            labels = {entry["id"]: entry["label"] for entry in self.system.get_faction_options(role)}
            return labels.get(self.state.get(key, ""), self.state.get(key, ""))
        if step == "archetype":
            profile = get_archetype(self.state["arch"])
            return archetype_display_label(profile)
        if step == "sub_archetype":
            profile = get_archetype(self.state["arch"])
            for sub in profile.sub_archetypes:
                if sub.id == self.state["sub"]:
                    return sub.label
            return self.state.get("sub", "")
        if step == "predator":
            labels = {entry["id"]: entry["label"] for entry in self.system.get_predator_picker()}
            pred = self.state.get("predator") or ""
            return labels.get(pred, pred.replace("_", " ").title())
        if step == "generate":
            return f"Seed {self.state.get('seed', '')}"
        return ""

    def _perform_pending_scroll(self) -> None:
        target = self.state.pop("scroll_to_step", None)
        if not target:
            return
        from pyscript.ffi import create_proxy

        def do_scroll() -> None:
            el = document.getElementById(f"wizard-step-{target}")
            if el is not None and hasattr(el, "scrollIntoView"):
                el.scrollIntoView({"behavior": "smooth", "block": "start"})

        window.setTimeout(create_proxy(do_scroll), 50)

    def _start_build(self) -> None:
        self.state["phase"] = "build"
        self.state["unlocked_through"] = "venue"
        self.state["scroll_to_step"] = "venue"
        self.state["expanded_sections"] = []
        self.state["error"] = None

    def _reset_to_landing(self) -> None:
        """Clear share state and return to game pick for a fresh character."""
        self.state["phase"] = "landing"
        self.state["unlocked_through"] = "venue"
        self.state["scroll_to_step"] = None
        self.state["expanded_sections"] = []
        self.state["result"] = None
        self.state["error"] = None
        self.state["seed"] = random.randint(1, 999_999)
        self.state["convictions_seed"] = random.randint(1, 999_999)
        path = window.location.pathname or "/"
        hash_part = window.location.hash or ""
        window.history.replaceState(None, "", f"{path}{hash_part}")

    def _goto_results(self) -> None:
        self.state["phase"] = "results"

    def _wrap_section(self, step: str, title: str, body: Any) -> Any:
        collapsed = self._is_section_collapsed(step)
        section = document.createElement("section")
        section.className = "wizard-section"
        if collapsed:
            section.className += " wizard-section--collapsed"
        elif step == self._active_step():
            section.className += " wizard-section--active"
        section.id = f"wizard-step-{step}"

        head = document.createElement("button")
        head.type = "button"
        head.className = "wizard-section__head"
        head.setAttribute("aria-expanded", "false" if collapsed else "true")
        head.setAttribute("aria-controls", f"wizard-step-{step}-body")

        title_row = document.createElement("div")
        title_row.className = "wizard-section__title-row"
        h2 = document.createElement("h2")
        h2.className = "wizard-section__title"
        h2.innerText = title
        chevron = document.createElement("span")
        chevron.className = "wizard-section__chevron"
        chevron.innerText = "▾" if not collapsed else "▸"
        chevron.setAttribute("aria-hidden", "true")
        title_row.appendChild(h2)
        title_row.appendChild(chevron)
        head.appendChild(title_row)

        if collapsed:
            summary = document.createElement("p")
            summary.className = "wizard-section__summary"
            summary.innerText = self._step_summary(step)
            head.appendChild(summary)

        def toggle(_=None, s=step):
            self._toggle_section(s)

        head.onclick = toggle
        section.appendChild(head)

        body_wrap = document.createElement("div")
        body_wrap.id = f"wizard-step-{step}-body"
        body_wrap.className = "wizard-section__body"
        if collapsed:
            body_wrap.className += " wizard-section__body--hidden"
            body_wrap.setAttribute("hidden", "")
        if body.className:
            body.className += " wizard-section__content"
        else:
            body.className = "wizard-section__content"
        body_wrap.appendChild(body)
        section.appendChild(body_wrap)
        return section

    def _on_type_selected(self, character_type: str) -> None:
        self.state["type"] = character_type
        profiles = archetypes_for_type(character_type)
        if profiles:
            self.state["arch"] = profiles[0].id
            self.state["sub"] = profiles[0].sub_archetypes[0].id
        if not self.system.type_uses_predator(character_type):
            self.state["predator"] = ""
        self._finish_step("type")

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

    def _recreate_summary_lines(self, result) -> list[str]:
        """Build options + seeds needed to regenerate this character from a share URL."""
        lines = [
            f"Share link: {self._share_url()}",
            f"Seed: {result.seed}",
            f"Convictions seed: {self.state['convictions_seed']}",
            f"Venue: {self._step_summary('venue')}",
            f"Type: {self._step_summary('type')}",
            f"Lineage: {self._step_summary('faction')}",
            f"Archetype: {self._step_summary('archetype')}",
            f"Subtype: {self._step_summary('sub_archetype')}",
        ]
        if self._type_uses_predator():
            lines.append(f"Predator: {self._step_summary('predator')}")
        lines.append(f"XP: {result.xp_spent}/{result.xp_budget} spent · {result.xp_remaining} banked")
        return lines

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

    def _apply_full_random(self, character_type: str) -> None:
        """Pick clan, archetype, subtype, and predator (vampire) at random."""
        self.state["type"] = character_type
        profiles = archetypes_for_type(character_type)
        if not profiles:
            raise ValueError(f"No archetypes for {character_type!r}")

        profile = random.choice(profiles)
        self.state["arch"] = profile.id
        self.state["sub"] = random.choice(profile.sub_archetypes).id

        role = "ghoul" if character_type == "ghoul" else "vampire"
        faction_options = [
            entry
            for entry in self.system.get_faction_options(role)
            if character_type != "vampire" or entry.get("kind") != "thin_blood"
        ]
        if not faction_options:
            raise ValueError(f"No faction options for {character_type!r}")
        faction = random.choice(faction_options)
        if character_type == "ghoul":
            self.state["domitor_clan"] = faction["id"]
        else:
            self.state["clan"] = faction["id"]

        if self.system.type_uses_predator(character_type):
            preds = self.system.get_predator_picker()
            self.state["predator"] = random.choice(preds)["id"]
        else:
            self.state["predator"] = ""

        self.state["seed"] = random.randint(1, 999_999)
        self._validate_selection()

    def _reroll_character(self) -> None:
        if self.state.get("full_random"):
            self._apply_full_random(self.state["type"])
        else:
            self.state["seed"] = random.randint(1, 999_999)
        self._generate()

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
        phase = self.state["phase"]
        container = document.createElement("div")
        container.className = "flex-1 mx-auto w-full px-4 py-8 max-w-6xl wizard-page"

        if phase == "landing":
            container.appendChild(self._view_game())
        else:
            container.appendChild(self._home_link())
            if phase == "build":
                container.appendChild(self._view_build())
            elif phase == "results":
                container.appendChild(self._view_results())

        self.root.appendChild(container)
        dark_pack_footer()
        if phase == "build":
            self._perform_pending_scroll()

    def _home_link(self) -> Any:
        copy = self.system.get_wizard_copy()
        link = document.createElement("a")
        link.href = "#"
        link.className = "wizard-home-link no-print"
        link.innerText = copy.get("home_link_label", "← New character")

        def go_home(e=None):
            if e is not None:
                e.preventDefault()
            self._reset_to_landing()
            self._render()

        link.onclick = go_home
        return link

    def _view_build(self) -> Any:
        el = document.createElement("div")
        el.className = "wizard-build"
        el.appendChild(self._page_header("WoD Character Generator"))

        map_link = document.createElement("a")
        map_link.href = "#weights"
        map_link.className = "inline-block mb-6 text-blood hover:underline text-sm"
        map_link.innerText = "Explore weight map →"
        from pyscript.ffi import create_proxy

        from app.nav import _nav_click

        map_link.onclick = create_proxy(lambda e: _nav_click("weights", e))
        el.appendChild(map_link)

        copy = self.system.get_wizard_copy()
        sections: list[tuple[str, str, Any]] = [
            ("venue", copy.get("xp_title", "Starting XP"), self._view_venue()),
            ("type", "Character type", self._view_type()),
            ("faction", self.system.get_faction_picker_title(self._faction_role()), self._view_faction()),
            (
                "archetype",
                copy.get("archetype_title", "Archetype"),
                self._view_archetype(),
            ),
            (
                "sub_archetype",
                copy.get("sub_archetype_title", "Subtype"),
                self._view_sub_archetype(),
            ),
            ("predator", copy.get("predator_title", "Predator type"), self._view_predator()),
            ("generate", "Generate", self._view_generate()),
        ]
        for step, title, body in sections:
            if not self._step_visible(step):
                continue
            if not self._is_unlocked(step):
                continue
            el.appendChild(self._wrap_section(step, title, body))

        if self.state.get("error") and self.state.get("phase") == "build":
            err = document.createElement("p")
            err.className = "text-red-400 mt-4"
            err.innerText = self.state["error"]
            el.appendChild(err)
        return el

    def _page_header(self, title: str) -> Any:
        wrap = document.createElement("div")
        wrap.className = "mb-6"
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
        el.appendChild(self._page_header("WoD Character Generator"))
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
                    self.system = get_game(gid)
                    self._venue_picker = {v["id"]: v for v in self.system.get_venue_picker()}
                    self._start_build()
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
        copy = self.system.get_wizard_copy()
        random_wrap = document.createElement("label")
        random_wrap.className = "card p-4 mb-4 flex items-start gap-3 cursor-pointer"
        random_cb = document.createElement("input")
        random_cb.type = "checkbox"
        random_cb.className = "mt-1"
        random_cb.checked = bool(self.state.get("full_random"))

        def on_random_toggle(_=None):
            self.state["full_random"] = bool(random_cb.checked)

        random_cb.onchange = on_random_toggle
        random_wrap.appendChild(random_cb)
        random_text = document.createElement("div")
        random_title = document.createElement("div")
        random_title.className = "font-semibold"
        random_title.innerText = copy.get("full_random_label", "Full random")
        random_hint = document.createElement("p")
        random_hint.className = "text-stone-400 text-sm mt-1"
        random_hint.innerText = copy.get(
            "full_random_hint",
            "Skip the build steps — randomly pick clan, archetype, subtype, and predator type, then generate.",
        )
        random_text.appendChild(random_title)
        random_text.appendChild(random_hint)
        random_wrap.appendChild(random_text)
        el.appendChild(random_wrap)

        grid = document.createElement("div")
        grid.className = "wizard-type-grid"
        for entry in self.system.get_character_type_picker():
            tid = entry["id"]
            btn = document.createElement("button")
            btn.type = "button"
            active = self.state["type"] == tid
            btn.className = f"wizard-type-card {'wizard-type-card--active' if active else ''}"

            label_el = document.createElement("span")
            label_el.className = "wizard-type-card__label"
            label_el.innerText = entry["label"]
            btn.appendChild(label_el)
            summary = entry.get("summary")
            if summary:
                summary_el = document.createElement("p")
                summary_el.className = "wizard-type-card__summary"
                summary_el.innerText = summary
                btn.appendChild(summary_el)

            def pick(e, t=tid):
                if self.state.get("full_random"):
                    self._apply_full_random(t)
                    self._generate()
                    if self.state.get("result"):
                        self._goto_results()
                    else:
                        self.state["phase"] = "build"
                        self.state["unlocked_through"] = "generate"
                else:
                    self._on_type_selected(t)
                self._render()

            btn.onclick = pick
            grid.appendChild(btn)
        el.appendChild(grid)
        return el

    def _faction_role(self) -> str:
        return "ghoul" if self.state["type"] == "ghoul" else "vampire"

    def _view_faction(self) -> Any:
        el = document.createElement("div")
        role = self._faction_role()
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
                self._finish_step("faction")
                self._render()

            btn.onclick = pick
            grid.appendChild(btn)
        el.appendChild(grid)
        return el

    def _append_archetype_label(self, parent: Any, profile: Any) -> None:
        label = document.createElement("span")
        label.className = "archetype-card__label"
        name = document.createElement("span")
        name.innerText = profile.label
        label.appendChild(name)
        if is_thin_blood_only(profile):
            note = document.createElement("span")
            note.className = "archetype-card__type-note"
            note.innerText = THIN_BLOOD_ONLY_SUFFIX
            label.appendChild(note)
        parent.appendChild(label)

    def _view_archetype(self) -> Any:
        el = document.createElement("div")
        profiles = archetypes_for_type(self.state["type"])

        grid = document.createElement("div")
        grid.className = "archetype-grid"
        for p in profiles:
            btn = document.createElement("button")
            active = self.state["arch"] == p.id
            btn.className = f"archetype-card archetype-card--pickable {'archetype-card--active' if active else ''}"
            btn.setAttribute("type", "button")

            self._append_archetype_label(btn, p)

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
                self._finish_step("archetype")
                self._render()

            btn.onclick = pick
            grid.appendChild(btn)
        el.appendChild(grid)
        return el

    def _view_sub_archetype(self) -> Any:
        el = document.createElement("div")
        copy = self.system.get_wizard_copy()
        profile = get_archetype(self.state["arch"])

        intro = document.createElement("p")
        intro.className = "text-stone-400 mb-4"
        intro.innerText = copy.get("sub_archetype_intro", "")
        el.appendChild(intro)

        picked = document.createElement("p")
        picked.className = "text-stone-500 text-sm mb-4"
        picked.innerText = archetype_display_label(profile)
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
                self._finish_step("sub_archetype")
                self._render()

            btn.onclick = pick
            grid.appendChild(btn)
        el.appendChild(grid)
        return el

    def _view_predator(self) -> Any:
        el = document.createElement("div")
        copy = self.system.get_wizard_copy()

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
                self._finish_step("predator")
                self._render()

            btn.onclick = pick
            grid.appendChild(btn)
        el.appendChild(grid)
        return el

    def _view_venue(self) -> Any:
        el = document.createElement("div")
        copy = self.system.get_wizard_copy()

        intro = document.createElement("p")
        intro.className = "text-stone-400 mb-4"
        intro.innerText = copy.get(
            "xp_intro",
            "Choose how much experience the character has to spend.",
        )
        el.appendChild(intro)

        for venue in self.system.get_venue_picker():
            vid = venue["id"]
            label = venue["label"]
            btn = document.createElement("button")
            btn.className = f"card p-4 w-full text-left mb-3 {'card--selected' if self.state['venue'] == vid else ''}"

            def pick(e, v=vid):
                self.state["venue"] = v
                self.state["error"] = None
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

        xp_inp: Any | None = None
        if self.state.get("venue") == "custom_xp":
            lbl = document.createElement("label")
            lbl.className = "block mt-4 text-stone-400"
            lbl.innerText = copy.get("xp_custom_label", "XP amount")
            xp_inp = document.createElement("input")
            xp_inp.type = "number"
            xp_inp.min = "0"
            xp_inp.step = "1"
            xp_inp.value = str(self.state.get("xp_custom", "100"))
            xp_inp.className = "bg-ash border border-stone-700 rounded px-3 py-2 w-full mt-1"

            def on_xp_change(e):
                self.state["xp_custom"] = xp_inp.value

            xp_inp.oninput = on_xp_change
            el.appendChild(lbl)
            el.appendChild(xp_inp)

        go = document.createElement("button")
        go.className = "btn-primary mt-6"

        def next_step(_=None):
            if xp_inp is not None:
                self.state["xp_custom"] = str(xp_inp.value).strip()
            err = self._venue_continue_error()
            if err:
                self.state["error"] = err
                self._render()
                return
            self.state["error"] = None
            self._finish_step("venue")
            self._render()

        go.innerText = "Continue"
        go.onclick = next_step
        el.appendChild(go)
        return el

    def _view_generate(self) -> Any:
        el = document.createElement("div")
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
                self._goto_results()
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
        header = self._page_header("Results")
        header.className += " no-print"
        actions_top = document.createElement("div")
        actions_top.className = "flex flex-wrap gap-3 mb-4 no-print"

        def edit_build(_=None):
            self.state["phase"] = "build"
            self.state["unlocked_through"] = "generate"
            self.state["scroll_to_step"] = "generate"
            self.state["expanded_sections"] = []
            self.state["error"] = None
            self._render()

        edit_btn = document.createElement("button")
        edit_btn.className = "btn-secondary text-sm"
        edit_btn.innerText = "← Edit build"
        edit_btn.onclick = edit_build
        actions_top.appendChild(edit_btn)
        header.appendChild(actions_top)
        el.appendChild(header)
        result = self.state.get("result")
        if not result:
            if not self.state.get("error"):
                self._generate()
                result = self.state.get("result")
        if not result:
            err = self.state.get("error")
            if err:
                _render_generation_error(el, err)
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
        tabs.className = "flex gap-2 mb-4 border-b border-stone-800 no-print"
        tab_ids = [("sheet", "Sheet"), ("log", "Creation Log"), ("xp", "XP Log")]
        for tid, label in tab_ids:
            tbtn = document.createElement("button")
            tbtn.type = "button"
            tbtn.className = f"results-tab {'results-tab--active' if self.state['tab'] == tid else ''}"
            tbtn.setAttribute("role", "tab")
            tbtn.setAttribute("aria-selected", "true" if self.state["tab"] == tid else "false")

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

        recreate_panel = document.createElement("section")
        recreate_panel.className = "results-recreate-panel"
        recreate_heading = document.createElement("h2")
        recreate_heading.className = "results-print-heading"
        recreate_heading.innerText = "Recreation"
        recreate_panel.appendChild(recreate_heading)
        recreate_body = document.createElement("pre")
        recreate_body.className = "results-log-body results-recreate-body whitespace-pre-wrap"
        recreate_body.innerText = "\n".join(self._recreate_summary_lines(result))
        recreate_panel.appendChild(recreate_body)
        panel.appendChild(recreate_panel)

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
            _flash_button(copy_btn, "Link copied!")

        def reroll(_=None):
            self._reroll_character()
            self._render()

        def export_json(_=None):
            payload = result.to_dict()
            payload["convictions_seed"] = int(self.state["convictions_seed"])
            payload["convictions"] = self._convictions()
            blob = json.dumps(payload, indent=2)
            window.navigator.clipboard.writeText(blob)
            _flash_button(json_btn, "JSON copied!")

        copy_btn = document.createElement("button")
        copy_btn.className = "btn-secondary"
        copy_btn.type = "button"
        copy_btn.innerText = "Copy Share Link"
        copy_btn.onclick = copy_link
        actions.appendChild(copy_btn)

        reroll_btn = document.createElement("button")
        reroll_btn.className = "btn-secondary"
        reroll_btn.type = "button"
        reroll_btn.innerText = "Re-roll"
        reroll_btn.onclick = reroll
        actions.appendChild(reroll_btn)

        json_btn = document.createElement("button")
        json_btn.className = "btn-secondary"
        json_btn.type = "button"
        json_btn.innerText = "Copy JSON"
        json_btn.onclick = export_json
        actions.appendChild(json_btn)

        print_btn = document.createElement("button")
        print_btn.className = "btn-secondary"
        print_btn.type = "button"

        def print_sheet(_=None):
            from pyscript.ffi import create_proxy

            window.setTimeout(create_proxy(lambda: window.print()), 50)

        print_btn.innerText = "Print sheet"
        print_btn.onclick = print_sheet
        actions.appendChild(print_btn)
        el.appendChild(actions)

        return el
