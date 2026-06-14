"""Tests for weight map graph data."""

from app.weight_map_data import (
    LENSES,
    build_tree,
    build_archetype_overview_tree,
    build_archetype_profile_tree,
    build_clan_profile_tree,
    build_predator_profile_tree,
)


def test_all_lenses_overview():
    for lens_id in LENSES:
        tree = build_tree(lens_id, "overview")
        assert tree.get("children") is not None


def test_archetype_overview_has_all_primaries():
    tree = build_archetype_overview_tree()
    assert len(tree["children"]) == 12


def test_archetype_profile_sections():
    tree = build_archetype_profile_tree("shadow", "spy", "vampire")
    assert "Shadow" in tree["name"]
    section_names = {c["name"] for c in tree["children"]}
    assert "Skills" in section_names
    assert "Tag affinities" in section_names


def test_predator_profile_has_pool_and_benefits():
    tree = build_predator_profile_tree("alleycat")
    assert tree["name"] == "Alleycat"
    names = {c["name"] for c in tree["children"]}
    assert "Pool skill weights" in names
    assert "Benefit — backgrounds" in names


def test_clan_profile_in_clan_disciplines():
    tree = build_clan_profile_tree("brujah")
    assert tree["name"] == "Brujah"
    in_clan = next(c for c in tree["children"] if "In-clan" in c["name"])
    ids = {leaf["id"] for leaf in in_clan["children"]}
    assert "celerity" in ids


def test_category_skills_peak_bias():
    tree = build_tree("category", "profile", id="skills")
    traits = tree["children"][0]["children"]
    stealth = next(t for t in traits if t["id"] == "stealth")
    assert stealth["value"] >= 2.0


def test_combo_merges_archetype_predator_and_clan():
    tree = build_tree(
        "combo",
        "profile",
        arch="diplomat",
        sub="courtier",
        predator="alleycat",
        clan="brujah",
        type="vampire",
    )
    assert "Alleycat" in tree["name"]
    assert "Brujah" in tree["name"]
    section_names = {c["name"] for c in tree["children"]}
    assert "Combined skills" in section_names
    assert "Combined disciplines" in section_names
    assert "Combined discipline powers" in section_names
    assert "Tag affinities" in section_names


def test_combo_clan_adapts_off_clan_signatures():
    from app.weight_map_data import generation_profile

    tremere = generation_profile("scholar", "loremaster", "alleycat", "tremere", "vampire")
    brujah = generation_profile("scholar", "loremaster", "alleycat", "brujah", "vampire")
    assert tremere.discipline_biases.get("blood_sorcery", 0) >= 0.85
    assert brujah.discipline_biases.get("celerity", 0) >= 0.85
    assert tremere.discipline_biases != brujah.discipline_biases

