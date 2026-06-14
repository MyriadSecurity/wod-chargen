"""Build hierarchical graph data for weight mind maps (all generation lenses)."""

from __future__ import annotations

from typing import Any, Callable

from wod_chargen.core.data_loader import load_json_cached
from wod_chargen.games.lotn_v5.archetypes import ArchetypeProfile, archetype_display_label, effective_profile, get_archetype, load_all_archetypes
from wod_chargen.games.lotn_v5.clan_discipline_adapt import adapt_profile_for_clan
from wod_chargen.games.lotn_v5.predators import apply_predator_biases, load_predator_types, predator_by_id
from wod_chargen.games.lotn_v5.trait_biases import load_trait_tags, resolve_trait_bias

DATA = "wod_chargen.games.lotn_v5.data"

LENSES: dict[str, str] = {
    "archetype": "Archetypes",
    "predator": "Predator (feed) types",
    "clan": "Clans",
    "catalog": "Catalog defaults",
    "category": "Trait categories",
    "combo": "Archetype + feed + clan",
}

CATEGORY_IDS: dict[str, str] = {
    "attributes": "Attributes",
    "skills": "Skills",
    "disciplines": "Disciplines",
    "backgrounds": "Background types",
    "spheres": "Contact spheres",
    "modifiers": "Background modifiers",
    "merits": "Merits",
    "flaws": "Flaws",
    "powers": "Discipline powers",
    "tags": "Theme tags",
}


def _leaf(name: str, value: float, kind: str, trait_id: str, **extra: Any) -> dict[str, Any]:
    node: dict[str, Any] = {
        "name": name.replace("_", " ").title() if name == trait_id else name,
        "value": round(float(value), 3),
        "kind": kind,
        "id": trait_id,
    }
    node.update(extra)
    return node


def _section(label: str, block: dict[str, float], kind: str) -> dict[str, Any] | None:
    if not block:
        return None
    items = sorted(block.items(), key=lambda kv: (-kv[1], kv[0]))
    return {
        "name": label,
        "kind": "section",
        "children": [_leaf(k, v, kind, k) for k, v in items],
    }


