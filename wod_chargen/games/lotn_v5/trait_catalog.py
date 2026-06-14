"""Shared trait catalog ID registries for validation and visualization."""

from __future__ import annotations

from functools import lru_cache

from wod_chargen.core.data_loader import load_json_cached
from wod_chargen.games.lotn_v5.paths import DATA_PKG
from wod_chargen.games.lotn_v5.trait_biases import load_trait_tags


@lru_cache(maxsize=1)
def attribute_ids() -> frozenset[str]:
    return frozenset(load_json_cached(DATA_PKG, "attributes.json")["all"])


@lru_cache(maxsize=1)
def skill_ids() -> frozenset[str]:
    return frozenset(load_json_cached(DATA_PKG, "skills.json")["all"])


@lru_cache(maxsize=1)
def discipline_ids() -> frozenset[str]:
    return frozenset(load_json_cached(DATA_PKG, "disciplines.json")["all"])


@lru_cache(maxsize=1)
def background_ids() -> frozenset[str]:
    bg = load_json_cached(DATA_PKG, "backgrounds.json")
    return frozenset(bg["backgrounds"].keys())


@lru_cache(maxsize=1)
def sphere_ids() -> frozenset[str]:
    bg = load_json_cached(DATA_PKG, "backgrounds.json")
    return frozenset(s["id"] for s in bg["spheres"])


@lru_cache(maxsize=1)
def modifier_ids() -> frozenset[str]:
    bg = load_json_cached(DATA_PKG, "backgrounds.json")
    mods: set[str] = set()
    for spec in bg["backgrounds"].values():
        for mod in spec.get("advantages", []) + spec.get("disadvantages", []):
            mods.add(mod["id"])
    return frozenset(mods)


@lru_cache(maxsize=1)
def merit_ids() -> frozenset[str]:
    mf = load_json_cached(DATA_PKG, "merits_flaws.json")
    return frozenset(m["id"] for m in mf["merits"])


@lru_cache(maxsize=1)
def flaw_ids() -> frozenset[str]:
    mf = load_json_cached(DATA_PKG, "merits_flaws.json")
    return frozenset(f["id"] for f in mf["flaws"])


@lru_cache(maxsize=1)
def power_ids() -> frozenset[str]:
    ids: set[str] = set()
    for disc in load_json_cached(DATA_PKG, "discipline_powers.json")["disciplines"]:
        for p in disc.get("powers", []):
            ids.add(p["id"])
    return frozenset(ids)


@lru_cache(maxsize=1)
def loresheet_ids() -> frozenset[str]:
    data = load_json_cached(DATA_PKG, "loresheets.json")
    return frozenset(ls["id"] for ls in data["loresheets"])


@lru_cache(maxsize=1)
def tag_ids() -> frozenset[str]:
    return frozenset(load_trait_tags().get("tags", {}).keys())


def all_bias_keys() -> dict[str, set[str]]:
    return {
        "attribute_biases": set(attribute_ids()),
        "skill_biases": set(skill_ids()),
        "discipline_biases": set(discipline_ids()),
        "merit_biases": set(merit_ids()),
        "flaw_biases": set(flaw_ids()),
        "background_biases": set(background_ids()),
        "sphere_biases": set(sphere_ids()),
        "modifier_biases": set(modifier_ids()),
        "discipline_power_biases": set(power_ids()),
        "tag_affinities": set(tag_ids()),
        "loresheet_biases": set(loresheet_ids()),
    }


def trait_ids_for_category(category: str) -> list[str]:
    if category == "attributes":
        return list(attribute_ids())
    if category == "skills":
        return list(skill_ids())
    if category == "disciplines":
        return list(discipline_ids())
    if category == "backgrounds":
        return list(background_ids())
    if category == "spheres":
        return list(sphere_ids())
    if category == "modifiers":
        return sorted(modifier_ids())
    if category == "merits":
        return list(merit_ids())
    if category == "flaws":
        return list(flaw_ids())
    if category == "powers":
        return [p for p in power_ids() if not p.startswith("counterfeit")]
    if category == "tags":
        return sorted(tag_ids())
    raise ValueError(f"Unknown category: {category}")
