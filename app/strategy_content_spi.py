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
                "Three specialties.",
            ],
        },
        {
            "title": "Merits at creation",
            "paragraphs": [
                "Seven free merit dots. Up to three of those may be Affinity powers from the "
                "starting Affinity list; the rest are general. Division Status is recorded at 1 "
                "(no XP). Fighting-style trees and messy prereq chains are soft-skipped.",
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
                "MES SPI Game XP floor starts at 35 on 2026-01-01 and rises +3 each month "
                "(e.g. 2026-07 → 53). Fixed 35 and custom amounts are also available. "
                "MC / Event / Bonus XP are out of scope for oneshot sheets.",
            ],
        },
        {
            "title": "Flat costs (MES)",
            "paragraphs": [
                "SPI uses CoD 2e flat rates: each new dot costs the same XP, not old "
                "World of Darkness “new rating × factor” graduated pricing.",
            ],
            "table": {
                "headers": ["Trait", "XP"],
                "rows": [
                    ["Affinity", "5 per dot"],
                    ["Attribute", "4 per dot"],
                    ["Skill", "2 per dot"],
                    ["Integrity (increase / regain)", "2 per dot"],
                    ["Supernatural Resistance", "2 per dot"],
                    ["Specialty", "1"],
                    ["Merit (default)", "1 per dot"],
                    ["Willpower-dot regain", "1"],
                ],
            },
        },
        {
            "title": "Merits: flat vs fixed-rating vs Extra Touchstone",
            "paragraphs": [
                "Almost all merits are flat rate: 1 XP per dot. A ••• merit costs 3 XP "
                "whether bought as one package or raised one level at a time.",
                "Catalog shape differs: fixed-rating merits (e.g. ••• only) must be bought "
                "at full rating in one purchase; range merits (• to •••••) rise one dot per "
                "buy. Both still cost 1 XP per dot — the generator no longer penalizes "
                "fixed packages as multi-dot “jumps.”",
                "Exception: Extra Touchstone is graduated (1st dot 1 XP, 2nd 2 XP, … 5th "
                "5 XP; 15 XP total). Touchstones are omitted on oneshot sheets, so that "
                "merit is not purchased here.",
            ],
        },
        {
            "title": "XP mix",
            "paragraphs": [
                "After free creation, remaining XP is spent toward a jittered mix "
                "(normalized per character):",
            ],
            "table": {
                "headers": ["Area", "Target share"],
                "rows": [
                    ["Skills (+ extra specialties)", "~30%"],
                    ["Attributes", "~28%"],
                    ["Merits (general + Affinity powers)", "~27%"],
                    ["Affinity dots", "~15%"],
                ],
            },
        },
        {
            "title": "Prerequisites",
            "paragraphs": [
                "When a desired merit needs unmet prereqs, the generator may buy the whole "
                "bundle (trait + missing dots) as one candidate cost. Messy fighting-style "
                "chains are soft-skipped. Integrity and Willpower-dot regain are legal MES "
                "costs but are not on the oneshot spend loop.",
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
        {
            "title": "Derived advantages",
            "paragraphs": [
                "Health = Size 5 + Stamina. Speed = 5 + Strength + Dexterity. "
                "Willpower = Resolve + Composure. Initiative = Dexterity + Composure. "
                "Perception = Wits + Composure. Defense = lower of Wits/Dexterity + Athletics. "
                "Clash of Wills = highest Resistance attribute + Occult. "
                "Downtimes = Resolve + 1.",
            ],
        },
    ]
