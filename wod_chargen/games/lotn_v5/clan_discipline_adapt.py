"""Clan-aware discipline bias adaptation for unconventional archetype+clan combos."""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from wod_chargen.core.data_loader import load_json_cached
from wod_chargen.games.lotn_v5.archetypes import ArchetypeProfile

DATA = "wod_chargen.games.lotn_v5.data"

IN_CLAN_DISCIPLINE_FLOOR = 0.85
IN_CLAN_POWER_FLOOR = 0.75
OFF_CLAN_SIGNATURE_FACTOR = 0.6
OFF_CLAN_DEFAULT_FACTOR = 0.3
SIGNATURE_DISCIPLINE_MIN_BIAS = 1.05


def clan_discipline_pool(clan_id: str | None) -> frozenset[str]:
    if not clan_id:
        return frozenset()
    clans = load_json_cached(DATA, "clans.json")
    return frozenset(clans.get(clan_id, {}).get("disciplines", []))


def signature_disciplines(profile: ArchetypeProfile) -> list[str]:
    """Archetype signature disciplines (explicit list or high discipline_biases)."""
    expr = profile.discipline_expressions
    if expr and expr.get("signature"):
        return list(expr["signature"])
    return [
        disc_id
        for disc_id, bias in profile.discipline_biases.items()
        if float(bias) >= SIGNATURE_DISCIPLINE_MIN_BIAS
    ]


def _missing_signatures(profile: ArchetypeProfile, clan_pool: frozenset[str]) -> list[str]:
    return [d for d in signature_disciplines(profile) if d not in clan_pool]


def _apply_expression_alternates(
    profile: ArchetypeProfile,
    clan_pool: frozenset[str],
) -> tuple[dict[str, float], dict[str, float]]:
    """Merge alternate discipline/power biases when signature discs are off-clan."""
    disc_biases = dict(profile.discipline_biases)
    power_biases = dict(profile.discipline_power_biases)
    expr = profile.discipline_expressions
    if not expr or not _missing_signatures(profile, clan_pool):
        return disc_biases, power_biases

    alternates = expr.get("alternates") or {}
    for disc_id, spec in alternates.items():
        if disc_id not in clan_pool:
            continue
        target = float(spec.get("discipline_bias", 1.0))
        disc_biases[disc_id] = max(disc_biases.get(disc_id, 1.0), target)
        for pid, bias in (spec.get("power_biases") or {}).items():
            power_biases[pid] = float(bias)
    return disc_biases, power_biases


def adapt_profile_for_clan(profile: ArchetypeProfile, clan_id: str | None) -> ArchetypeProfile:
    """Apply in-clan floors and expression-map alternates for this clan."""
    clan_pool = clan_discipline_pool(clan_id)
    if not clan_pool:
        return profile

    disc_biases, power_biases = _apply_expression_alternates(profile, clan_pool)
    for disc_id in clan_pool:
        disc_biases[disc_id] = max(float(disc_biases.get(disc_id, 1.0)), IN_CLAN_DISCIPLINE_FLOOR)

    return replace(
        profile,
        discipline_biases=disc_biases,
        discipline_power_biases=power_biases,
    )


def resolve_discipline_bias(
    profile: ArchetypeProfile,
    disc_id: str,
    clan_pool: frozenset[str] | set[str],
) -> float:
    """Discipline bias with in-clan soft floor."""
    bias = float(profile.discipline_biases.get(disc_id, 1.0))
    if disc_id in clan_pool:
        return max(bias, IN_CLAN_DISCIPLINE_FLOOR)
    return bias


def off_clan_signature_factor(
    profile: ArchetypeProfile,
    disc_id: str,
    clan_pool: frozenset[str] | set[str],
) -> float:
    """XP clan factor: 0.6 for off-clan signature discs, else 0.3."""
    if disc_id in clan_pool:
        return 1.0
    if disc_id in signature_disciplines(profile):
        return OFF_CLAN_SIGNATURE_FACTOR
    return OFF_CLAN_DEFAULT_FACTOR


def char_clan_pool(char: dict[str, Any]) -> frozenset[str]:
    """In-clan discipline pool for a character sheet dict."""
    ctype = char.get("character_type", "vampire")
    if ctype == "ghoul":
        return clan_discipline_pool(char.get("domitor_clan"))
    if ctype == "thin_blood":
        return frozenset({"thin_blood_alchemy"})
    return clan_discipline_pool(char.get("clan"))
