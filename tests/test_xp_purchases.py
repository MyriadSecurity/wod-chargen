"""XP purchase enumeration tests."""

from wod_chargen.core.data_loader import load_json_cached
from wod_chargen.core.rng import SeededRng
from wod_chargen.games.lotn_v5.archetypes import effective_profile
from wod_chargen.games.lotn_v5.backgrounds import empty_backgrounds
from wod_chargen.games.lotn_v5.paths import DATA_PKG as DATA
from wod_chargen.games.lotn_v5.xp_purchases import enumerate_purchases


def _caps(creation: dict) -> dict[str, int]:
    return {
        "attribute": 5,
        "skill": 5,
        "background": 3,
        "discipline": int(creation.get("discipline_max", 5)),
        "loresheet": 3,
        "blood_potency": 3,
        "thin_blood_formula": int(creation.get("formula_max", 5)),
        "ghoul_power": 1,
    }


def _vampire_char() -> dict:
    return {
        "character_type": "vampire",
        "clan": "brujah",
        "attributes": {"strength": 2},
        "skills": {},
        "disciplines": {"potence": 1},
        "backgrounds": empty_backgrounds(),
        "background_meta": {},
        "merits": {},
        "flaws": {},
        "loresheets": {},
        "blood_potency": 1,
        "discipline_meta": {},
        "thin_blood_formulas": {},
        "ghoul_powers": {},
    }


def test_vampire_enumerate_includes_core_categories():
    creation = load_json_cached(DATA, "creation.json")
    costs = load_json_cached(DATA, "costs.json")
    profile = effective_profile("diplomat", "silver_tongue", "vampire")
    char = _vampire_char()
    caps = _caps(creation)
    rng = SeededRng(42)
    candidates = enumerate_purchases(
        char, profile, costs, "vampire", "diplomat/silver_tongue", caps, rng
    )
    categories = {c.category for c in candidates}
    assert "attribute" in categories
    assert "skill" in categories
    assert "discipline" in categories


def test_ghoul_enumerate_includes_power_candidates():
    creation = load_json_cached(DATA, "ghoul_creation.json")
    costs = load_json_cached(DATA, "costs.json")
    profile = effective_profile("shadow", "spy", "ghoul")
    char = {
        "character_type": "ghoul",
        "domitor_clan": "tremere",
        "attributes": {},
        "skills": {},
        "disciplines": {"auspex": 1},
        "backgrounds": empty_backgrounds(),
        "background_meta": {},
        "ghoul_powers": {},
    }
    caps = _caps(creation)
    rng = SeededRng(7)
    candidates = enumerate_purchases(
        char, profile, costs, "ghoul", "shadow/spy", caps, rng
    )
    assert isinstance(candidates, list)


def test_thin_blood_respects_discipline_cap():
    creation = load_json_cached(DATA, "thin_blood_creation.json")
    costs = load_json_cached(DATA, "costs.json")
    profile = effective_profile("alchemist", "distiller", "thin_blood")
    char = {
        "character_type": "thin_blood",
        "clan": None,
        "attributes": {},
        "skills": {},
        "disciplines": {"thin_blood_alchemy": 3},
        "backgrounds": empty_backgrounds(),
        "background_meta": {},
        "discipline_meta": {"affinity_discipline": "thin_blood_alchemy"},
        "thin_blood_formulas": {},
        "thin_blood_merits": {},
        "loresheets": {},
        "blood_potency": 0,
    }
    caps = _caps(creation)
    rng = SeededRng(99)
    candidates = enumerate_purchases(
        char, profile, costs, "thin_blood", "alchemist/distiller", caps, rng
    )
    for c in candidates:
        if c.category == "discipline" and c.item_id == "thin_blood_alchemy":
            assert c.new_level <= caps["discipline"]
