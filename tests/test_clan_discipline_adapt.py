"""Tests for clan-aware discipline bias adaptation."""

from __future__ import annotations

from dataclasses import replace

import pytest

from wod_chargen.core.data_loader import load_json_cached
from wod_chargen.games.lotn_v5.archetypes import effective_profile, get_archetype
from wod_chargen.games.lotn_v5.clan_discipline_adapt import (
    IN_CLAN_DISCIPLINE_FLOOR,
    IN_CLAN_POWER_FLOOR,
    OFF_CLAN_SIGNATURE_FACTOR,
    adapt_profile_for_clan,
    off_clan_signature_factor,
    resolve_discipline_bias,
)
from wod_chargen.games.lotn_v5.disciplines import load_power_catalog
from wod_chargen.games.lotn_v5.generator import generate_character
from wod_chargen.games.lotn_v5.trait_biases import build_power_biases
from tests.support.fixtures import load_venue, opts


def _venue():
    return load_venue()


def _opts(**kwargs):
    base = {
        "type": "vampire",
        "clan": "toreador",
        "arch": "enforcer",
        "sub": "brawler",
        "approval": "2026-06",
    }
    base.update(kwargs)
    return base


def _toreador_pool() -> frozenset[str]:
    clans = load_json_cached("wod_chargen.games.lotn_v5.data", "clans.json")
    return frozenset(clans["toreador"]["disciplines"])


def test_resolve_discipline_bias_in_clan_floor():
    profile = replace(get_archetype("enforcer"), discipline_biases={"auspex": 0.4})
    pool = _toreador_pool()
    assert resolve_discipline_bias(profile, "auspex", pool) == IN_CLAN_DISCIPLINE_FLOOR


def test_off_clan_signature_factor_occultist_blood_sorcery():
    profile = effective_profile("occultist", "thaumaturge", "vampire")
    pool = _toreador_pool()
    assert off_clan_signature_factor(profile, "blood_sorcery", pool) == OFF_CLAN_SIGNATURE_FACTOR
    assert off_clan_signature_factor(profile, "potence", pool) == 0.3


def test_adapt_profile_raises_in_clan_discipline_floor():
    base = get_archetype("enforcer")
    adapted = adapt_profile_for_clan(base, "toreador")
    for disc in _toreador_pool():
        assert adapted.discipline_biases[disc] >= IN_CLAN_DISCIPLINE_FLOOR


def test_adapt_profile_merges_expression_alternates():
    base = get_archetype("enforcer")
    adapted = adapt_profile_for_clan(base, "toreador")
    assert adapted.discipline_biases["celerity"] >= 1.12
    assert adapted.discipline_power_biases["fleetness"] >= 1.25


def test_build_power_biases_in_clan_floor_occultist_celerity():
    profile = adapt_profile_for_clan(
        effective_profile("occultist", "thaumaturge", "vampire"),
        "toreador",
    )
    char = {
        "character_type": "vampire",
        "clan": "toreador",
        "disciplines": {"celerity": 2},
    }
    celerity_powers = [
        p["id"]
        for disc in load_power_catalog()["disciplines"]
        if disc["id"] == "celerity"
        for p in disc["powers"]
    ]
    biases = build_power_biases(profile, celerity_powers, char=char, track_id="celerity")
    for pid in celerity_powers:
        if pid in (profile.discipline_power_biases or {}):
            continue
        assert biases[pid] >= IN_CLAN_POWER_FLOOR


@pytest.mark.parametrize("seed", range(10))
def test_toreador_occultist_in_clan_power_biases(seed: int):
    result = generate_character(
        seed,
        _opts(clan="toreador", arch="occultist", sub="thaumaturge"),
        _venue(),
    )
    profile = adapt_profile_for_clan(
        effective_profile("occultist", "thaumaturge", "vampire"),
        "toreador",
    )
    pool = _toreador_pool()
    char = result.character
    for disc_id, rating in char.get("disciplines", {}).items():
        if disc_id not in pool or rating < 1:
            continue
        powers = [
            p["id"]
            for disc in load_power_catalog()["disciplines"]
            if disc["id"] == disc_id
            for p in disc["powers"]
        ]
        biases = build_power_biases(profile, powers, char=char, track_id=disc_id)
        for pid, bias in biases.items():
            if pid in profile.discipline_power_biases:
                continue
            assert bias >= IN_CLAN_POWER_FLOOR, f"seed={seed} {disc_id} {pid}={bias}"


@pytest.mark.parametrize("seed", range(8))
def test_toreador_enforcer_generates_in_clan_disciplines(seed: int):
    result = generate_character(
        seed,
        _opts(clan="toreador", arch="enforcer", sub="brawler"),
        _venue(),
    )
    pool = _toreador_pool()
    discs = set(result.character.get("disciplines", {}))
    assert pool <= discs
