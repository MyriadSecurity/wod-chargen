"""SPI player-facing build guide copy."""

from __future__ import annotations

from typing import Any

STRATEGY_TABS: tuple[tuple[str, str], ...] = (
    ("overview", "Overview"),
    ("creation", "Creation"),
    ("xp", "Experience"),
    ("reference", "Quick reference"),
)

STRATEGY_PAGE_TITLE = "How SPI Investigators Are Built"

STRATEGY_BLURB = (
    "Pick Division, Faction, Archetype, Subtype, and Affinity; the tool builds a CoD 2e "
    "investigator sheet for oneshots or NPCs. Hard rules first — Affinity caps, "
    "prerequisites, flat XP costs. Weights break ties among legal options."
)


def strategy_sections() -> dict[str, list[dict[str, Any]]]:
    return {
        "overview": _overview_sections(),
        "creation": _creation_sections(),
        "xp": _xp_sections(),
        "reference": _reference_sections(),
    }


def _overview_sections() -> list[dict[str, Any]]:
    return [
        {
            "title": "Overview",
            "paragraphs": [
                "SPI sheets use Chronicles of Darkness 2e traits (Presence, Weaponry) "
                "plus Society Affinity tracks. Built for oneshots and NPCs — not MES intake.",
                "Division, Faction, and Archetype bias spends. Affinity defaults from the "
                "archetype unless you lock one. Multi-Affinity is a toggle on generate.",
            ],
        },
        {
            "title": "Build order",
            "steps": [
                "Starting XP profile (MES floor, fixed 35, or custom)",
                "Division",
                "Faction",
                "Archetype",
                "Subtype",
                "Affinity (Any from archetype, or lock Ghost/Spirit/Mage/Fae/Vampire)",
                "Free creation: attributes, skills, specialties, merits, free Affinity 1",
                "XP spends with bias + prereq bundling",
                "Derived advantages and Integrity cap",
            ],
        },
        {
            "title": "Bias layers",
            "paragraphs": [
                "Preferences multiply across layers. Illegal options never enter the pool.",
            ],
            "table": {
                "headers": ["Layer", "Effect"],
                "rows": [
                    ["Archetype", "Attribute, skill, Affinity, and merit leans"],
                    ["Subtype", "Additive deltas that sharpen the primary fantasy"],
                    ["Division", "Soft skill/attribute tilt toward Society role"],
                    ["Faction", "Political lean (secrecy, hunter, diplomacy, …)"],
                    ["Affinity lock", "Forces primary Affinity track when not Any"],
                ],
            },
        },
    ]


def _creation_sections() -> list[dict[str, Any]]:
    return [
        {
            "title": "Attributes and skills",
            "paragraphs": [
                "Attributes start at 1. Free pools: primary 5 / secondary 4 / tertiary 3 "
                "across Mental, Physical, Social. Skills: 11 / 7 / 4 across the same columns. "
                "Three specialties. Seven general merit dots.",
            ],
        },
        {
            "title": "Affinity",
            "paragraphs": [
                "Free Affinity 1 on the primary type. Affinity merit dots per type are capped "
                "at 3 × Affinity rating. With multi-Affinity off, only one track receives dots.",
                "Max Integrity = 11 − sum of the top two Affinity ratings. Starting Integrity "
                "is min(7, max).",
            ],
        },
        {
            "title": "Division Status",
            "paragraphs": [
                "Generated sheets always record Division Status 1 (rules allow 1–2 at start).",
            ],
        },
    ]


def _xp_sections() -> list[dict[str, Any]]:
    return [
        {
            "title": "XP sources",
            "paragraphs": [
                "MES SPI Game XP floor starts at 35 on 2026-01-01 and rises +3 each month. "
                "Fixed 35 and custom amounts are also available. MC/Event/Bonus XP are out of "
                "scope for oneshot sheets.",
            ],
        },
        {
            "title": "Flat costs (per dot)",
            "table": {
                "headers": ["Trait", "XP"],
                "rows": [
                    ["Affinity", "5"],
                    ["Attribute", "4"],
                    ["Skill", "2"],
                    ["Integrity", "2"],
                    ["Specialty", "1"],
                    ["Merit", "1"],
                ],
            },
        },
        {
            "title": "Prerequisites",
            "paragraphs": [
                "When a desired merit needs unmet prereqs, the generator may buy the whole "
                "bundle (trait + missing dots) as one candidate cost. Messy fighting-style "
                "chains are soft-skipped.",
            ],
        },
    ]


def _reference_sections() -> list[dict[str, Any]]:
    return [
        {
            "title": "Sheet traits",
            "paragraphs": [
                "Social attribute is Presence (not Charisma). Physical skills include Weaponry "
                "(not Melee). Unskilled: Mental −3, Physical/Social −1.",
            ],
        },
        {
            "title": "Starter archetypes",
            "paragraphs": [
                "Eight primaries (Investigator, Occultist, Scholar, Guardian, Field Agent, "
                "Shadow, Diplomat, Caregiver), each with subtypes that sharpen the role "
                "(e.g. Detective / Forensic / Interviewer). Staff can add packs under "
                "data/archetypes/ and register them in the manifest.",
            ],
        },
        {
            "title": "Factions",
            "paragraphs": [
                "The Higher Ground, Humanity First, The Order of the Everlight, The Diplomats, "
                "Veritas.",
            ],
        },
    ]