def _info_section(label: str, items: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not items:
        return None
    return {"name": label, "kind": "section", "children": items}


def _nav_node(
    name: str,
    kind: str,
    node_id: str,
    *,
    lens: str,
    extra: dict[str, Any] | None = None,
    children: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    node: dict[str, Any] = {
        "name": name,
        "kind": kind,
        "id": node_id,
        "lens": lens,
        "nav": True,
    }
    if extra:
        node.update(extra)
    if children:
        node["children"] = children
    return node


# --- Archetypes ---


def build_archetype_profile_tree(arch_id: str, sub_id: str, character_type: str = "vampire") -> dict[str, Any]:
    base = get_archetype(arch_id)
    sub = next(s for s in base.sub_archetypes if s.id == sub_id)
    profile = effective_profile(arch_id, sub_id, character_type)
    sections: list[dict[str, Any] | None] = [
        _section("Spend weights", profile.weights, "weight"),
        _section("Tag affinities", profile.tag_affinities, "tag"),
        _section("Attributes", profile.attribute_biases, "attribute"),
        _section("Skills", profile.skill_biases, "skill"),
        _section("Disciplines", profile.discipline_biases, "discipline"),
        _section("Backgrounds", profile.background_biases, "background"),
        _section("Spheres", profile.sphere_biases, "sphere"),
        _section("Modifiers", profile.modifier_biases, "modifier"),
        _section("Merits", profile.merit_biases, "merit"),
        _section("Flaws", profile.flaw_biases, "flaw"),
        _section("Loresheets", profile.loresheet_biases, "loresheet"),
        _section("Discipline powers", profile.discipline_power_biases, "power"),
    ]
    return {
        "name": f"{archetype_display_label(base)} · {sub.label}",
        "kind": "root",
        "lens": "archetype",
        "arch": arch_id,
        "sub": sub_id,
        "type": character_type,
        "children": [s for s in sections if s],
    }


def build_archetype_overview_tree() -> dict[str, Any]:
    children: list[dict[str, Any]] = []
    for arch_id in sorted(load_all_archetypes().keys()):
        profile = get_archetype(arch_id)
        sub = profile.sub_archetypes[0]
        ctype = profile.allowed_types[0] if profile.allowed_types else "vampire"
        merged = effective_profile(arch_id, sub.id, ctype)
        branches: list[dict[str, Any]] = []
        for label, block, kind in (
            ("Tags", dict(list(merged.tag_affinities.items())[:5]), "tag"),
            ("Skills", dict(list(merged.skill_biases.items())[:4]), "skill"),
            ("Disciplines", dict(list(merged.discipline_biases.items())[:3]), "discipline"),
        ):
            sec = _section(label, block, kind)
            if sec:
                branches.append(sec)
        children.append(
            _nav_node(
                archetype_display_label(profile),
                "archetype",
                arch_id,
                lens="archetype",
                extra={"sub": sub.id, "type": ctype},
                children=branches,
            )
        )
    return {"name": "Archetypes", "kind": "root", "lens": "archetype", "children": children}


def archetype_picker_options() -> list[dict[str, Any]]:
    options: list[dict[str, Any]] = []
    for profile in sorted(load_all_archetypes().values(), key=lambda p: p.id):
        ctype = profile.allowed_types[0] if profile.allowed_types else "vampire"
        for sub in profile.sub_archetypes:
            options.append(
                {
                    "id": f"{profile.id}:{sub.id}",
                    "label": f"{archetype_display_label(profile)} — {sub.label}",
                    "arch": profile.id,
                    "sub": sub.id,
                    "type": ctype,
                }
            )
    return options


# --- Predator / feed types ---


def build_predator_profile_tree(predator_id: str) -> dict[str, Any]:
    pred = predator_by_id(predator_id)
    pool_weights = pred.get("pool_weights") or {}
    benefit_weights = pred.get("benefit_weights") or {}
    package = pred.get("package") or {}

    sections: list[dict[str, Any] | None] = [
        _section("Selection weight", {"pick_chance": float(pred.get("weight", 1.0))}, "weight"),
        _section("Pool attribute weights", pool_weights.get("attributes", {}), "attribute"),
        _section("Pool skill weights", pool_weights.get("skills", {}), "skill"),
        _section("Benefit — backgrounds", benefit_weights.get("backgrounds", {}), "background"),
        _section("Benefit — skills", benefit_weights.get("skills", {}), "skill"),
        _section("Benefit — disciplines", benefit_weights.get("disciplines", {}), "discipline"),
    ]

    pool = pred.get("pool") or {}
    if pool:
        feeding = _info_section(
            "Feeding pool",
            [
                _leaf(pool["attribute"], 1.0, "attribute", pool["attribute"]),
                _leaf(pool["skill"], 1.0, "skill", pool["skill"]),
            ],
        )
        sections.insert(0, feeding)

    pkg_merits = [
        _leaf(m.get("label", m["id"]), float(m.get("dots", 1)), "merit", m["id"])
        for m in package.get("merits", [])
    ]
    pkg_flaws = [
        _leaf(f.get("label", f["id"]), float(f.get("dots", 1)), "flaw", f["id"])
        for f in package.get("flaws", [])
    ]
    pkg_bg = [
        _leaf(
            f"{b['type']} ({b.get('dots', 1)} dots)",
            float(b.get("dots", 1)),
            "background",
            b["type"],
        )
        for b in package.get("backgrounds", [])
    ]
    sections.extend(
        [
            _info_section("Package merits", pkg_merits),
            _info_section("Package flaws", pkg_flaws),
            _info_section("Package backgrounds", pkg_bg),
        ]
    )

    if pred.get("requires_max_blood_potency") is not None:
        sections.append(
            _section(
                "Restrictions",
                {"max_blood_potency": float(pred["requires_max_blood_potency"])},
                "weight",
            )
        )

    return {
        "name": pred["label"],
        "kind": "root",
        "lens": "predator",
        "id": predator_id,
        "children": [s for s in sections if s],
    }


def build_predator_overview_tree() -> dict[str, Any]:
    children: list[dict[str, Any]] = []
    for pred in sorted(load_predator_types(), key=lambda p: p["id"]):
        pw = pred.get("pool_weights") or {}
        bw = pred.get("benefit_weights") or {}
        skills = {**pw.get("skills", {}), **bw.get("skills", {})}
        branches: list[dict[str, Any]] = []
        for sec in (
            _section("Pool skills", dict(list(pw.get("skills", {}).items())[:4]), "skill"),
            _section("Benefit backgrounds", dict(list(bw.get("backgrounds", {}).items())[:3]), "background"),
        ):
            if sec:
                branches.append(sec)
        children.append(
            _nav_node(
                pred["label"],
                "predator",
                pred["id"],
                lens="predator",
                extra={"weight": pred.get("weight", 1.0)},
                children=branches or None,
            )
        )
    return {"name": "Predator (feed) types", "kind": "root", "lens": "predator", "children": children}


def predator_picker_options() -> list[dict[str, Any]]:
    return [
        {"id": p["id"], "label": p["label"], "summary": p.get("summary", "")[:80]}
        for p in sorted(load_predator_types(), key=lambda p: p["id"])
    ]


# --- Clans ---


def build_clan_profile_tree(clan_id: str) -> dict[str, Any]:
    clans = load_json_cached(DATA, "clans.json")
    clan = clans.get(clan_id)
    if clan is None:
        raise ValueError(f"Unknown clan: {clan_id}")

    discs = clan.get("disciplines", [])
    in_clan = {d: 2.0 for d in discs} if discs else {}
    all_discs = set(load_json_cached(DATA, "disciplines.json")["all"])
    out_clan = {d: 0.3 for d in sorted(all_discs - set(discs))}

    tags_data = load_trait_tags()
    disc_tags: dict[str, float] = {}
    for d in discs:
        for tag in tags_data.get("disciplines", {}).get(d, tags_data.get("powers", {}).get(d, [])):
            if isinstance(tag, str) and not tag.startswith("opposed"):
                disc_tags[tag] = disc_tags.get(tag, 1.0) + 0.35

    sections: list[dict[str, Any] | None] = [
        _section("In-clan disciplines (pick pool)", in_clan, "discipline"),
        _section("Out-of-clan (XP factor)", dict(list(out_clan.items())[:6]), "discipline"),
        _section("In-clan theme tags", disc_tags, "tag"),
        _section("Loresheets", clan.get("loresheet_biases", {}), "loresheet"),
    ]
    if clan.get("discipline_note"):
        sections.insert(
            0,
            _info_section("Note", [_leaf(clan["discipline_note"], 1.0, "weight", "note")]),
        )

    return {
        "name": clan["label"],
        "kind": "root",
        "lens": "clan",
        "id": clan_id,
        "children": [s for s in sections if s],
    }


def build_clan_overview_tree() -> dict[str, Any]:
    clans = load_json_cached(DATA, "clans.json")
    children: list[dict[str, Any]] = []
    for clan_id in sorted(clans.keys()):
        clan = clans[clan_id]
        discs = clan.get("disciplines", [])
        branches = []
        if discs:
            sec = _section("In-clan", {d: 2.0 for d in discs}, "discipline")
            if sec:
                branches.append(sec)
        children.append(
            _nav_node(clan["label"], "clan", clan_id, lens="clan", children=branches or None)
        )
    return {"name": "Clans", "kind": "root", "lens": "clan", "children": children}


def clan_picker_options() -> list[dict[str, Any]]:
    clans = load_json_cached(DATA, "clans.json")
    return [
        {"id": cid, "label": c["label"], "kind": c.get("kind", "clan")}
        for cid, c in sorted(clans.items(), key=lambda x: x[1]["label"])
    ]


# --- Catalog defaults ---


def build_catalog_overview_tree() -> dict[str, Any]:
    bg = load_json_cached(DATA, "backgrounds.json")
    creation_bias = {
        t: float(spec.get("creation_bias", 1.0)) for t, spec in bg["backgrounds"].items()
    }
    spheres = {s["id"]: 1.0 for s in bg["spheres"]}
    modifiers: dict[str, float] = {}
    for spec in bg["backgrounds"].values():
        for mod in spec.get("advantages", []) + spec.get("disadvantages", []):
            modifiers.setdefault(mod["id"], 1.0)

    tags = load_trait_tags()
    tag_counts = {tid: len(traits) for tid, traits in tags.get("tags", {}).items()}

    sections = [
        _section("Background creation bias", creation_bias, "background"),
        _section("Spheres (neutral pick)", spheres, "sphere"),
        _section("Modifiers (eligible)", modifiers, "modifier"),
        _section("Tag index (trait count)", tag_counts, "tag"),
    ]
    return {
        "name": "Catalog defaults",
        "kind": "root",
        "lens": "catalog",
        "children": [s for s in sections if s],
    }


# --- Trait categories (cross-archetype heat) ---


def _registry_for_category(category: str) -> list[str]:
    if category == "attributes":
        return load_json_cached(DATA, "attributes.json")["all"]
    if category == "skills":
        return load_json_cached(DATA, "skills.json")["all"]
    if category == "disciplines":
        return load_json_cached(DATA, "disciplines.json")["all"]
    if category == "backgrounds":
        return list(load_json_cached(DATA, "backgrounds.json")["backgrounds"].keys())
    if category == "spheres":
        return [s["id"] for s in load_json_cached(DATA, "backgrounds.json")["spheres"]]
    if category == "modifiers":
        bg = load_json_cached(DATA, "backgrounds.json")
        mods: set[str] = set()
        for spec in bg["backgrounds"].values():
            for mod in spec.get("advantages", []) + spec.get("disadvantages", []):
                mods.add(mod["id"])
        return sorted(mods)
    if category == "merits":
        return [m["id"] for m in load_json_cached(DATA, "merits_flaws.json")["merits"]]
    if category == "flaws":
        return [f["id"] for f in load_json_cached(DATA, "merits_flaws.json")["flaws"]]
    if category == "powers":
        ids: list[str] = []
        for disc in load_json_cached(DATA, "discipline_powers.json")["disciplines"]:
            for p in disc.get("powers", []):
                if not p["id"].startswith("counterfeit"):
                    ids.append(p["id"])
        return ids
    if category == "tags":
        return sorted(load_trait_tags().get("tags", {}).keys())
    raise ValueError(f"Unknown category: {category}")


def _max_archetype_bias(category: str, trait_id: str) -> float:
    peak = 1.0
    for profile in load_all_archetypes().values():
        ctype = profile.allowed_types[0] if profile.allowed_types else "vampire"
        for sub in profile.sub_archetypes:
            merged = effective_profile(profile.id, sub.id, ctype)
            peak = max(peak, resolve_trait_bias(merged, trait_id, category))
    return peak


def _max_tag_affinity(tag_id: str) -> float:
    peak = 1.0
    for profile in load_all_archetypes().values():
        ctype = profile.allowed_types[0] if profile.allowed_types else "vampire"
        for sub in profile.sub_archetypes:
            merged = effective_profile(profile.id, sub.id, ctype)
            peak = max(peak, float(merged.tag_affinities.get(tag_id, 1.0)))
    return peak


def _traits_for_tag(tag_id: str) -> dict[str, str]:
    """Map trait_id -> resolve category for traits carrying this tag."""
    tags_data = load_trait_tags()
    cat_map = {
        "skills": "skills",
        "merits": "merits",
        "flaws": "flaws",
        "powers": "powers",
        "backgrounds": "backgrounds",
        "spheres": "spheres",
        "modifiers": "modifiers",
        "attributes": "attributes",
        "disciplines": "disciplines",
    }
    found: dict[str, str] = {}
    for block, resolve_cat in cat_map.items():
        for tid, ttags in tags_data.get(block, {}).items():
            tags = ttags if isinstance(ttags, list) else [ttags]
            if tag_id in tags:
                found[tid] = resolve_cat
    return found


def build_category_profile_tree(category: str) -> dict[str, Any]:
    cat_label = CATEGORY_IDS.get(category, category.title())
    tags_data = load_trait_tags()

    if category == "tags":
        children: list[dict[str, Any]] = []
        for tag_id in sorted(tags_data.get("tags", {}).keys()):
            linked = _traits_for_tag(tag_id)
            sample = dict(list(linked.items())[:10])
            trait_leaves = [
                _leaf(tid, _max_archetype_bias(cat, tid), cat, tid)
                for tid, cat in sample.items()
            ]
            node = _leaf(
                tags_data["tags"][tag_id].get("label", tag_id.replace("_", " ").title()),
                _max_tag_affinity(tag_id),
                "tag",
                tag_id,
            )
            if trait_leaves:
                node["children"] = [_info_section("Sample traits", trait_leaves)]
            children.append(node)
        return {"name": cat_label, "kind": "root", "lens": "category", "id": category, "children": children}

    traits = _registry_for_category(category)
    resolve_cat = category.rstrip("s") if category in ("powers",) else category.rstrip("s")
    if category == "attributes":
        resolve_cat = "attributes"
    elif category == "skills":
        resolve_cat = "skills"
    elif category == "disciplines":
        resolve_cat = "disciplines"
    elif category == "backgrounds":
        resolve_cat = "backgrounds"
    elif category == "spheres":
        resolve_cat = "spheres"
    elif category == "modifiers":
        resolve_cat = "modifiers"
    elif category == "merits":
        resolve_cat = "merits"
    elif category == "flaws":
        resolve_cat = "flaws"
    elif category == "powers":
        resolve_cat = "powers"

    trait_nodes: list[dict[str, Any]] = []
    for tid in traits:
        peak = _max_archetype_bias(resolve_cat, tid)
        tag_list = tags_data.get(category if category != "powers" else "powers", {}).get(tid, [])
        if not tag_list and category == "disciplines":
            tag_list = tags_data.get("disciplines", {}).get(tid, [])
        tag_children = [
            _leaf(t, 1.0, "tag", t) for t in (tag_list if isinstance(tag_list, list) else [tag_list])
        ]
        node = _leaf(tid.replace("_", " ").title(), peak, resolve_cat, tid)
        if tag_children:
            sec = _info_section("Tags", tag_children)
            if sec:
                node["children"] = [sec]
        trait_nodes.append(node)

    if category == "powers" and len(trait_nodes) > 40:
        trait_nodes = sorted(trait_nodes, key=lambda n: -n["value"])[:40]

    return {
        "name": cat_label,
        "kind": "root",
        "lens": "category",
        "id": category,
        "children": [_info_section("Traits", trait_nodes)] if trait_nodes else [],
    }


def build_category_overview_tree() -> dict[str, Any]:
    children = [
        _nav_node(label, "category", cat_id, lens="category")
        for cat_id, label in CATEGORY_IDS.items()
    ]
    return {"name": "Trait categories", "kind": "root", "lens": "category", "children": children}


def category_picker_options() -> list[dict[str, Any]]:
    return [{"id": k, "label": v} for k, v in CATEGORY_IDS.items()]


# --- Combined archetype + predator + clan (generation profile) ---


def generation_profile(
    arch_id: str,
    sub_id: str,
    predator_id: str,
    clan_id: str,
    character_type: str = "vampire",
) -> ArchetypeProfile:
    """Merged profile matching generator order: archetype → clan → predator."""
    profile = effective_profile(arch_id, sub_id, character_type)
    profile = adapt_profile_for_clan(profile, clan_id or None)
    pred = predator_by_id(predator_id)
    return apply_predator_biases(profile, pred)


def build_combo_profile_tree(
    arch_id: str,
    sub_id: str,
    predator_id: str,
    clan_id: str = "brujah",
    character_type: str = "vampire",
) -> dict[str, Any]:
    base = get_archetype(arch_id)
    sub = next(s for s in base.sub_archetypes if s.id == sub_id)
    pred = predator_by_id(predator_id)
    clans = load_json_cached(DATA, "clans.json")
    clan = clans.get(clan_id, {"label": clan_id.replace("_", " ").title()})
    merged = generation_profile(arch_id, sub_id, predator_id, clan_id, character_type)

    sections: list[dict[str, Any] | None] = [
        _section("Spend weights", merged.weights, "weight"),
        _section("Tag affinities", merged.tag_affinities, "tag"),
        _section("Combined attributes", merged.attribute_biases, "attribute"),
        _section("Combined skills", merged.skill_biases, "skill"),
        _section("Combined disciplines", merged.discipline_biases, "discipline"),
        _section("Combined discipline powers", merged.discipline_power_biases, "power"),
        _section("Archetype backgrounds", merged.background_biases, "background"),
        _section(
            "Predator background boost",
            (pred.get("benefit_weights") or {}).get("backgrounds", {}),
            "background",
        ),
        _section("Spheres", merged.sphere_biases, "sphere"),
        _section("Modifiers", merged.modifier_biases, "modifier"),
        _section("Merits", merged.merit_biases, "merit"),
        _section("Flaws", merged.flaw_biases, "flaw"),
        _section("Loresheets", merged.loresheet_biases, "loresheet"),
    ]
    return {
        "name": f"{archetype_display_label(base)} · {sub.label} · {clan['label']} · {pred['label']}",
        "kind": "root",
        "lens": "combo",
        "arch": arch_id,
        "sub": sub_id,
        "predator": predator_id,
        "clan": clan_id,
        "type": character_type,
        "children": [s for s in sections if s],
    }


def build_combo_overview_tree() -> dict[str, Any]:
    return {
        "name": "Archetype + feed + clan",
        "kind": "root",
        "lens": "combo",
        "children": [
            _info_section(
                "How to use",
                [
                    _leaf(
                        "Single profile: pick archetype, feed type, and clan to see the merged generation weights",
                        1.0,
                        "weight",
                        "hint",
                    )
                ],
            )
        ],
    }


def combo_picker_options() -> list[dict[str, str]]:
    return []


# --- Unified API ---


def build_tree(lens: str, mode: str, **params: str) -> dict[str, Any]:
    if lens == "archetype":
        if mode == "overview":
            return build_archetype_overview_tree()
        return build_archetype_profile_tree(
            params.get("arch", "diplomat"),
            params.get("sub", "silver_tongue"),
            params.get("type", "vampire"),
        )
    if lens == "predator":
        if mode == "overview":
            return build_predator_overview_tree()
        return build_predator_profile_tree(params.get("id", "alleycat"))
    if lens == "clan":
        if mode == "overview":
            return build_clan_overview_tree()
        return build_clan_profile_tree(params.get("id", "brujah"))
    if lens == "catalog":
        return build_catalog_overview_tree()
    if lens == "category":
        if mode == "overview":
            return build_category_overview_tree()
        return build_category_profile_tree(params.get("id", "skills"))
    if lens == "combo":
        if mode == "overview":
            return build_combo_overview_tree()
        return build_combo_profile_tree(
            params.get("arch", "diplomat"),
            params.get("sub", "silver_tongue"),
            params.get("predator", "alleycat"),
            params.get("clan", "brujah"),
            params.get("type", "vampire"),
        )
    raise ValueError(f"Unknown lens: {lens}")


def picker_for_lens(lens: str) -> list[dict[str, Any]]:
    pickers: dict[str, Callable[[], list[dict[str, Any]]]] = {
        "archetype": archetype_picker_options,
        "predator": predator_picker_options,
        "clan": clan_picker_options,
        "category": category_picker_options,
        "combo": archetype_picker_options,
    }
    fn = pickers.get(lens)
    return fn() if fn else []


# Back-compat aliases
build_profile_tree = build_archetype_profile_tree
build_overview_tree = build_archetype_overview_tree
picker_options = archetype_picker_options
