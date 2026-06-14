"""Predator type package, weight, and bias validation."""

from __future__ import annotations

import pytest

from wod_chargen.games.lotn_v5.archetypes import effective_profile
from wod_chargen.games.lotn_v5.generator import generate_character
from wod_chargen.games.lotn_v5.predators import (
    apply_predator_biases,
    load_predator_types,
    predator_by_id,
    validate_predator_catalog,
)
from tests.support.fixtures import load_venue, opts as _opts

EXPECTED = {
    "alleycat": {
        "pool": ("wits", "streetwise"),
        "humanity": -1,
        "backgrounds": [("contacts", 2)],
        "background_grants": [("resources", 1)],
    },
    "bagger": {
        "pool": ("intelligence", "larceny"),
        "merits": [("iron_gullet", 3)],
        "backgrounds": [("contacts", 2)],
        "flaws": [("enemy", 2)],
        "requires_max_blood_potency": 2,
    },
    "cleaver": {
        "pool": ("manipulation", "subterfuge"),
        "backgrounds": [("herd", 2), ("mask", 2)],
        "flaws": [("cleaver", 1)],
    },
    "consentualist": {
        "pool": ("manipulation", "persuasion"),
        "humanity": 1,
        "backgrounds": [("herd", 3)],
        "flaws": [("masquerade_breacher", 1), ("prey_exclusion_non_consenting", 1)],
    },
    "extortionist": {
        "pool": ("manipulation", "intimidation"),
        "background_grants": [("resources", 1)],
        "background_spend": ("contacts", "allies", 3),
        "flaws": [("enemy", 2)],
    },
    "farmer": {
        "pool": ("composure", "animal_ken"),
        "humanity": 1,
        "background_grants": [("haven", 2)],
        "flaws": [("farmer", 2)],
        "requires_max_blood_potency": 2,
    },
    "ferryman": {
        "pool": None,
        "background_grants": [("allies", 2), ("haven", 2)],
        "flaw_spend_dots": 3,
    },
    "graverobber": {
        "pool": ("wits", "medicine"),
        "merits": [("iron_gullet", 3)],
        "background_grants": [("haven", 1)],
        "flaws": [("obvious_predator", 2)],
    },
    "hitcher": {
        "pool": ("wits", "etiquette"),
        "background_grants": [("haven", 1), ("resources", 1)],
    },
    "osiris": {
        "pool": ("manipulation", "subterfuge"),
        "backgrounds": [("mask", 2)],
        "background_spend": ("herd", "fame", 3),
        "flaws": [("enemy", 2)],
    },
    "sandman": {
        "pool": ("dexterity", "stealth"),
        "backgrounds": [("mask", 4)],
        "flaws": [("prey_exclusion_conscious", 1)],
    },
    "scene_queen": {
        "pool": ("charisma", "etiquette"),
        "backgrounds": [("mask", 2), ("fame", 1), ("herd", 2)],
        "flaw_choice": True,
    },
    "siren": {
        "pool": ("charisma", "subterfuge"),
        "background_spend": ("herd", "fame", 5),
        "flaws": [("enemy", 2)],
    },
}


def _pkg(entry: dict) -> dict:
    return entry["package"]


def _bg_grants(pkg: dict) -> list[tuple[str, int]]:
    return [(b["type"], b["dots"]) for b in pkg.get("backgrounds", [])]


def _bg_grant_specs(pkg: dict) -> list[tuple[str, int]]:
    return [(b["type"], b["dots"]) for b in pkg.get("background_grants", [])]


def _merit_grants(pkg: dict) -> list[tuple[str, int]]:
    return [(m["id"], m["dots"]) for m in pkg.get("merits", [])]


def _flat_flaws(pkg: dict) -> list[tuple[str, int]]:
    out: list[tuple[str, int]] = []
    for flaw in pkg.get("flaws", []):
        out.append((flaw["id"], flaw["dots"]))
    return out


