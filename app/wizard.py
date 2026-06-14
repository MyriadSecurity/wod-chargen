"""Multi-step creation wizard."""

from __future__ import annotations

import json
import random
from typing import Any

from pyscript import document, window

from app.components.footer import dark_pack_footer
from app.components.sheet import render_lotn_v5_sheet
from app.formatting import titleize_id
from app.nav import app_nav
from app.views import archetype as archetype_view
from app.views import faction as faction_view
from app.views import generate as generate_view
from app.views import predator as predator_view
from app.views import type as type_view
from app.views import venue as venue_view
from app.wizard_state import (
    build_share_options,
    default_state,
    generate,
    parse_url,
    share_payload,
    share_url,
    sync_url,
    type_uses_predator,
    validate_selection,
    venue_continue_error,
)
from wod_chargen.core.xp_log_format import format_xp_log
from wod_chargen.games.lotn_v5.archetypes import (
    archetypes_for_type,
    archetype_display_label,
    get_archetype,
)
from wod_chargen.games.lotn_v5.convictions import pick_convictions
from wod_chargen.games.registry import get_game, load_game_catalog


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
        self.state: dict[str, Any] = default_state()
        self.system = get_game(self.state["game"])
        self._venue_picker = {v["id"]: v for v in self.system.get_venue_picker()}
        parse_url(self)

    def _build_steps(self) -> list[str]:
        return self.system.get_wizard_steps()

    def _parse_url(self) -> None:
        parse_url(self)

    def _type_uses_predator(self) -> bool:
        return type_uses_predator(self)

    def _options(self) -> dict[str, str]:
        return build_share_options(self)

    def _venue_continue_error(self) -> str | None:
        return venue_continue_error(self)

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
            return labels.get(pred, titleize_id(pred))
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

    def _share_payload(self):
        return share_payload(self)

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
        return share_url(self)

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
        sync_url(self)

    def _validate_selection(self) -> None:
        validate_selection(self)

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
        generate(self)

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
            ("venue", copy.get("xp_title", "Starting XP"), venue_view.render_venue(self)),
            ("type", "Character type", type_view.render_type(self)),
            ("faction", self.system.get_faction_picker_title(self._faction_role()), faction_view.render_faction(self)),
            (
                "archetype",
                copy.get("archetype_title", "Archetype"),
                archetype_view.render_archetype(self),
            ),
            (
                "sub_archetype",
                copy.get("sub_archetype_title", "Subtype"),
                archetype_view.render_sub_archetype(self),
            ),
            ("predator", copy.get("predator_title", "Predator type"), predator_view.render_predator(self)),
            ("generate", "Generate", generate_view.render_generate(self)),
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

    def _faction_role(self) -> str:
        return faction_view.faction_role(self)

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
        sheet_model = self.system.build_sheet_model(
            result,
            convictions=self._convictions(),
            convictions_seed=int(self.state["convictions_seed"]),
        )
        sheet_panel.appendChild(
            render_lotn_v5_sheet(
                sheet_model,
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
