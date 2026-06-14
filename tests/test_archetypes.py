"""Archetype JSON loading tests."""

import pytest

from wod_chargen.games.lotn_v5.archetypes import archetypes_for_type, archetype_display_label, get_archetype, load_all_archetypes


def test_all_archetypes_load():
    profiles = load_all_archetypes()
    assert len(profiles) == 12


def test_alchemist_thin_blood_only():
    alc = get_archetype("alchemist")
    assert alc.allowed_types == ("thin_blood",)
    assert "alchemist" not in {p.id for p in archetypes_for_type("vampire")}
    assert "alchemist" in {p.id for p in archetypes_for_type("thin_blood")}
    assert archetype_display_label(alc) == "The Alchemist *** Thin-Blood Only ***"


def test_archetype_type_gate():
    with pytest.raises(ValueError, match="not allowed"):
        from wod_chargen.games.lotn_v5.archetypes import effective_profile

        effective_profile("alchemist", "distiller", "vampire")
