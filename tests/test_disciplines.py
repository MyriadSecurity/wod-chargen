"""Discipline power selection tests."""

from wod_chargen.core.data_loader import load_json_cached
from wod_chargen.core.rng import SeededRng
from wod_chargen.games.lotn_v5.disciplines import (
    assign_powers_for_discipline,
    enumerate_eligible_powers,
    load_power_catalog,
    owned_power_ids,
    pick_power,
    power_by_id,
    power_eligible,
    record_formula_selection,
    record_ritual,
    validate_discipline_selections,
)
from wod_chargen.games.lotn_v5.generator import generate_character


def _venue():
    return load_json_cached("wod_chargen.venues", "mes_end_to_dawn.json")


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


def test_creation_assigns_power_per_discipline_level():
    result = generate_character(100, _opts(), _venue())
    char = result.character
    for disc_id, rating in char["disciplines"].items():
        picks = char["discipline_powers"].get(disc_id, {})
        for level in range(1, int(rating) + 1):
            assert str(level) in picks, f"{disc_id} missing level {level}"
    assert not validate_discipline_selections(char)


def test_reproducibility_includes_powers():
    a = generate_character(999, _opts(clan="brujah", arch="duelist", sub="fencer"), _venue())
    b = generate_character(999, _opts(clan="brujah", arch="duelist", sub="fencer"), _venue())
    assert a.character.get("discipline_powers") == b.character.get("discipline_powers")


def test_thin_blood_discipline_and_formulas():
    result = generate_character(
        77,
        _opts(type="thin_blood", arch="alchemist", sub="distiller"),
        _venue(),
    )
    char = result.character
    assert char["disciplines"].get("thin_blood_alchemy", 0) >= 1
    tba_picks = char.get("discipline_powers", {}).get("thin_blood_alchemy", {})
    assert tba_picks
    owned = owned_power_ids(char)
    for fid in char.get("thin_blood_formulas", {}):
        assert fid in owned


def test_xp_discipline_buy_adds_power():
    result = generate_character(1, _opts(clan="brujah"), _venue())
    disc_xp = [e for e in result.xp_log if e.category == "discipline"]
    if disc_xp:
        assert result.character["discipline_powers"]


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
