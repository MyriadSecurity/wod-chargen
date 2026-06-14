"""Benefit package application tests."""

from wod_chargen.core.rng import SeededRng
from wod_chargen.games.lotn_v5.archetypes import effective_profile
from wod_chargen.games.lotn_v5.backgrounds import empty_backgrounds
from wod_chargen.games.lotn_v5.benefit_packages import apply_benefit_package
from wod_chargen.games.lotn_v5.predators import load_predator_types


def test_predator_package_grants_background():
    alleycat = next(p for p in load_predator_types() if p["id"] == "alleycat")
    char = {
        "backgrounds": empty_backgrounds(),
        "skills": {},
        "merits": {},
        "flaws": {},
        "humanity": 7,
        "blood_potency": 1,
    }
    profile = effective_profile("diplomat", "silver_tongue", "vampire")
    lines = apply_benefit_package(
        alleycat["package"],
        char,
        SeededRng(42),
        profile,
        caps={"blood_potency": 3},
    )
    assert lines
    assert char["backgrounds"]
