"""Wizard state defaults, URL parsing, validation, and share options."""

from __future__ import annotations

import random
import traceback
from typing import TYPE_CHECKING, Any

from pyscript import window

from wod_chargen.core.share import (
    SharePayload,
    browser_share_url,
    decode_query,
    wizard_share_options,
)
from wod_chargen.defaults import DEFAULT_GAME_ID
from wod_chargen.games.lotn_v5.archetypes import archetypes_for_type, get_archetype
from wod_chargen.games.registry import get_game
from wod_chargen.venues import load_venue

if TYPE_CHECKING:
    from app.wizard import WizardApp


def default_state() -> dict[str, Any]:
    return {
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


def type_uses_predator(app: WizardApp) -> bool:
    return app.system.type_uses_predator(app.state["type"])


def build_share_options(app: WizardApp) -> dict[str, str]:
    opts = wizard_share_options(
        character_type=app.state["type"],
        arch=app.state["arch"],
        sub=app.state["sub"],
        clan=app.state.get("clan", ""),
        domitor_clan=app.state.get("domitor_clan", ""),
        predator=app.state.get("predator", ""),
        approval=app.state.get("approval", ""),
        venue_requires_approval_month=bool(
            app._venue_picker.get(app.state["venue"], {}).get("requires_approval_month")
        ),
        type_uses_predator=type_uses_predator(app),
    )
    if app.state.get("venue") == "custom_xp":
        opts["xp"] = str(app.state.get("xp_custom", "")).strip()
    return opts


def venue_continue_error(app: WizardApp) -> str | None:
    venue_id = app.state.get("venue", "")
    if venue_id == "custom_xp":
        raw = str(app.state.get("xp_custom", "")).strip()
        if not raw:
            return "Enter an XP amount."
        try:
            xp = int(raw)
        except ValueError:
            return "XP must be a whole number."
        if xp < 0:
            return "XP must be zero or greater."
        return None
    if app._venue_picker.get(venue_id, {}).get("requires_approval_month"):
        approval = str(app.state.get("approval", "")).strip()
        if not approval:
            return "Enter an approval month (YYYY-MM)."
    return None


def validate_selection(app: WizardApp) -> None:
    """Ensure arch/sub still exist after data changes or stale share URLs."""
    profiles = archetypes_for_type(app.state["type"])
    valid_arch = {p.id for p in profiles}
    if app.state["arch"] not in valid_arch:
        app.state["arch"] = profiles[0].id
    profile = get_archetype(app.state["arch"])
    valid_sub = {s.id for s in profile.sub_archetypes}
    if app.state["sub"] not in valid_sub:
        app.state["sub"] = profile.sub_archetypes[0].id
    if type_uses_predator(app):
        valid_pred = {p["id"] for p in app.system.get_predator_picker()}
        pred = app.state.get("predator") or ""
        if pred and pred not in valid_pred:
            app.state["predator"] = app.system.get_predator_picker()[0]["id"]


def share_payload(app: WizardApp) -> SharePayload:
    return SharePayload(
        seed=int(app.state["seed"]),
        convictions_seed=int(app.state["convictions_seed"]),
        game=app.state["game"],
        venue=app.state["venue"],
        options=build_share_options(app),
    )


def share_url(app: WizardApp) -> str:
    return browser_share_url(window.location.pathname, share_payload(app))


def sync_url(app: WizardApp) -> None:
    window.history.replaceState(None, "", share_url(app))


def parse_url(app: WizardApp) -> None:
    try:
        qs = window.location.search
        if not qs:
            return
        payload = decode_query(qs)
        app.state["seed"] = payload.seed
        if payload.convictions_seed is not None:
            app.state["convictions_seed"] = payload.convictions_seed
        app.state["game"] = payload.game
        app.system = get_game(payload.game)
        app._venue_picker = {v["id"]: v for v in app.system.get_venue_picker()}
        app.state["venue"] = payload.venue
        opts = payload.options
        for key in ("type", "clan", "domitor_clan", "arch", "sub", "predator", "approval"):
            if key in opts:
                app.state[key] = opts[key]
        if "xp" in opts:
            app.state["xp_custom"] = opts["xp"]
            app.state["venue"] = "custom_xp"
        validate_selection(app)
        generate(app)
        app.state["phase"] = "results" if app.state.get("result") else "build"
        app.state["unlocked_through"] = "generate"
    except Exception as exc:
        app.state["error"] = str(exc)
        app.state["phase"] = "landing"


def generate(app: WizardApp) -> None:
    try:
        validate_selection(app)
        venue = load_venue(app.state["venue"])
        result = app.system.generate(
            int(app.state["seed"]),
            build_share_options(app),
            venue,
        )
        app.state["result"] = result
        app.state["error"] = None
        try:
            sync_url(app)
        except Exception as sync_exc:
            app.state["error"] = f"Share URL sync failed: {sync_exc}"
    except Exception as exc:
        app.state["error"] = f"{exc}\n\n{traceback.format_exc()}"
        app.state["result"] = None
