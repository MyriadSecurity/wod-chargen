"""SPI weight-map tree builders (archetype / division / faction / affinity)."""

from __future__ import annotations

from typing import Any

from wod_chargen.core.data_loader import load_json_cached
from wod_chargen.games.spi.archetypes import get_archetype, list_archetypes
from wod_chargen.games.spi.paths import DATA_PKG

LENSES: dict[str, str] = {
    "archetype": "Archetypes",
    "division": "Divisions",
    "faction": "Factions",
    "affinity": "Affinities",
    "catalog": "Catalog defaults",
    "combo": "Archetype + division + faction",
}

CATEGORY_IDS: dict[str, str] = {
    "attributes": "Attributes",
    "skills": "Skills",
    "affinities": "Affinities",
    "merits": "Merits",
}


def _leaf(name: str, value: float, kind: str, trait_id: str) -> dict[str, Any]:
    return {
        "name": name.replace("_", " ").title() if name == trait_id else name,
        "value": round(float(value), 3),
        "kind": kind,
        "id": trait_id,
    }


def _section(label: str, block: dict[str, float], kind: str) -> dict[str, Any] | None:
    if not block:
        return None
    items = sorted(block.items(), key=lambda kv: (-kv[1], kv[0]))
    return {
        "name": label,
        "kind": "section",
        "children": [_leaf(k, v, kind, k) for k, v in items],
    }


def _profile_children(profile: dict[str, Any]) -> list[dict[str, Any]]:
    children: list[dict[str, Any]] = []
    for label, key, kind in (
        ("Attributes", "attribute_biases", "attribute"),
        ("Skills", "skill_biases", "skill"),
        ("Affinities", "affinity_biases", "affinity"),
        ("Tag affinities", "tag_affinities", "tag"),
        ("Merits", "merit_biases", "merit"),
    ):
        sec = _section(label, profile.get(key) or {}, kind)
        if sec:
            children.append(sec)
    return children


def picker_for_lens(lens: str) -> list[dict[str, str]]:
    if lens == "archetype":
        return [{"id": a["id"], "label": a.get("label", a["id"])} for a in list_archetypes()]
    if lens == "division":
        data = load_json_cached(DATA_PKG, "divisions.json")
        return [{"id": d["id"], "label": d.get("label", d["id"])} for d in data.values()]
    if lens == "faction":
        data = load_json_cached(DATA_PKG, "factions.json")
        return [{"id": f["id"], "label": f.get("label", f["id"])} for f in data.values()]
    if lens == "affinity":
        data = load_json_cached(DATA_PKG, "affinity_types.json")
        return [{"id": a["id"], "label": a.get("label", a["id"])} for a in data.values()]
    return []


def build_tree(lens: str, mode: str, **params: str) -> dict[str, Any]:
    if lens == "archetype":
        if mode == "overview":
            return {
                "name": "SPI Archetypes",
                "kind": "root",
                "children": [
                    {
                        "name": a.get("label", a["id"]),
                        "kind": "archetype",
                        "id": a["id"],
                        "lens": "archetype",
                        "children": _profile_children(a),
                    }
                    for a in list_archetypes()
                ],
            }
        arch = get_archetype(params.get("id") or params.get("arch") or "investigator")
        return {
            "name": arch.get("label", arch["id"]),
            "kind": "archetype",
            "id": arch["id"],
            "children": _profile_children(arch),
        }

    if lens == "division":
        data = load_json_cached(DATA_PKG, "divisions.json")
        if mode == "overview":
            return {
                "name": "Divisions",
                "kind": "root",
                "children": [
                    {
                        "name": d.get("label", d["id"]),
                        "kind": "division",
                        "id": d["id"],
                        "lens": "division",
                        "children": _profile_children(d),
                    }
                    for d in data.values()
                ],
            }
        d = data[params.get("id", "adventure")]
        return {"name": d.get("label", d["id"]), "kind": "division", "children": _profile_children(d)}

    if lens == "faction":
        data = load_json_cached(DATA_PKG, "factions.json")
        if mode == "overview":
            return {
                "name": "Factions",
                "kind": "root",
                "children": [
                    {
                        "name": f.get("label", f["id"]),
                        "kind": "faction",
                        "id": f["id"],
                        "lens": "faction",
                        "children": _profile_children(f),
                    }
                    for f in data.values()
                ],
            }
        f = data[params.get("id", "higher_ground")]
        return {"name": f.get("label", f["id"]), "kind": "faction", "children": _profile_children(f)}

    if lens == "affinity":
        data = load_json_cached(DATA_PKG, "affinity_types.json")
        children = [
            {"name": a.get("label", a["id"]), "kind": "affinity", "id": a["id"], "value": 1.0}
            for a in data.values()
        ]
        return {"name": "Affinity types", "kind": "root", "children": children}

    if lens == "combo":
        arch = get_archetype(params.get("arch", "investigator"))
        divisions = load_json_cached(DATA_PKG, "divisions.json")
        factions = load_json_cached(DATA_PKG, "factions.json")
        div = divisions.get(params.get("division", "adventure"), {})
        fac = factions.get(params.get("faction", "higher_ground"), {})
        merged: dict[str, Any] = {
            "attribute_biases": {},
            "skill_biases": {},
            "affinity_biases": {},
            "tag_affinities": {},
            "merit_biases": {},
        }
        for key in merged:
            for src in (arch, div, fac):
                for trait, val in (src.get(key) or {}).items():
                    merged[key][trait] = merged[key].get(trait, 1.0) * float(val)
        return {
            "name": "Combined biases",
            "kind": "root",
            "children": _profile_children(merged),
        }

    # catalog
    attrs = load_json_cached(DATA_PKG, "attributes.json")["all"]
    skills = load_json_cached(DATA_PKG, "skills.json")["all"]
    return {
        "name": "SPI catalog",
        "kind": "root",
        "children": [
            {
                "name": "Attributes",
                "kind": "section",
                "children": [_leaf(a, 1.0, "attribute", a) for a in attrs],
            },
            {
                "name": "Skills",
                "kind": "section",
                "children": [_leaf(s, 1.0, "skill", s) for s in skills],
            },
        ],
    }