@pytest.mark.parametrize("predator_id", sorted(EXPECTED))
def test_predator_package_matches_rules(predator_id: str):
    entry = predator_by_id(predator_id)
    pkg = _pkg(entry)
    rules = EXPECTED[predator_id]

    if rules["pool"] is None:
        assert entry.get("pool") is None
    else:
        attr, skill = rules["pool"]
        assert entry["pool"] == {"attribute": attr, "skill": skill}
        assert entry["feeding_pool"]

    if "humanity" in rules:
        assert pkg.get("humanity") == rules["humanity"]
    if "requires_max_blood_potency" in rules:
        assert entry.get("requires_max_blood_potency") == rules["requires_max_blood_potency"]
    if "backgrounds" in rules:
        assert _bg_grants(pkg) == rules["backgrounds"]
    if "background_grants" in rules:
        assert _bg_grant_specs(pkg) == rules["background_grants"]
    if "merits" in rules:
        assert _merit_grants(pkg) == rules["merits"]
    if "flaws" in rules:
        assert _flat_flaws(pkg) == rules["flaws"]

    if "background_spend" in rules:
        spec = rules["background_spend"]
        spend = pkg["background_spend"]
        assert spend["dots"] == spec[-1]
        assert set(spend["options"]) == set(spec[:-1])

    if rules.get("flaw_spend_dots"):
        assert pkg["flaw_spend"]["dots"] == rules["flaw_spend_dots"]

    if rules.get("flaw_choice"):
        assert pkg.get("flaw_choice")

    assert "disciplines" not in pkg
    assert "specialties" not in pkg


def test_no_tabletop_only_predator_types():
    ids = {t["id"] for t in load_predator_types()}
    removed = {"blood_leech", "grim_reaper", "montero", "pursuer", "trapdoor", "consensualist"}
    assert ids.isdisjoint(removed)


def test_predator_catalog_validates():
    validate_predator_catalog()


def test_apply_predator_biases_boosts_feeding_pool():
    profile = effective_profile("enforcer", "brawler", "vampire")
    alleycat = predator_by_id("alleycat")
    merged = apply_predator_biases(profile, alleycat)

    assert merged.skill_biases["streetwise"] > profile.skill_biases.get("streetwise", 1.0)
    assert merged.attribute_biases["wits"] > profile.attribute_biases.get("wits", 1.0)


@pytest.mark.parametrize(
    "seed,predator_id",
    [(42, "alleycat"), (7, "bagger"), (99, "farmer")],
)
def test_predator_package_applied_in_generation(seed: int, predator_id: str):
    result = generate_character(seed, _opts(predator=predator_id), load_venue())
    char = result.character
    predator_logs = [e for e in result.creation_log if e.phase == "predator"]
    log_messages = [e.message for e in predator_logs]

    assert char["predator"] == predator_id
    assert predator_logs
    assert not any("Discipline" in e.message for e in predator_logs)

    if predator_id == "alleycat":
        assert char["humanity"] == 6
        assert not char.get("specialties")
        assert sum(d["dots"] for d in char["backgrounds"] if d["type"] == "contacts") >= 2
        assert any(d["type"] == "resources" for d in char["backgrounds"])
        assert any("Humanity" in e.message for e in predator_logs)
        assert char["predator_meta"].get("package_applied")
    elif predator_id == "bagger":
        assert char["merits"].get("iron_gullet") == 3
        enemy_dots = sum(v for k, v in char["flaws"].items() if k == "enemy" or k.startswith("enemy:"))
        assert enemy_dots >= 2
        contacts = [d for d in char["backgrounds"] if d["type"] == "contacts"]
        assert contacts and sum(c["dots"] for c in contacts) >= 2
        assert predator_by_id("bagger")["pool"]["skill"] == "larceny"
    elif predator_id == "farmer":
        assert char["humanity"] == 8
        assert char["flaws"].get("farmer") == 2
        assert any("Humanity" in line for line in log_messages)
        assert any("Flaw Farmer" in line for line in log_messages)
