"""Unit tests for trait bias resolution."""

from __future__ import annotations

from dataclasses import dataclass, field

from wod_chargen.games.lotn_v5.archetypes import effective_profile, get_archetype
from wod_chargen.games.lotn_v5.trait_biases import (
    BIAS_MAX,
    BIAS_MIN,
    build_power_biases,
    power_utility_bias,
    resolve_trait_bias,
)


@dataclass
class _StubProfile:
    attribute_biases: dict[str, float] = field(default_factory=dict)
    skill_biases: dict[str, float] = field(default_factory=dict)
    discipline_biases: dict[str, float] = field(default_factory=dict)
    merit_biases: dict[str, float] = field(default_factory=dict)
    flaw_biases: dict[str, float] = field(default_factory=dict)
    background_biases: dict[str, float] = field(default_factory=dict)
    sphere_biases: dict[str, float] = field(default_factory=dict)
    modifier_biases: dict[str, float] = field(default_factory=dict)
    discipline_power_biases: dict[str, float] = field(default_factory=dict)
    tag_affinities: dict[str, float] = field(default_factory=dict)


def test_explicit_bias_overrides_tags():
    profile = _StubProfile(
        skill_biases={"persuasion": 2.0},
        tag_affinities={"social": 1.5},
    )
    assert resolve_trait_bias(profile, "persuasion", "skills") == 2.0


def test_tag_product_for_untagged_explicit():
    profile = _StubProfile(tag_affinities={"social": 1.6, "influence": 1.4})
    bias = resolve_trait_bias(profile, "persuasion", "skills")
    assert bias > 1.0
    assert BIAS_MIN <= bias <= BIAS_MAX


def test_clamp_extreme_values():
    profile = _StubProfile(merit_biases={"iron_gullet": 99.0})
    assert resolve_trait_bias(profile, "iron_gullet", "merits") == BIAS_MAX


def test_unknown_trait_returns_one():
    profile = _StubProfile(tag_affinities={"social": 2.0})
    assert resolve_trait_bias(profile, "nonexistent_skill", "skills") == 1.0


def test_effective_profile_merges_sub_deltas():
    base = get_archetype("diplomat")
    sub = base.sub_archetypes[0]
    merged = effective_profile("diplomat", sub.id, "vampire")
    assert merged.skill_biases.get("persuasion", 0) >= base.skill_biases.get("persuasion", 1.0)


def test_sub_power_bias_deltas_not_targets():
    """Sub discipline_power_biases add to primary; merged values stay in sane range."""
    merged = effective_profile("diplomat", "silver_tongue", "vampire")
    assert merged.discipline_power_biases["mesmerize"] <= 2.5


def test_power_utility_bias_staples():
    assert power_utility_bias("fleetness") > power_utility_bias("nonexistent_power_xyz")


def test_build_power_biases_includes_utility():
    profile = _StubProfile(discipline_power_biases={"fleetness": 1.0})
    biases = build_power_biases(profile, ["fleetness", "rapier"])
    assert biases["fleetness"] > biases.get("rapier", 1.0)
