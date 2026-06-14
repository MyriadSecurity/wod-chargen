#!/usr/bin/env python3
"""Build loresheets.json and loresheet_themes.json from LoTN pocket book (Ch. 6 pp. 159–175).

Run: python scripts/build_loresheet_data.py
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "wod_chargen/games/lotn_v5/data"
ARCH = DATA / "archetypes"

ARCHETYPES = [
    "diplomat",
    "enforcer",
    "predator",
    "criminal",
    "shadow",
    "scholar",
    "manipulator",
    "duelist",
    "occultist",
    "investigator",
    "artist",
    "alchemist",
]

CLANS = [
    "brujah",
    "gangrel",
    "malkavian",
    "nosferatu",
    "toreador",
    "tremere",
    "ventrue",
    "lasombra",
    "ministry",
    "hecata",
    "ravnos",
    "tzimisce",
    "salubri",
    "caitiff",
    "thin_blood",
]

# Pocket book loresheets — descriptions paraphrased from Ch. 6; mechanics in levels.
LORESHEETS: list[dict] = [
    {
        "id": "anarch_revolt",
        "label": "Anarch Revolt",
        "category": "organization",
        "restriction_sect": "anarch",
        "description": (
            "Student of the 14th–15th century Anarch Revolt who sees the same patterns in modern rebellion. "
            "Chronicles the past to steer the future and inspire gangmates under pressure."
        ),
        "archetype_biases": {
            "criminal": 1.65,
            "enforcer": 1.55,
            "predator": 1.25,
            "scholar": 1.35,
            "duelist": 1.2,
            "diplomat": 0.75,
            "manipulator": 0.85,
            "shadow": 0.9,
            "investigator": 0.8,
            "occultist": 0.65,
            "artist": 0.55,
            "alchemist": 0.45,
        },
        "clan_biases": {
            "brujah": 1.85,
            "gangrel": 1.55,
            "caitiff": 1.45,
            "nosferatu": 1.2,
            "malkavian": 1.1,
            "ventrue": 0.45,
            "tremere": 0.5,
            "toreador": 0.55,
        },
        "weight_notes": "Revolt historian and street agitator; Anarch sect; Brujah and outcast clans.",
    },
    {
        "id": "the_cobweb",
        "label": "The Cobweb",
        "category": "organization",
        "restriction_clan": "malkavian",
        "description": (
            "Tap the Malkavian Madness Network — sporadic psychic static connecting the clan. "
            "Ask the Cobweb questions, broadcast to other Malkavians, and pluck shared knowledge."
        ),
        "archetype_biases": {
            "scholar": 1.65,
            "occultist": 1.55,
            "manipulator": 1.45,
            "shadow": 1.25,
            "investigator": 1.15,
            "diplomat": 0.7,
            "enforcer": 0.5,
            "duelist": 0.45,
            "predator": 0.5,
            "criminal": 0.55,
            "artist": 1.1,
            "alchemist": 0.6,
        },
        "clan_biases": {"malkavian": 2.0},
        "weight_notes": "Malkavian-only; lore-seeker and oracle archetypes.",
    },
    {
        "id": "the_church_of_set",
        "label": "The Church of Set",
        "category": "organization",
        "restriction_clan": "ministry",
        "description": (
            "Hardline Setite orthodox who weaken other clans to pave the way for Set's resurrection. "
            "Cult congregation, degenerative healing rites, and stain-shaving faith."
        ),
        "archetype_biases": {
            "manipulator": 1.75,
            "occultist": 1.65,
            "criminal": 1.35,
            "diplomat": 1.15,
            "shadow": 1.2,
            "scholar": 1.1,
            "predator": 1.0,
            "artist": 0.85,
            "investigator": 0.75,
            "enforcer": 0.7,
            "duelist": 0.55,
            "alchemist": 0.6,
        },
        "clan_biases": {"ministry": 2.0},
        "weight_notes": "Ministry-only; corruptor and cult-leader builds.",
    },
    {
        "id": "the_circulatory_system",
        "label": "The Circulatory System",
        "category": "organization",
        "description": (
            "Blood trafficking network tracking vessel Resonance — transporters, smugglers, scientists, and consumers. "
            "Secure transit, upstate farms, and sommelier secrets."
        ),
        "archetype_biases": {
            "alchemist": 1.85,
            "criminal": 1.7,
            "predator": 1.6,
            "scholar": 1.45,
            "shadow": 1.35,
            "manipulator": 1.2,
            "investigator": 1.0,
            "diplomat": 0.75,
            "occultist": 0.9,
            "enforcer": 0.85,
            "artist": 0.5,
            "duelist": 0.45,
        },
        "clan_biases": {
            "tremere": 1.35,
            "ministry": 1.3,
            "nosferatu": 1.25,
            "ventrue": 1.15,
            "hecata": 1.2,
            "toreador": 1.0,
        },
        "weight_notes": "Blood commerce and resonance science; thin-blood alchemist peak fit.",
    },
    {
        "id": "convention_of_thorns",
        "label": "Convention of Thorns",
        "category": "organization",
        "description": (
            "Historian of the Camarilla's founding treaty — signatory descendant or archivist who weaponizes "
            "Tradition lore in negotiations with Camarilla and Anarch alike."
        ),
        "archetype_biases": {
            "diplomat": 1.85,
            "scholar": 1.75,
            "shadow": 1.35,
            "investigator": 1.25,
            "manipulator": 1.2,
            "occultist": 1.0,
            "artist": 0.85,
            "enforcer": 0.55,
            "criminal": 0.5,
            "predator": 0.45,
            "duelist": 0.5,
            "alchemist": 0.4,
        },
        "clan_biases": {
            "ventrue": 1.55,
            "tremere": 1.45,
            "toreador": 1.35,
            "lasombra": 1.2,
            "nosferatu": 1.15,
            "brujah": 0.7,
        },
        "weight_notes": "Camarilla historian and negotiator; court and archive themes.",
    },
    {
        "id": "descendant_of_hardestadt",
        "label": "Descendant of Hardestadt",
        "category": "bloodline",
        "restriction_clan": "ventrue",
        "description": (
            "Scion of the destroyed Camarilla founder — limitless Ventrue wealth, leadership training, "
            "and domination that auto-succeeds on mortal targets."
        ),
        "archetype_biases": {
            "diplomat": 1.85,
            "manipulator": 1.5,
            "enforcer": 1.25,
            "scholar": 1.0,
            "investigator": 0.9,
            "shadow": 0.75,
            "duelist": 0.7,
            "artist": 0.65,
            "predator": 0.55,
            "criminal": 0.4,
            "occultist": 0.45,
            "alchemist": 0.35,
        },
        "clan_biases": {"ventrue": 2.0},
        "weight_notes": "Ventrue-only; Ivory Tower prince-in-waiting.",
    },
    {
        "id": "descendant_of_helena",
        "label": "Descendant of Helena",
        "category": "bloodline",
        "restriction_clan": "toreador",
        "description": (
            "Lineage of legendary Toreador beauty — master artist, forgiven social trespasses, "
            "and licensed Succubus Club franchise."
        ),
        "archetype_biases": {
            "artist": 1.95,
            "diplomat": 1.65,
            "manipulator": 1.55,
            "scholar": 0.9,
            "shadow": 0.65,
            "enforcer": 0.45,
            "predator": 0.5,
            "criminal": 0.55,
            "duelist": 0.7,
            "investigator": 0.6,
            "occultist": 0.5,
            "alchemist": 0.45,
        },
        "clan_biases": {"toreador": 2.0},
        "weight_notes": "Toreador-only; fame, performance, and nightclub patron.",
    },
    {
        "id": "descendant_of_karl_schrekt",
        "label": "Descendant of Karl Schrekt",
        "category": "bloodline",
        "restriction_clan": "tremere",
        "description": (
            "Heir to the former Justicar's paranoid ritual prep, supernatural archive, and surveillance tradecraft "
            "against sect enemies."
        ),
        "archetype_biases": {
            "occultist": 1.85,
            "scholar": 1.65,
            "investigator": 1.55,
            "shadow": 1.45,
            "diplomat": 1.0,
            "manipulator": 1.05,
            "enforcer": 0.75,
            "criminal": 0.55,
            "predator": 0.5,
            "duelist": 0.45,
            "artist": 0.4,
            "alchemist": 0.65,
        },
        "clan_biases": {"tremere": 2.0},
        "weight_notes": "Tremere-only; blood sorcery, lore, and hunter mindset.",
    },
    {
        "id": "descendant_of_montano",
        "label": "Descendant of Montano",
        "category": "bloodline",
        "restriction_clan": "lasombra",
        "description": (
            "Lasombra honor-lineage tied to the Abyss — clan resources, remorse-driven Humanity, "
            "and session-swap Oblivion powers under Montano's tutelage."
        ),
        "archetype_biases": {
            "shadow": 1.85,
            "manipulator": 1.65,
            "diplomat": 1.45,
            "occultist": 1.35,
            "enforcer": 1.15,
            "investigator": 1.0,
            "scholar": 0.95,
            "duelist": 0.85,
            "predator": 0.7,
            "criminal": 0.65,
            "artist": 0.75,
            "alchemist": 0.45,
        },
        "clan_biases": {"lasombra": 2.0},
        "weight_notes": "Lasombra-only; Camarilla loyalist shadow courtier.",
    },
    {
        "id": "descendant_of_tyler",
        "label": "Descendant of Tyler",
        "category": "bloodline",
        "restriction_clan": "brujah",
        "description": (
            "Tyler's lineage — rebellion funding, controlled Fury, and Furore strike teams against tyrannical elders."
        ),
        "archetype_biases": {
            "enforcer": 1.75,
            "criminal": 1.6,
            "duelist": 1.35,
            "predator": 1.25,
            "diplomat": 0.85,
            "scholar": 0.9,
            "shadow": 0.75,
            "manipulator": 0.7,
            "investigator": 0.65,
            "occultist": 0.5,
            "artist": 0.55,
            "alchemist": 0.4,
        },
        "clan_biases": {"brujah": 2.0},
        "weight_notes": "Brujah-only; Anarch champion and street revolutionary.",
    },
    {
        "id": "descendant_of_vasantasena",
        "label": "Descendant of Vasantasena",
        "category": "bloodline",
        "restriction_clan": "malkavian",
        "description": (
            "Anti–Blood Bond Malkavian zealot — scent Bonds, resist mental control, and ritually destroy thralls."
        ),
        "archetype_biases": {
            "manipulator": 1.75,
            "shadow": 1.55,
            "occultist": 1.45,
            "investigator": 1.25,
            "scholar": 1.15,
            "diplomat": 1.0,
            "criminal": 0.9,
            "enforcer": 0.75,
            "predator": 0.65,
            "duelist": 0.55,
            "artist": 0.85,
            "alchemist": 0.5,
        },
        "clan_biases": {"malkavian": 2.0},
        "weight_notes": "Malkavian-only; freedom fighter against Bonds and hierarchy.",
    },
    {
        "id": "descendant_of_xaviar",
        "label": "Descendant of Xaviar",
        "category": "bloodline",
        "restriction_clan": "gangrel",
        "description": (
            "Xaviar's guilt-ridden lineage — detect torpid Kindred, bat-hybrid flight, and Nomad Hounds "
            "against supernatural threats."
        ),
        "archetype_biases": {
            "predator": 1.85,
            "enforcer": 1.45,
            "shadow": 1.35,
            "duelist": 1.1,
            "investigator": 1.05,
            "scholar": 0.85,
            "criminal": 0.75,
            "occultist": 0.7,
            "diplomat": 0.55,
            "manipulator": 0.5,
            "artist": 0.45,
            "alchemist": 0.4,
        },
        "clan_biases": {"gangrel": 2.0},
        "weight_notes": "Gangrel-only; Antediluvian truth-seeker and wilderness defender.",
    },
    {
        "id": "descendant_of_zao_xue",
        "label": "Descendant of Zao-Xue",
        "category": "bloodline",
        "restriction_clan": "salubri",
        "description": (
            "Salubri Watcher — hidden scholar havens, supernatural encyclopedia, and rotating shadow contacts."
        ),
        "archetype_biases": {
            "scholar": 1.85,
            "occultist": 1.55,
            "investigator": 1.45,
            "diplomat": 1.25,
            "shadow": 1.2,
            "manipulator": 1.0,
            "artist": 0.7,
            "predator": 0.55,
            "enforcer": 0.5,
            "criminal": 0.45,
            "duelist": 0.4,
            "alchemist": 0.65,
        },
        "clan_biases": {"salubri": 2.0},
        "weight_notes": "Salubri-only; lore hunter and supernatural threat analyst.",
    },
    {
        "id": "descendant_of_zelios",
        "label": "Descendant of Zelios",
        "category": "bloodline",
        "restriction_clan": "nosferatu",
        "description": (
            "Nosferatu architect lineage — building schematics, fortress haven, and city Labyrinth travel."
        ),
        "archetype_biases": {
            "shadow": 1.85,
            "investigator": 1.55,
            "criminal": 1.45,
            "scholar": 1.25,
            "occultist": 1.0,
            "enforcer": 0.85,
            "predator": 0.8,
            "manipulator": 0.75,
            "diplomat": 0.55,
            "duelist": 0.5,
            "artist": 0.45,
            "alchemist": 0.5,
        },
        "clan_biases": {"nosferatu": 2.0},
        "weight_notes": "Nosferatu-only; warren master and urban planner.",
    },
    {
        "id": "the_first_inquisition",
        "label": "The First Inquisition",
        "category": "organization",
        "description": (
            "Scholar of the First Inquisition who reads Society of St. Leopold patterns — faith sensitivity, "
            "Church mole, and Black Spot hideouts."
        ),
        "archetype_biases": {
            "investigator": 1.85,
            "shadow": 1.75,
            "scholar": 1.55,
            "occultist": 1.35,
            "manipulator": 1.15,
            "diplomat": 0.9,
            "criminal": 0.85,
            "enforcer": 0.7,
            "predator": 0.65,
            "duelist": 0.5,
            "artist": 0.45,
            "alchemist": 0.55,
        },
        "clan_biases": {
            "nosferatu": 1.45,
            "tremere": 1.35,
            "lasombra": 1.25,
            "malkavian": 1.15,
            "ventrue": 1.1,
        },
        "weight_notes": "Hunter-evasion and Church infiltration; paranoid survivor.",
    },
    {
        "id": "firstlight",
        "label": "FIRSTLIGHT",
        "category": "organization",
        "description": (
            "Target of the global intelligence hunt for Kindred — erased records, urban evasion, "
            "and a manipulated inside mole."
        ),
        "archetype_biases": {
            "shadow": 1.85,
            "investigator": 1.75,
            "criminal": 1.55,
            "manipulator": 1.45,
            "scholar": 1.1,
            "occultist": 0.95,
            "predator": 0.85,
            "diplomat": 0.75,
            "enforcer": 0.65,
            "duelist": 0.55,
            "artist": 0.5,
            "alchemist": 0.7,
        },
        "clan_biases": {
            "nosferatu": 1.5,
            "lasombra": 1.45,
            "malkavian": 1.2,
            "gangrel": 1.15,
            "tremere": 1.1,
            "ventrue": 0.85,
        },
        "weight_notes": "Second Inquisition survival; spy and fixer archetypes.",
    },
    {
        "id": "golconda",
        "label": "Golconda",
        "category": "organization",
        "description": (
            "Seeker (or debunker) of Saulot's path — efficient feeding, controlled Beast, and Bane suppression "
            "at high Humanity."
        ),
        "archetype_biases": {
            "scholar": 1.75,
            "diplomat": 1.55,
            "occultist": 1.45,
            "investigator": 1.15,
            "artist": 0.85,
            "manipulator": 0.75,
            "shadow": 0.7,
            "predator": 0.55,
            "enforcer": 0.45,
            "criminal": 0.4,
            "duelist": 0.4,
            "alchemist": 0.6,
        },
        "clan_biases": {
            "salubri": 1.85,
            "gangrel": 1.35,
            "malkavian": 1.2,
            "toreador": 1.1,
            "ventrue": 1.0,
        },
        "weight_notes": "Humanity-focused mystic path; Salubri natural fit.",
    },
    {
        "id": "high_clan",
        "label": "High Clan",
        "category": "organization",
        "description": (
            "Noblesse oblige High Clan pedigree — etiquette training, elite mortal connections, "
            "and treating your Bane as blessing."
        ),
        "archetype_biases": {
            "diplomat": 1.85,
            "artist": 1.65,
            "manipulator": 1.55,
            "scholar": 1.05,
            "duelist": 0.85,
            "investigator": 0.65,
            "shadow": 0.55,
            "enforcer": 0.5,
            "predator": 0.45,
            "criminal": 0.35,
            "occultist": 0.55,
            "alchemist": 0.4,
        },
        "clan_biases": {
            "ventrue": 1.75,
            "toreador": 1.7,
            "lasombra": 1.55,
            "tzimisce": 1.5,
            "ministry": 1.25,
            "tremere": 1.15,
            "brujah": 0.65,
            "nosferatu": 0.45,
            "gangrel": 0.45,
        },
        "weight_notes": "Court aristocrat; Toreador/Ventrue/Lasombra/Tzimisce peak.",
    },
    {
        "id": "low_clan",
        "label": "Low Clan",
        "category": "organization",
        "description": (
            "Fringe-clan solidarity — thick hide against High Clan slights, underworld kinship, "
            "and sabotaging rivals' mortal connections."
        ),
        "archetype_biases": {
            "criminal": 1.65,
            "enforcer": 1.55,
            "shadow": 1.5,
            "predator": 1.4,
            "investigator": 1.05,
            "duelist": 1.0,
            "manipulator": 0.85,
            "scholar": 0.75,
            "occultist": 0.7,
            "diplomat": 0.45,
            "artist": 0.5,
            "alchemist": 0.55,
        },
        "clan_biases": {
            "nosferatu": 1.65,
            "gangrel": 1.6,
            "malkavian": 1.55,
            "brujah": 1.45,
            "caitiff": 1.5,
            "tremere": 1.15,
            "ventrue": 0.35,
            "toreador": 0.4,
        },
        "weight_notes": "Street and counter-culture; Low Clan solidarity.",
    },
    {
        "id": "scion_of_lucretia",
        "label": "Scion of Lucretia",
        "category": "organization",
        "restriction_sect": "camarilla",
        "description": (
            "Student of Archon Lucretia Wright — political peacemaker, Camarilla city rebuilding, "
            "and guaranteed-safe parley Armistices."
        ),
        "archetype_biases": {
            "diplomat": 1.95,
            "scholar": 1.45,
            "manipulator": 1.35,
            "investigator": 1.05,
            "artist": 1.0,
            "shadow": 0.65,
            "enforcer": 0.55,
            "occultist": 0.6,
            "criminal": 0.45,
            "predator": 0.4,
            "duelist": 0.45,
            "alchemist": 0.35,
        },
        "clan_biases": {
            "ventrue": 1.65,
            "tremere": 1.45,
            "toreador": 1.35,
            "lasombra": 1.25,
            "nosferatu": 1.15,
            "brujah": 0.55,
        },
        "weight_notes": "Camarilla-only; diplomat and archon peacemaker.",
    },
    {
        "id": "sect_war_veteran",
        "label": "Sect War Veteran",
        "category": "organization",
        "description": (
            "Survivor of the Camarilla–Sabbat wars — Masquerade-safe combat lore, sect rewards, "
            "out-of-clan discipline from old comrades, and fortress havens."
        ),
        "archetype_biases": {
            "enforcer": 1.85,
            "predator": 1.65,
            "duelist": 1.55,
            "shadow": 1.5,
            "criminal": 1.25,
            "investigator": 1.1,
            "scholar": 0.85,
            "manipulator": 0.75,
            "diplomat": 0.65,
            "occultist": 0.7,
            "artist": 0.45,
            "alchemist": 0.4,
        },
        "clan_biases": {
            "brujah": 1.45,
            "gangrel": 1.4,
            "nosferatu": 1.35,
            "tremere": 1.25,
            "ventrue": 1.2,
            "lasombra": 1.15,
            "malkavian": 1.1,
        },
        "weight_notes": "Combat veteran and siege strategist; cross-sect war stories.",
    },
    {
        "id": "the_society_of_heralds",
        "label": "The Society of Heralds",
        "category": "organization",
        "restriction_sect": "camarilla",
        "description": (
            "Cross-domain Herald network — gossip on visiting Kindred, tenure protection, "
            "and social-elite Camarilla influence."
        ),
        "archetype_biases": {
            "diplomat": 1.9,
            "artist": 1.65,
            "manipulator": 1.55,
            "scholar": 1.15,
            "investigator": 1.1,
            "shadow": 0.85,
            "enforcer": 0.45,
            "predator": 0.4,
            "criminal": 0.45,
            "duelist": 0.5,
            "occultist": 0.55,
            "alchemist": 0.35,
        },
        "clan_biases": {
            "toreador": 1.65,
            "ventrue": 1.55,
            "tremere": 1.4,
            "lasombra": 1.25,
            "nosferatu": 1.1,
        },
        "weight_notes": "Camarilla-only; Harpy-adjacent social intelligence.",
    },
    {
        "id": "the_trinity",
        "label": "The Trinity",
        "category": "organization",
        "description": (
            "Revivalist of Constantinople's Michael–Dracon–Antonius utopia — philosophical patrons, "
            "Frenzy aid, and a new Trinity that sheds Stains."
        ),
        "archetype_biases": {
            "diplomat": 1.75,
            "scholar": 1.65,
            "artist": 1.55,
            "occultist": 1.45,
            "manipulator": 1.2,
            "investigator": 0.85,
            "shadow": 0.75,
            "enforcer": 0.55,
            "predator": 0.45,
            "criminal": 0.4,
            "duelist": 0.5,
            "alchemist": 0.45,
        },
        "clan_biases": {
            "toreador": 1.55,
            "ventrue": 1.5,
            "tzimisce": 1.65,
            "lasombra": 1.2,
            "salubri": 1.15,
        },
        "weight_notes": "Utopian philosopher; Toreador/Ventrue/Tzimisce trinity echo.",
    },
    {
        "id": "the_week_of_nightmares",
        "label": "The Week of Nightmares",
        "category": "organization",
        "description": (
            "Student or survivor of the Ravnos Antediluvian's rampage — Night Network waystation, "
            "escape artist, and Red Star omens."
        ),
        "archetype_biases": {
            "occultist": 1.65,
            "scholar": 1.55,
            "shadow": 1.5,
            "predator": 1.35,
            "criminal": 1.25,
            "investigator": 1.15,
            "manipulator": 1.05,
            "enforcer": 0.85,
            "diplomat": 0.65,
            "artist": 0.75,
            "duelist": 0.7,
            "alchemist": 0.6,
        },
        "clan_biases": {
            "ravnos": 1.9,
            "malkavian": 1.4,
            "gangrel": 1.15,
            "nosferatu": 1.1,
            "tzimisce": 1.05,
        },
        "weight_notes": "Apocalyptic omen-watcher; Ravnos network hub.",
    },
]

LEVELS: dict[str, list[dict]] = {
    "anarch_revolt": [
        {"dots": 1, "label": "Hold the Line", "id": "hold_the_line"},
        {"dots": 2, "label": "Mutual Support", "id": "mutual_support"},
        {"dots": 3, "label": "In Open Rebellion", "id": "in_open_rebellion"},
    ],
    "the_cobweb": [
        {"dots": 1, "label": "A Break in the Static", "id": "a_break_in_the_static"},
        {"dots": 2, "label": "The Call", "id": "the_call"},
        {"dots": 3, "label": "Pluck the Strands", "id": "pluck_the_strands"},
    ],
    "the_church_of_set": [
        {"dots": 1, "label": "Congregation", "id": "congregation"},
        {"dots": 2, "label": "Degenerative Process", "id": "degenerative_process"},
        {"dots": 3, "label": "Avatar of Belief", "id": "avatar_of_belief"},
    ],
    "the_circulatory_system": [
        {"dots": 1, "label": "Secure Transit", "id": "secure_transit"},
        {"dots": 2, "label": "Farm Upstate", "id": "farm_upstate"},
        {"dots": 3, "label": "Blood Sommelier", "id": "blood_sommelier"},
    ],
    "convention_of_thorns": [
        {"dots": 1, "label": "Thorns Historian", "id": "thorns_historian"},
        {"dots": 2, "label": "Archivist", "id": "archivist"},
        {"dots": 3, "label": "Lessons of the Convention", "id": "lessons_of_the_convention"},
    ],
    "descendant_of_hardestadt": [
        {"dots": 1, "label": "Wealth", "id": "wealth"},
        {"dots": 2, "label": "Pedigree", "id": "pedigree"},
        {"dots": 3, "label": "Control", "id": "control"},
    ],
    "descendant_of_helena": [
        {"dots": 1, "label": "Real Talent", "id": "real_talent"},
        {"dots": 2, "label": "Popular", "id": "popular"},
        {"dots": 3, "label": "Succubus Club Franchise", "id": "succubus_club_franchise"},
    ],
    "descendant_of_karl_schrekt": [
        {"dots": 1, "label": "Ritual Preparedness", "id": "ritual_preparedness"},
        {"dots": 2, "label": "Know the World", "id": "know_the_world"},
        {"dots": 3, "label": "Surveillance", "id": "surveillance"},
    ],
    "descendant_of_montano": [
        {"dots": 1, "label": "Siblings in Darkness", "id": "siblings_in_darkness"},
        {"dots": 2, "label": "Purity of Remorse", "id": "purity_of_remorse"},
        {"dots": 3, "label": "Abyssal Appearance", "id": "abyssal_appearance"},
    ],
    "descendant_of_tyler": [
        {"dots": 1, "label": "Champion of the Cause", "id": "champion_of_the_cause"},
        {"dots": 2, "label": "Tyler's Mercy", "id": "tylers_mercy"},
        {"dots": 3, "label": "The Furores", "id": "the_furores"},
    ],
    "descendant_of_vasantasena": [
        {"dots": 1, "label": "Scent the Bond", "id": "scent_the_bond"},
        {"dots": 2, "label": "Agent of Chaos", "id": "agent_of_chaos"},
        {"dots": 3, "label": "Destroy the Bond", "id": "destroy_the_bond"},
    ],
    "descendant_of_xaviar": [
        {"dots": 1, "label": "Where the Bodies are Buried", "id": "where_the_bodies_are_buried"},
        {"dots": 2, "label": "Monstrous Bat", "id": "monstrous_bat"},
        {"dots": 3, "label": "Loyal Hounds", "id": "loyal_hounds"},
    ],
    "descendant_of_zao_xue": [
        {"dots": 1, "label": "Hidden Scholar", "id": "hidden_scholar"},
        {"dots": 2, "label": "Supernatural Encyclopedia", "id": "supernatural_encyclopedia"},
        {"dots": 3, "label": "Shadow Network", "id": "shadow_network"},
    ],
    "descendant_of_zelios": [
        {"dots": 1, "label": "Architect", "id": "architect"},
        {"dots": 2, "label": "Sanctuary", "id": "sanctuary"},
        {"dots": 3, "label": "The Labyrinth", "id": "the_labyrinth"},
    ],
    "the_first_inquisition": [
        {"dots": 1, "label": "Mistakes of the Past", "id": "mistakes_of_the_past"},
        {"dots": 2, "label": "The Second Act", "id": "the_second_act"},
        {"dots": 3, "label": "Black Spot", "id": "black_spot"},
    ],
    "firstlight": [
        {"dots": 1, "label": "No Records Found", "id": "no_records_found"},
        {"dots": 2, "label": "Evasion", "id": "evasion"},
        {"dots": 3, "label": "Friend on the Inside", "id": "friend_on_the_inside"},
    ],
    "golconda": [
        {"dots": 1, "label": "Satisfy the Hunger", "id": "satisfy_the_hunger"},
        {"dots": 2, "label": "Saulot's Disciple", "id": "saulots_disciple"},
        {"dots": 3, "label": "Overcoming Banes", "id": "overcoming_banes"},
    ],
    "high_clan": [
        {"dots": 1, "label": "Peacock", "id": "peacock"},
        {"dots": 2, "label": "Friends in High Places", "id": "friends_in_high_places"},
        {"dots": 3, "label": "Blessed, Not Cursed", "id": "blessed_not_cursed"},
    ],
    "low_clan": [
        {"dots": 1, "label": "Thick Hide", "id": "thick_hide"},
        {"dots": 2, "label": "Uncanny Kinship", "id": "uncanny_kinship"},
        {"dots": 3, "label": "Critical Incident", "id": "critical_incident"},
    ],
    "scion_of_lucretia": [
        {"dots": 1, "label": "Peacemaker", "id": "peacemaker"},
        {"dots": 2, "label": "Revitalization", "id": "revitalization"},
        {"dots": 3, "label": "Armistice", "id": "armistice"},
    ],
    "sect_war_veteran": [
        {"dots": 1, "label": "Survivor", "id": "survivor"},
        {"dots": 2, "label": "Soldier", "id": "soldier"},
        {"dots": 3, "label": "Strategist", "id": "strategist"},
    ],
    "the_society_of_heralds": [
        {"dots": 1, "label": "Hot Gossip", "id": "hot_gossip"},
        {"dots": 2, "label": "Tenured Protection", "id": "tenured_protection"},
        {"dots": 3, "label": "Social Elite", "id": "social_elite"},
    ],
    "the_trinity": [
        {"dots": 1, "label": "Constantinople", "id": "constantinople"},
        {"dots": 2, "label": "The Dream", "id": "the_dream"},
        {"dots": 3, "label": "The New Trinity", "id": "the_new_trinity"},
    ],
    "the_week_of_nightmares": [
        {"dots": 1, "label": "The Night Network", "id": "the_night_network"},
        {"dots": 2, "label": "Survivor", "id": "survivor"},
        {"dots": 3, "label": "The Red Star", "id": "the_red_star"},
    ],
}


def _restriction_label(entry: dict) -> str | None:
    if entry.get("restriction_clan"):
        return f"{entry['restriction_clan'].replace('_', ' ').title()} Only"
    if entry.get("restriction_sect") == "anarch":
        return "Anarch Only"
    if entry.get("restriction_sect") == "camarilla":
        return "Camarilla Only"
    return None


def build_loresheets_json() -> dict:
    sheets = []
    for entry in LORESHEETS:
        ls_id = entry["id"]
        sheets.append(
            {
                "id": ls_id,
                "label": entry["label"],
                "category": entry["category"],
                "description": entry["description"],
                "restriction": _restriction_label(entry),
                "restriction_clan": entry.get("restriction_clan"),
                "restriction_sect": entry.get("restriction_sect"),
                "levels": LEVELS[ls_id],
            }
        )
    return {
        "source_ref": {
            "book": "Laws of the Night pocket edition",
            "chapter": 6,
            "pages": "159-175",
            "srd": "https://www.oneworldofdarkness.com/laws-of-the-night/loresheets",
            "built_by": "scripts/build_loresheet_data.py",
        },
        "rules": {
            "max_per_character": 1,
            "cost_per_dot_xp": 3,
            "max_dots": 3,
            "levels_need_not_be_in_order": True,
        },
        "loresheets": sheets,
    }


def build_themes_json() -> dict:
    themes: dict[str, dict] = {}
    for entry in LORESHEETS:
        ls_id = entry["id"]
        themes[ls_id] = {
            "label": entry["label"],
            "weight_notes": entry["weight_notes"],
            "archetype_biases": entry["archetype_biases"],
            "clan_biases": entry["clan_biases"],
        }
    return {
        "source_ref": {
            "book": "Laws of the Night pocket edition",
            "chapter": 6,
            "pages": "159-175",
        },
        "notes": (
            "Procedural pick weights for one loresheet per character. "
            "Clan-restricted sheets use 2.0 on-clan; wrong clan is ineligible in generator. "
            "Sect restrictions are soft-biased until sect is a wizard input."
        ),
        "loresheets": themes,
    }


def apply_archetype_biases(themes: dict) -> None:
    arch_blocks: dict[str, dict[str, float]] = {a: {} for a in ARCHETYPES}
    for ls_id, block in themes["loresheets"].items():
        for arch_id, bias in block["archetype_biases"].items():
            arch_blocks[arch_id][ls_id] = float(bias)

    for arch_id, biases in arch_blocks.items():
        path = ARCH / f"{arch_id}.json"
        data = json.loads(path.read_text())
        data["loresheet_biases"] = dict(sorted(biases.items()))
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def apply_clan_biases(themes: dict) -> None:
    clans_path = DATA / "clans.json"
    clans = json.loads(clans_path.read_text())
    clan_blocks: dict[str, dict[str, float]] = {c: {} for c in clans if c != "thin_blood"}

    for ls_id, block in themes["loresheets"].items():
        for clan_id, bias in block["clan_biases"].items():
            if clan_id in clan_blocks:
                clan_blocks[clan_id][ls_id] = float(bias)

    for clan_id, clan in clans.items():
        if clan_id == "thin_blood":
            continue
        clan["loresheet_biases"] = dict(sorted(clan_blocks.get(clan_id, {}).items()))
    clans_path.write_text(json.dumps(clans, indent=2, ensure_ascii=False) + "\n")


def main() -> None:
    loresheets = build_loresheets_json()
    themes = build_themes_json()
    (DATA / "loresheets.json").write_text(json.dumps(loresheets, indent=2, ensure_ascii=False) + "\n")
    (DATA / "loresheet_themes.json").write_text(json.dumps(themes, indent=2, ensure_ascii=False) + "\n")
    apply_archetype_biases(themes)
    apply_clan_biases(themes)
    print(f"Wrote {len(loresheets['loresheets'])} loresheets")
    print(f"Applied biases to {len(ARCHETYPES)} archetypes and clans.json")


if __name__ == "__main__":
    main()
