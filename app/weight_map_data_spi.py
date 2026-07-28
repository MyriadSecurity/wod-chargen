"""SPI weight-map tree builders (archetype / division / faction / affinity)."""

from __future__ import annotations

from typing import Any

from wod_chargen.core.data_loader import load_json_cached
from wod_chargen.games.spi.archetypes import (
    default_sub_id,
    effective_profile,
    list_archetypes,
)
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

_DEFAULT_ARCH = "investigator"
_DEFAULT_DIVISION = "adventure"
_DEFAULT_FACTION = "higher_ground"


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


def _nav_node(
    name: str,
    kind: str,
    node_id: str,
    *,
    lens: str,
    children: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    node: dict[str, Any] = {
        "name": name,
        "kind": kind,
        "id": node_id,
        "lens": lens,
        "nav": True,
    }
    if children:
        node["children"] = children
    return node


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


def _peek_sections(profile: dict[str, Any]) -> list[dict[str, Any]]:
    """Compact overview branches so the radial map stays readable."""
    branches: list[dict[str, Any]] = []
    for label, key, kind, n in (
        ("Tags", "tag_affinities", "tag", 5),
        ("Skills", "skill_biases", "skill", 4),
        ("Affinities", "affinity_biases", "affinity", 3),
    ):
        ranked = sorted((profile.get(key) or {}).items(), key=lambda kv: (-kv[1], kv[0]))[:n]
        sec = _section(label, dict(ranked), kind)
        if sec:
            branches.append(sec)
    return branches


def default_arch_picker_id() -> str:
    return f"{_DEFAULT_ARCH}:{default_sub_id(_DEFAULT_ARCH)}"


def picker_for_lens(lens: str) -> list[dict[str, str]]:
    if lens == "archetype":
        out: list[dict[str, str]] = []
        for a in list_archetypes():
            for s in a.get("sub_archetypes") or []:
                out.append(
                    {
                        "id": f"{a['id']}:{s['id']}",
                        "label": f"{a.get('label', a['id'])} — {s.get('label', s['id'])}",
                    }
                )
        return out
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


def _parse_arch_sub(raw: str) -> tuple[str, str]:
    if ":" in raw:
        arch, sub = raw.split(":", 1)
        return arch, sub
    arch = raw or _DEFAULT_ARCH
    try:
        return arch, default_sub_id(arch)
    except KeyError:
        return _DEFAULT_ARCH, default_sub_id(_DEFAULT_ARCH)


def _lookup(data: dict[str, Any], key: str, fallback: str) -> dict[str, Any]:
    if key in data:
        return data[key]
    if fallback in data:
        return data[fallback]
    return next(iter(data.values()))


def _merge_combo(
    arch: dict[str, Any],
    div: dict[str, Any],
    fac: dict[str, Any],
) -> dict[str, Any]:
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
    return merged


def _affinity_lean_tree(affinity_id: str) -> dict[str, Any]:
    """Rank archetype/subtype packs by bias toward one Affinity type."""
    leans: list[tuple[float, str, str, str, str]] = []
    for a in list_archetypes():
        for s in a.get("sub_archetypes") or []:
            merged = effective_profile(a["id"], s["id"])
            bias = float((merged.get("affinity_biases") or {}).get(affinity_id, 1.0))
            leans.append(
                (
                    bias,
                    a.get("label", a["id"]),
                    s.get("label", s["id"]),
                    a["id"],
                    s["id"],
                )
            )
    leans.sort(key=lambda row: (-row[0], row[1], row[2]))
    children = [
        _nav_node(
            f"{arch_label} — {sub_label}",
            "subtype",
            f"{arch_id}:{sub_id}",
            lens="archetype",
            children=[_leaf(affinity_id, bias, "affinity", affinity_id)],
        )
        for bias, arch_label, sub_label, arch_id, sub_id in leans
    ]
    types = load_json_cached(DATA_PKG, "affinity_types.json")
    label = types.get(affinity_id, {}).get("label", affinity_id)
    return {
        "name": f"{label} Affinity leans",
        "kind": "root",
        "lens": "affinity",
        "id": affinity_id,
        "children": children,
    }


def build_tree(lens: str, mode: str, **params: str) -> dict[str, Any]:
    if lens == "archetype":
        if mode == "overview":
            children = []
            for a in list_archetypes():
                subs = a.get("sub_archetypes") or []
                if not subs:
                    continue
                default = subs[0]
                merged = effective_profile(a["id"], default["id"])
                sub_nav = [
                    _nav_node(
                        s.get("label", s["id"]),
                        "subtype",
                        f"{a['id']}:{s['id']}",
                        lens="archetype",
                    )
                    for s in subs
                ]
                children.append(
                    _nav_node(
                        a.get("label", a["id"]),
                        "archetype",
                        f"{a['id']}:{default['id']}",
                        lens="archetype",
                        children=_peek_sections(merged) + sub_nav,
                    )
                )
            return {
                "name": "SPI Archetypes",
                "kind": "root",
                "lens": "archetype",
                "children": children,
            }

        raw = params.get("id") or params.get("arch") or default_arch_picker_id()
        arch_id, sub_id = _parse_arch_sub(raw)
        if params.get("sub"):
            sub_id = params["sub"]
        try:
            merged = effective_profile(arch_id, sub_id)
        except KeyError:
            arch_id, sub_id = _parse_arch_sub(default_arch_picker_id())
            merged = effective_profile(arch_id, sub_id)
        return {
            "name": f"{merged.get('label', arch_id)} · {merged.get('sub_label', sub_id)}",
            "kind": "root",
            "lens": "archetype",
            "id": f"{arch_id}:{sub_id}",
            "children": _profile_children(merged),
        }

    if lens == "division":
        data = load_json_cached(DATA_PKG, "divisions.json")
        if mode == "overview":
            return {
                "name": "Divisions",
                "kind": "root",
                "lens": "division",
                "children": [
                    _nav_node(
                        d.get("label", d["id"]),
                        "division",
                        d["id"],
                        lens="division",
                        children=_peek_sections(d),
                    )
                    for d in data.values()
                ],
            }
        d = _lookup(data, params.get("id", _DEFAULT_DIVISION), _DEFAULT_DIVISION)
        return {
            "name": d.get("label", d["id"]),
            "kind": "root",
            "lens": "division",
            "id": d["id"],
            "children": _profile_children(d),
        }

    if lens == "faction":
        data = load_json_cached(DATA_PKG, "factions.json")
        if mode == "overview":
            return {
                "name": "Factions",
                "kind": "root",
                "lens": "faction",
                "children": [
                    _nav_node(
                        f.get("label", f["id"]),
                        "faction",
                        f["id"],
                        lens="faction",
                        children=_peek_sections(f),
                    )
                    for f in data.values()
                ],
            }
        f = _lookup(data, params.get("id", _DEFAULT_FACTION), _DEFAULT_FACTION)
        return {
            "name": f.get("label", f["id"]),
            "kind": "root",
            "lens": "faction",
            "id": f["id"],
            "children": _profile_children(f),
        }

    if lens == "affinity":
        data = load_json_cached(DATA_PKG, "affinity_types.json")
        if mode == "overview":
            return {
                "name": "Affinity types",
                "kind": "root",
                "lens": "affinity",
                "children": [
                    _nav_node(a.get("label", a["id"]), "affinity", a["id"], lens="affinity")
                    for a in data.values()
                ],
            }
        aff_id = params.get("id", "ghost")
        if aff_id not in data:
            aff_id = next(iter(data))
        return _affinity_lean_tree(aff_id)

    if lens == "combo":
        if mode == "overview":
            return {
                "name": "Archetype + Division + Faction",
                "kind": "root",
                "lens": "combo",
                "children": [
                    {
                        "name": "How to use",
                        "kind": "section",
                        "children": [
                            _leaf(
                                "Single profile: pick archetype, Division, and Faction "
                                "to see multiplied generation weights",
                                1.0,
                                "weight",
                                "hint",
                            )
                        ],
                    }
                ],
            }
        arch_raw = params.get("arch") or params.get("id") or default_arch_picker_id()
        arch_id, sub_id = _parse_arch_sub(arch_raw)
        if params.get("sub"):
            sub_id = params["sub"]
        try:
            arch = effective_profile(arch_id, sub_id)
        except KeyError:
            arch_id, sub_id = _parse_arch_sub(default_arch_picker_id())
            arch = effective_profile(arch_id, sub_id)
        divisions = load_json_cached(DATA_PKG, "divisions.json")
        factions = load_json_cached(DATA_PKG, "factions.json")
        div = _lookup(divisions, params.get("division", _DEFAULT_DIVISION), _DEFAULT_DIVISION)
        fac = _lookup(factions, params.get("faction", _DEFAULT_FACTION), _DEFAULT_FACTION)
        merged = _merge_combo(arch, div, fac)
        return {
            "name": (
                f"{arch.get('label', arch_id)} · {arch.get('sub_label', sub_id)} · "
                f"{div.get('label', div['id'])} · {fac.get('label', fac['id'])}"
            ),
            "kind": "root",
            "lens": "combo",
            "children": _profile_children(merged),
        }

    # catalog
    attrs = load_json_cached(DATA_PKG, "attributes.json")["all"]
    skills = load_json_cached(DATA_PKG, "skills.json")["all"]
    return {
        "name": "SPI catalog",
        "kind": "root",
        "lens": "catalog",
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
