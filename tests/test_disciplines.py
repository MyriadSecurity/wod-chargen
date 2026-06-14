"""Discipline power selection tests."""

import pytest

from wod_chargen.core.rng import SeededRng
from wod_chargen.games.lotn_v5.disciplines import (
    assign_power_at_level,
    assign_powers_for_discipline,
    enumerate_eligible_powers,
    load_power_catalog,
    pick_power,
    power_by_id,
    power_eligible,
    record_formula_selection,
    record_ritual,
)
from wod_chargen.games.lotn_v5.generator import generate_character
from tests.support.fixtures import load_venue, opts


def _venue():
    return load_venue()


def _opts(**kwargs):
    base = {
        "type": "vampire",
        "clan": "tremere",
        "arch": "occultist",
        "sub": "thaumaturge",
        "approval": "2026-06",
    }
    base.update(kwargs)
    return base


class _Profile:
    discipline_biases: dict[str, float] = {}
    discipline_power_biases: dict[str, float] = {}


def test_catalog_rules_resolve():
    for disc in load_power_catalog()["disciplines"]:
        for power in disc["powers"]:
            assert "rules" in power, power["id"]
            assert power_by_id(power["id"]) is not None


def test_amalgam_blocks_unliving_hive_without_obfuscate():
    power = power_by_id("unliving_hive")
    char = {
        "disciplines": {"animalism": 3, "obfuscate": 1},
        "discipline_powers": {},
        "rituals": [],
        "ceremonies": [],
        "formula_powers": {},
    }
    assert not power_eligible(power, char, track_id="animalism", buying_level=3)
    char["disciplines"]["obfuscate"] = 2
    assert power_eligible(power, char, track_id="animalism", buying_level=3)


def test_blood_walk_requires_a_taste_for_blood():
    ritual = power_by_id("blood_walk")
    char = {
        "disciplines": {"blood_sorcery": 2},
        "discipline_powers": {"blood_sorcery": {"1": "corrosive_vitae", "2": "extinguish_vitae"}},
        "rituals": [],
        "ceremonies": [],
        "formula_powers": {},
    }
    assert not power_eligible(ritual, char, track_id="blood_sorcery_rituals", buying_level=1)
    char["discipline_powers"]["blood_sorcery"]["1"] = "a_taste_for_blood"
    assert power_eligible(ritual, char, track_id="blood_sorcery_rituals", buying_level=1)


def test_or_prerequisite_conceal_or_unseen_passage():
    power = power_by_id("vanish_from_the_mind_s_eye")
    base = {
        "disciplines": {"obfuscate": 4},
        "discipline_powers": {
            "obfuscate": {
                "1": "cloud_memory",
                "2": "silence_of_death",
                "3": "ghost_in_the_machine",
            }
        },
        "rituals": [],
        "ceremonies": [],
        "formula_powers": {},
    }
    assert not power_eligible(power, base, track_id="obfuscate", buying_level=4)
    base["discipline_powers"]["obfuscate"]["3"] = "unseen_passage"
    assert power_eligible(power, base, track_id="obfuscate", buying_level=4)


def test_xp_discipline_buy_adds_power():
    result = generate_character(1, _opts(clan="brujah"), _venue())
    disc_xp = [e for e in result.xp_log if e.category == "discipline"]
    if disc_xp:
        assert result.character["discipline_powers"]
    for buy in disc_xp:
        disc = buy.item
        level = buy.new_level
        pid = result.character["discipline_powers"][disc][str(level)]
        assert int(power_by_id(pid)["level"]) == level


def test_pick_power_respects_bias():
    rng = SeededRng(1)
    candidates = [{"id": "a"}, {"id": "b"}]
    picks = [pick_power(rng, candidates, {"a": 100.0, "b": 0.01})["id"] for _ in range(20)]
    assert picks.count("a") > picks.count("b")


def test_record_formula_skips_duplicate():
    char = {
        "disciplines": {"thin_blood_alchemy": 1},
        "discipline_powers": {"thin_blood_alchemy": {"1": "haze"}},
        "thin_blood_formulas": {},
        "formula_powers": {},
        "rituals": [],
        "ceremonies": [],
    }
    record_formula_selection(char, "haze")
    assert "haze" not in char["thin_blood_formulas"]


def test_record_ritual():
    char = {"disciplines": {"blood_sorcery": 2}, "discipline_powers": {}, "rituals": [], "ceremonies": [], "formula_powers": {}}
    log = []
    record_ritual(char, "cling_of_the_arachnid", log)
    assert "cling_of_the_arachnid" in char["rituals"]


def test_enumerate_eligible_at_level():
    char = {
        "disciplines": {"celerity": 0},
        "discipline_powers": {},
        "rituals": [],
        "ceremonies": [],
        "formula_powers": {},
    }
    eligible = enumerate_eligible_powers("celerity", 1, char)
    assert eligible
    assert all(int(p["level"]) == 1 for p in eligible)


def test_assign_powers_for_discipline():
    rng = SeededRng(5)
    char = {
        "disciplines": {"potence": 2},
        "discipline_powers": {},
        "rituals": [],
        "ceremonies": [],
        "formula_powers": {},
    }
    log = []
    assign_powers_for_discipline(rng, char, "potence", 2, _Profile(), log)
    assert char["discipline_powers"]["potence"]["1"]
    assert char["discipline_powers"]["potence"]["2"]
    for level_str, pid in char["discipline_powers"]["potence"].items():
        assert int(power_by_id(pid)["level"]) == int(level_str)


@pytest.mark.parametrize("seed", range(12))
def test_xp_discipline_advancement_picks_matching_level_power(seed: int):
    """Each +1 discipline dot during XP must fill the slot at the new dot level."""
    result = generate_character(seed, _opts(clan="tremere", arch="occultist", sub="thaumaturge"), _venue())
    for buy in [e for e in result.xp_log if e.category == "discipline"]:
        pid = result.character["discipline_powers"][buy.item][str(buy.new_level)]
        assert int(power_by_id(pid)["level"]) == buy.new_level


def test_assign_power_at_level_rejects_wrong_catalog_level():
    rng = SeededRng(1)
    char = {
        "disciplines": {"celerity": 2},
        "discipline_powers": {"celerity": {"1": "fleetness"}},
        "rituals": [],
        "ceremonies": [],
        "formula_powers": {},
    }
    log = []
    assign_power_at_level(rng, char, "celerity", 2, _Profile(), log)
    pid = char["discipline_powers"]["celerity"]["2"]
    assert int(power_by_id(pid)["level"]) == 2
