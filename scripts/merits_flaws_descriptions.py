"""Short LoTN pocket-book descriptions for merits and flaws (Chapter 7).

Source: reference/lotn_v5/laws_of_the_night_pocket.pdf (Merits & Flaws, pp. 177–190).
Used by scripts/enrich_merits_flaws_descriptions.py and import_mes_tables.py.
"""

from __future__ import annotations

# id -> one- or two-sentence summary for procedural weighting / UI hints
DESCRIPTIONS: dict[str, str] = {
    # Bonding merits
    "bond_resistance": (
        "Easier to resist the Blood Bond; each dot reduces Defiance check difficulty by one."
    ),
    "short_bond": (
        "Bond decays faster: reduce Bond Strength by two each month without feeding from your regnant "
        "(still need one successful Defiance check that month)."
    ),
    "sympathy_pains": (
        "Whenever any of your thralls take Aggravated Damage, you feel a twinge signaling they are in danger."
    ),
    "unbondable": "Cannot be Blood Bound. Must be purchased at character creation.",
    # Connection merits
    "linguistics": (
        "Each dot grants two extra languages you may speak and/or write beyond your native tongue "
        "and the game's local common language."
    ),
    "cobbler": (
        "Can create and improve Masks for yourself and others using downtime actions. "
        "Prerequisite: Mask (••)."
    ),
    "phenom": (
        "Extremely talented performer, academic, or craftsperson. Choose Academics, Crafts, or Performance; "
        "gain an extra specialty per dot in that Skill. May purchase once per listed Skill."
    ),
    "zeroed": (
        "No fingerprints, DNA, or facial recognition on file; name searches come up empty. "
        "Cannot take both Zeroed and Known Blankbody. Prerequisite: Mask (•••)."
    ),
    # Feeding merits
    "bloodhound": (
        "Identify a mortal's Blood Resonance within five steps (simple action, then Resolve + Awareness vs. 3). "
        "Ghouls may purchase."
    ),
    "iron_gullet": (
        "Can feed from stale, bagged, or long-dead blood. Ventrue and Blood Potency 3+ cannot benefit."
    ),
    "viscosity": (
        "Blood does not dilute after tapping a Dyscrasia; each dot allows one additional Dyscrasia tap per session "
        "(still only one Dyscrasia at a time)."
    ),
    # Ghoul merits
    "blood_empathy": (
        "Stronger bond to your regnant: sense their emotional state while in their presence; "
        "feel a twinge when they take aggravated damage."
    ),
    "vampiric_visage": (
        "Aura reads vampiric; heartbeat hard to detect, teeth appear fang-like, breath nearly undetectable."
    ),
    # Mythical merits
    "loremaster": "Encyclopedic supernatural knowledge; +2 bonus to all Lore checks.",
    "medium": (
        "Channel to the Shadowlands: sense and hear ghosts within 15 steps; "
        "ghosts may become visible to you alone without spending Pathos."
    ),
    # Physical merits
    "ambidextrous": (
        "Use both hands with equal dexterity; dual-wield benefits, staggered firearm reload, "
        "disarm targets only one held weapon."
    ),
    "eat_food": (
        "May consume food and drink (not blood) regardless of Humanity; provides no nourishment "
        "and must be expelled before resting."
    ),
    "light_sleeper": (
        "Automatically wake in dangerous situations; may stay awake 30 minutes free, "
        "then spend Willpower for up to one more hour."
    ),
    # Psychological merits
    "calm_heart": (
        "Great emotional control; reduce all Frenzy trigger difficulty by two "
        "(Brujah gain no benefit vs. Fury Frenzy)."
    ),
    "common_sense": (
        "Twice per game, ask the Storyteller one risk-assessment question about the current situation "
        "and receive a truthful answer."
    ),
    # Thin-blood merits (no dot cost)
    "anarch_comrades": (
        "Local Anarch vampires will exchange major and life boons with you; without it, "
        "non-thin-blood Anarchs may refuse major/life boons."
    ),
    "camarilla_contact": (
        "A friendly Camarilla vampire holds minor/trivial boons for you and keeps your thin-blood nature secret."
    ),
    "catenating_blood": (
        "Blood strong enough to Blood Bond, create ghouls, and Embrace (embraced child is also thin-blood)."
    ),
    "day_drinker": (
        "No sunlight damage; instead halve health boxes while exposed, cannot use Disciplines/Alchemy in sun, "
        "and lose Willpower if awake more than two days."
    ),
    "discipline_affinity": (
        "Affinity for one Discipline: gain one free dot and may buy more at out-of-clinic costs "
        "in addition to resonance-fed Discipline."
    ),
    "lifelike": (
        "Biologically identical to a mortal at all times; mundane and supernatural scrutiny "
        "(except sun damage) reads human."
    ),
    "thin_blood_alchemist": (
        "Know Thin-Blood Alchemy: first dot and one Formula free; buy more dots and Formulae with XP."
    ),
    "vampiric_resilience": (
        "Take damage and heal like a full vampire rather than a mortal."
    ),
    # Bonding flaws
    "bond_at_first_taste": (
        "Bond at the first drink of vampire blood; thrall after one drink with Bond Strength starting at one."
    ),
    "bond_junkie": (
        "The Bond feels sweeter; increase Defiance check difficulty by this Flaw's dot rating."
    ),
    "long_bond": (
        "Bond decays slowly: reduce Bond Strength by one every three months without feeding from regnant."
    ),
    "symbiotic_dependency": (
        "Physical link to regnant: for every two damage they take, you take one of the same type anywhere; "
        "their Final Death kills you within minutes."
    ),
    # Connection flaws
    "enemy": (
        "Someone in a Sphere of Influence actively works against you (harassment to murder by dot level). "
        "May be taken multiple times for different enemies."
    ),
    "infamy": (
        "Famous for something horrible in a chosen Sphere; cumulative -2 to mundane non-Intimidation social "
        "interactions with those who recognize you per dot."
    ),
    "poor": (
        "Worse off than lower-middle class; cannot buy Resources. Limits Haven dots/advantages by level; "
        "at three dots you may not buy Haven (but can use others' Havens without advantages)."
    ),
    "no_haven": (
        "No consistent daytime rest; must find shelter each dawn, one fewer downtime action, "
        "cannot buy or benefit from Haven."
    ),
    "obvious_predator": (
        "Look frighteningly predatory; cannot buy Herd and take -1 to non-violent feeding challenges."
    ),
    "illiterate": (
        "Cannot read or write; can match familiar sign letters but not compose text."
    ),
    "known_corpse": (
        "Mortals know you died; friends and family react with horror. Prerequisite: no Mask dots."
    ),
    "known_blankbody": (
        "Flagged in government databases; monthly downtime to cover tracks or face Hunters. "
        "Failed hunts draw Hunter attention. Cannot take Zeroed. Prerequisite: no Mask dots."
    ),
    # Feeding flaws
    "farmer": (
        "Feed exclusively from animals; must spend two Willpower to feed from any other source. "
        "Blood Potency 3+ may not take."
    ),
    "methuselah_s_thirst": (
        "Hunger only fully Slaked by draining a supernatural creature dry (killing it unless it can survive)."
    ),
    "organovore": (
        "Slake Hunger only from live human flesh/organs (major organs, ≤30 minutes dead); "
        "must kill and consume most organs/flesh to drop Hunger below 1."
    ),
    "prey_exclusion": (
        "Refuse to feed from a chosen class of mortals; doing so gains Stains as a Tenet violation. "
        "Ventrue gain an extra vessel restriction."
    ),
    "weak_stomach": (
        "Squeamish around blood; Weakened for one hour after feeding and start each session Weakened. "
        "Ghouls may purchase."
    ),
    # Ghoul flaws
    "baneful_blood": (
        "Your regnant's clan Bane transferred to you at Bane Severity equal to this Flaw's dots; "
        "persists even if regnant changes."
    ),
    "crone_s_curse": (
        "Ghouling aged you unnaturally: appear ten years older and have one fewer health box."
    ),
    "distressing_fangs": (
        "Teeth mystically sharpen overnight; off-putting to humans and probable cause for Inquisition stops."
    ),
    # Mythical flaws
    "bound_to_the_earth": (
        "Must rest near natural soil or do not regain Willpower upon Awakening."
    ),
    "eerie_presence": (
        "Radiate unsettling otherworldliness (visual, scent, or tactile); always disconcerting, "
        "may breach Masquerade."
    ),
    "folkloric_bane": (
        "Besides sun and fire, a common substance (e.g. silver, cold iron, holy water) deals Aggravated Damage; "
        "touching it causes one aggravated."
    ),
    "folkloric_block": (
        "Cannot willingly come within five steps of a chosen folkloric object/place (holy symbols, running water, "
        "invitation-only entries, etc.) or gain Frightened until you leave."
    ),
    "haunted": (
        "A ghostly enemy harasses you like the Enemy Background, built by the Storyteller."
    ),
    "stake_bait": (
        "Heart remains mortal; successful staking causes Final Death."
    ),
    "stigmata": (
        "At Hunger 4+, bleed from hands, feet, and forehead (attracts attention, no extra Hunger)."
    ),
    "trouble_magnet": (
        "Storyteller random bad luck always targets you when multiple outcomes are possible."
    ),
    # Physical flaws
    "awkward_mobility": (
        "Move slowly; two steps per movement action instead of three."
    ),
    "deep_sleeper": (
        "Cannot spend Willpower to stay awake at sunrise unless danger; Awakening costs an extra Willpower."
    ),
    "low_pain_threshold": (
        "Wound penalties start one box earlier per dot (max dots = total health boxes − 3)."
    ),
    "slow_healing": (
        "Combat Rouse-to-mend resolves at end of round after the mass Rouse challenge."
    ),
    # Psychological flaws
    "archaic": (
        "Modern technology enrages you; cannot buy Driving, modern Science, or Technology and "
        "cannot use machinery from the last 100 years. 9th Gen+, 100+ years Embraced only."
    ),
    "dark_secret": (
        "A secret that would cause great embarrassment if revealed; must buy off if public. "
        "Only one Dark Secret."
    ),
    "death_sight": (
        "World appears decaying and dead; cannot determine creature type or mood even with powers like Scry the Soul."
    ),
    "living_on_the_edge": (
        "Curiosity overrides caution; lose Willpower when you pass up new experiences, "
        "Impaired if you run out."
    ),
    "impatient": (
        "Must spend Willpower to wait five minutes when forced to be patient; otherwise lash out in anger."
    ),
    "weak_willed": (
        "Cannot resolve Distracted, Disoriented, Staggered, or Prone without another character's help; "
        "immune to powers that alter those Conditions."
    ),
    # Thin-blood flaws (no dot cost)
    "baby_teeth": (
        "Never developed fangs; must cut victims or use a syringe—no Sip unless target is unconscious."
    ),
    "bestial_temper": (
        "Beast as strong as a full vampire; test for Terror and Rage Frenzy like a full-blood."
    ),
    "branded_by_the_camarilla": (
        "Pay trivial boons to be tolerated on Camarilla turf; name known as branded and extortion-prone."
    ),
    "clan_curse": (
        "Suffer your sire's clan Bane at Severity 1 (Brujah/Gangrel if Bestial Temper; Tremere if Catenating Blood)."
    ),
    "dead_flesh": (
        "Rotting, green-tinted flesh and stench; Masquerade breach without Obfuscate. Cannot take Lifelike."
    ),
    "mortal_frailty": (
        "Heal as a mortal; cannot Rouse the Blood to mend. Cannot take Vampiric Resilience."
    ),
    "shunned_by_the_anarchs": (
        "Anarchs refuse all boons with you and may send Enforcers; cannot take Anarch Comrades."
    ),
    "vitae_dependency": (
        "Must Slake at least one Hunger from vampire blood weekly or lose Disciplines and Thin-Blood Alchemy."
    ),
}
