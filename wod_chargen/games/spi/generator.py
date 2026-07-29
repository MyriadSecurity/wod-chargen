"""SPI oneshot/NPC character generator."""

from __future__ import annotations

from typing import Any, Callable

from wod_chargen.core.costs import lookup_cost
from wod_chargen.core.data_loader import load_json_cached
from wod_chargen.core.models import GenerationResult, LogEntry
from wod_chargen.core.rng import SeededRng
from wod_chargen.core.share import ENGINE_VERSION
from wod_chargen.core.spender import PurchaseCandidate, spend_xp
from wod_chargen.core.xp_strategy import SPI_CATEGORY_TARGETS, creation_pick_weight
from wod_chargen.games.spi.archetypes import (
    effective_profile,
    get_archetype,
    list_archetypes,
    resolve_sub_id,
)
from wod_chargen.games.spi.merit_efficiency import spi_merit_efficiency
from wod_chargen.games.spi.paths import DATA_PKG
from wod_chargen.games.spi.signature_skills import ensure_signature_skill_floor
from wod_chargen.games.spi.trait_biases import resolve_merit_bias
from wod_chargen.venues import resolve_xp_budget

ATTR_CATS = ("mental", "physical", "social")
SKILL_CATS = ("mental", "physical", "social")
AFFINITY_TYPES = ("ghost", "spirit", "mage", "fae", "vampire")
MAX_ATTR = 5
MAX_SKILL = 5
MAX_AFFINITY = 5
# Touchstones are omitted on oneshot sheets; do not spend free dots / XP here.
OMITTED_MERIT_IDS = frozenset({"extra_touchstone"})


def _merit_xp_cost(
    costs: dict[str, Any],
    merit_id: str,
    *,
    current: int,
    target: int,
) -> int:
    """XP for raising a merit from ``current`` to ``target`` (SPI flat rate + exceptions).

    Default merits: 1 XP per dot. Supernatural Resistance: 2 XP per dot.
    Extra Touchstone (if ever enabled): graduated — each new level costs that level.
    """
    dots = max(0, target - current)
    if dots <= 0:
        return 0
    if merit_id == "supernatural_resistance":
        return dots * lookup_cost(costs, "supernatural_resistance", new_level=1)
    if merit_id == "extra_touchstone":
        # Graduated: buy levels current+1 .. target at cost = level each.
        return sum(range(current + 1, target + 1))
    return dots * lookup_cost(costs, "merit", new_level=1)


def _data(name: str) -> dict[str, Any]:
    return load_json_cached(DATA_PKG, name)


def _title(key: str) -> str:
    return key.replace("_", " ").title()


def _pick_specialty_label(
    rng: SeededRng,
    skill: str,
    catalog: dict[str, list[str]],
    *,
    used_labels: set[str] | None = None,
) -> str:
    """Choose an example specialty label for ``skill`` from the catalog."""
    examples = list(catalog.get(skill) or [])
    if not examples:
        return "Focus"
    if used_labels:
        available = [e for e in examples if e not in used_labels]
        if available:
            examples = available
    return str(rng.choice(examples))


def _append_specialty(
    rng: SeededRng,
    char: dict[str, Any],
    skill: str,
    catalog: dict[str, list[str]],
) -> str:
    """Append ``skill:Label`` to ``char['specialties']``; return the entry."""
    used = {
        sp.split(":", 1)[1]
        for sp in char.get("specialties", [])
        if ":" in sp and sp.split(":", 1)[0] == skill
    }
    label = _pick_specialty_label(rng, skill, catalog, used_labels=used)
    entry = f"{skill}:{label}"
    char["specialties"].append(entry)
    return entry


def _merge_bias(*maps: dict[str, float]) -> dict[str, float]:
    out: dict[str, float] = {}
    for m in maps:
        for k, v in (m or {}).items():
            out[k] = out.get(k, 1.0) * float(v)
    return out


def _pick_id(rng: SeededRng, options: dict[str, Any], key: str, ids: list[str]) -> str:
    raw = options.get(key)
    if raw and raw != "any" and str(raw) in ids:
        return str(raw)
    return str(rng.choice(ids))


def _empty_character() -> dict[str, Any]:
    attrs = _data("attributes.json")
    skills = _data("skills.json")
    return {
        "type": "investigator",
        "concept": "",
        "virtue": "",
        "vice": "",
        "attributes": {a: 1 for a in attrs["all"]},
        "skills": {s: 0 for s in skills["all"]},
        "specialties": [],
        "affinities": {a: 0 for a in AFFINITY_TYPES},
        "division": "",
        "faction": "",
        "division_status": 1,
        "archetype": "",
        "sub_archetype": "",
        "options": {"multi_affinity": False, "affinity_lock": "any"},
        "merits": {},
        "integrity": 7,
        "size": 5,
        "advantages": {},
    }


def _assign_category_pools(
    rng: SeededRng,
    ratings: dict[str, int],
    categories: dict[str, list[str]],
    pool_order: list[tuple[str, int]],
    biases: dict[str, float],
    *,
    max_rating: int,
    log: list[LogEntry],
    phase: str,
) -> None:
    """Distribute fixed pools into trait categories (CoD primary/secondary/tertiary)."""
    cat_ids = list(categories.keys())
    # Soft bias: prefer categories whose traits have higher average bias
    cat_scores = []
    for cid in cat_ids:
        traits = categories[cid]
        avg = sum(biases.get(t, 1.0) for t in traits) / max(1, len(traits))
        cat_scores.append((avg * (0.7 + 0.6 * rng.uniform()), cid))
    cat_scores.sort(reverse=True)
    ranked = [cid for _, cid in cat_scores]

    for (label, dots), cat in zip(pool_order, ranked):
        remaining = dots
        while remaining > 0:
            weights = []
            traits = categories[cat]
            for trait in traits:
                cur = ratings[trait]
                w = creation_pick_weight(biases.get(trait, 1.0), cur, max_rating, remaining)
                weights.append(max(w, 0.0))
            if sum(weights) <= 0:
                break
            pick = rng.weighted_choice(traits, weights)
            ratings[pick] += 1
            remaining -= 1
            log.append(
                LogEntry(
                    phase=phase,
                    message=f"{label} +1 {_title(pick)} → {ratings[pick]}",
                    detail={"trait": pick, "category": cat, "pool": label},
                )
            )


def _spend_merit_dots(
    rng: SeededRng,
    char: dict[str, Any],
    merit_defs: list[dict[str, Any]],
    dots: int,
    bias_profile: dict[str, Any],
    *,
    max_affinity_merits: int,
    primary_affinity: str,
    log: list[LogEntry],
) -> None:
    """Spend free creation merit dots.

    General merits unrestricted within the pool. Affinity merits may be bought
    only for the primary Affinity and only up to ``max_affinity_merits`` dots.
    """
    eligible = [
        m
        for m in merit_defs
        if m["id"] not in OMITTED_MERIT_IDS
        and not m.get("style_steps")
        and _merit_creation_eligible(m)
        and (
            m.get("category") == "general"
            or (
                m.get("category") == "affinity"
                and m.get("affinity_type") == primary_affinity
            )
        )
    ]
    remaining = dots
    affinity_spent = 0
    while remaining > 0 and eligible:
        cands = []
        weights = []
        for m in eligible:
            mid = m["id"]
            cur = int(char["merits"].get(mid, 0))
            dmin = int(m.get("dots_min", 1))
            dmax = int(m.get("dots_max", dmin))
            if cur >= dmax:
                continue
            need = dmin if cur == 0 else 1
            if need > remaining:
                continue
            if m.get("category") == "affinity" and affinity_spent + need > max_affinity_merits:
                continue
            if not _prereqs_met(char, m.get("prereqs", []), soft=True):
                continue
            cands.append((m, need))
            weights.append(resolve_merit_bias(bias_profile, mid) * (0.5 + rng.uniform()))
        if not cands:
            break
        m, need = rng.weighted_choice(cands, weights)
        mid = m["id"]
        new_level = int(char["merits"].get(mid, 0)) + need
        if int(char["merits"].get(mid, 0)) == 0:
            new_level = max(new_level, int(m.get("dots_min", 1)))
            need = new_level
            if need > remaining:
                continue
            if m.get("category") == "affinity" and affinity_spent + need > max_affinity_merits:
                continue
        char["merits"][mid] = new_level
        remaining -= need
        if m.get("category") == "affinity":
            affinity_spent += need
        log.append(
            LogEntry(
                phase="creation_merits",
                message=f"Merit {_title(mid)} → {new_level} ({need} dots)",
                detail={"merit": mid, "dots": need, "category": m.get("category")},
            )
        )


def _willpower(char: dict[str, Any]) -> int:
    a = char.get("attributes") or {}
    return int(a.get("resolve", 1)) + int(a.get("composure", 1))


def _specialty_skills(char: dict[str, Any]) -> set[str]:
    out: set[str] = set()
    for sp in char.get("specialties") or []:
        if isinstance(sp, str) and ":" in sp:
            out.add(sp.split(":", 1)[0])
    return out


def _prereq_entry_met(char: dict[str, Any], p: dict[str, Any], *, soft: bool) -> bool:
    """Evaluate a single prereq entry (including any_of / merit_absent)."""
    kind = p.get("kind")
    if kind == "any_of":
        options = list(p.get("options") or [])
        if not options:
            return not soft
        return any(_prereq_entry_met(char, opt, soft=soft) for opt in options)
    if kind == "merit_absent":
        pid = str(p.get("id") or "")
        return int(char["merits"].get(pid, 0)) <= 0
    if kind == "any_skill":
        need = int(p.get("dots", 1))
        skills = char.get("skills") or {}
        return any(int(v) >= need for v in skills.values())
    if kind == "skill_with_specialty":
        need = int(p.get("dots", 1))
        skills = char.get("skills") or {}
        owned = _specialty_skills(char)
        return any(int(skills.get(sk, 0)) >= need and sk in owned for sk in skills)
    if kind == "specialty_on":
        allowed = {str(s) for s in (p.get("skills") or [])}
        if not allowed:
            return not soft
        return bool(_specialty_skills(char) & allowed)
    if kind == "integrity_max":
        cap = int(p.get("dots", 5))
        return int(char.get("integrity", 7)) <= cap
    if kind == "willpower_min":
        need = int(p.get("dots", 1))
        return _willpower(char) >= need
    pid = p.get("id")
    need = int(p.get("dots", 1))
    if kind == "attribute":
        return int(char["attributes"].get(pid, 0)) >= need
    if kind == "skill":
        return int(char["skills"].get(pid, 0)) >= need
    if kind == "merit":
        return int(char["merits"].get(pid, 0)) >= need
    if kind == "affinity":
        return int(char["affinities"].get(pid, 0)) >= need
    return not soft


def _prereqs_met(char: dict[str, Any], prereqs: list[dict[str, Any]], *, soft: bool) -> bool:
    """Check structured prereqs; unresolved stubs are ignored here.

    Unresolved-only merits are gated by ``_merit_creation_eligible`` /
    ``_merit_xp_prereqs_ok`` instead of free-riding.
    """
    for p in prereqs or []:
        if p.get("unresolved"):
            continue
        if not _prereq_entry_met(char, p, soft=soft):
            return False
    return True


_EVALUABLE_PREREQ_KINDS = frozenset(
    {
        "attribute",
        "skill",
        "merit",
        "affinity",
        "merit_absent",
        "any_skill",
        "skill_with_specialty",
        "specialty_on",
        "integrity_max",
        "willpower_min",
    }
)


def _prereq_is_evaluable(p: dict[str, Any]) -> bool:
    """True when the generator can meaningfully check this prereq."""
    if p.get("unresolved"):
        return False
    kind = p.get("kind")
    if kind == "any_of":
        return any(_prereq_is_evaluable(opt) for opt in (p.get("options") or []))
    return kind in _EVALUABLE_PREREQ_KINDS


def _merit_creation_eligible(m: dict[str, Any]) -> bool:
    """Creation pool: allow merits with evaluable prereqs; drop unresolved-only stubs."""
    prereqs = list(m.get("prereqs") or [])
    if not prereqs:
        return True
    return any(_prereq_is_evaluable(p) for p in prereqs)


def _merit_xp_prereqs_ok(char: dict[str, Any], m: dict[str, Any]) -> bool:
    """XP eligibility: skip unresolved-only free rides; enforce structured halves."""
    prereqs = list(m.get("prereqs") or [])
    if not prereqs:
        return True
    if not any(_prereq_is_evaluable(p) for p in prereqs):
        # All unresolved — do not treat as always-met.
        return False
    return _prereqs_met(char, prereqs, soft=False)


def _bundle_prereq_cost(
    char: dict[str, Any],
    costs: dict[str, Any],
    prereqs: list[dict[str, Any]],
) -> tuple[int, list[Callable[[], None]]]:
    """XP + apply callables for unmet structured prereqs (one level of recursion on attrs/skills/affinity)."""
    total = 0
    applies: list[Callable[[], None]] = []
    for p in prereqs or []:
        if p.get("unresolved") or p.get("kind") == "merit_absent":
            continue
        if p.get("kind") == "integrity_max":
            # Cannot buy Integrity down; eligibility is check-only.
            continue
        if p.get("kind") == "any_of":
            options = [opt for opt in (p.get("options") or []) if _prereq_is_evaluable(opt)]
            if not options:
                continue
            if any(_prereq_entry_met(char, opt, soft=False) for opt in options):
                continue
            # Bundle the cheapest unmet option.
            best: tuple[int, list[Callable[[], None]]] | None = None
            for opt in options:
                cost, fns = _bundle_prereq_cost(char, costs, [opt])
                if best is None or cost < best[0]:
                    best = (cost, fns)
            if best:
                total += best[0]
                applies.extend(best[1])
            continue
        kind = p.get("kind")
        pid = p.get("id")
        need = int(p.get("dots", 1))
        if kind == "attribute":
            cur = int(char["attributes"].get(pid, 1))
            while cur < need:
                cur += 1
                total += lookup_cost(costs, "attribute", new_level=cur)
                level = cur

                def _apply_attr(a=pid, lv=level):
                    char["attributes"][a] = max(int(char["attributes"].get(a, 1)), lv)

                applies.append(_apply_attr)
        elif kind == "skill":
            cur = int(char["skills"].get(pid, 0))
            while cur < need:
                cur += 1
                total += lookup_cost(costs, "skill", new_level=cur)
                level = cur

                def _apply_skill(s=pid, lv=level):
                    char["skills"][s] = max(int(char["skills"].get(s, 0)), lv)

                applies.append(_apply_skill)
        elif kind == "affinity":
            cur = int(char["affinities"].get(pid, 0))
            while cur < need:
                cur += 1
                total += lookup_cost(costs, "affinity", new_level=cur)
                level = cur

                def _apply_aff(a=pid, lv=level):
                    char["affinities"][a] = max(int(char["affinities"].get(a, 0)), lv)

                applies.append(_apply_aff)
        elif kind == "merit":
            cur = int(char["merits"].get(pid, 0))
            while cur < need:
                nxt = cur + 1
                total += _merit_xp_cost(costs, str(pid), current=cur, target=nxt)
                cur = nxt
                level = cur

                def _apply_merit(m=pid, lv=level):
                    char["merits"][m] = max(int(char["merits"].get(m, 0)), lv)

                applies.append(_apply_merit)
        elif kind == "any_skill":
            if _prereq_entry_met(char, p, soft=False):
                continue
            skills = char.get("skills") or {}
            # Raise the skill already closest to the floor (cheapest).
            sk = max(skills, key=lambda s: (int(skills.get(s, 0)), s), default=None)
            if sk is None:
                continue
            cur = int(skills.get(sk, 0))
            while cur < need:
                cur += 1
                total += lookup_cost(costs, "skill", new_level=cur)
                level = cur

                def _apply_any_skill(s=sk, lv=level):
                    char["skills"][s] = max(int(char["skills"].get(s, 0)), lv)

                applies.append(_apply_any_skill)
        elif kind == "skill_with_specialty":
            if _prereq_entry_met(char, p, soft=False):
                continue
            skills = char.get("skills") or {}
            owned = _specialty_skills(char)
            # Prefer a skill that already has a specialty, else the highest skill.
            candidates = [s for s in skills if s in owned] or list(skills)
            if not candidates:
                continue
            sk = max(candidates, key=lambda s: (int(skills.get(s, 0)), s))
            cur = int(skills.get(sk, 0))
            while cur < need:
                cur += 1
                total += lookup_cost(costs, "skill", new_level=cur)
                level = cur

                def _apply_sws_skill(s=sk, lv=level):
                    char["skills"][s] = max(int(char["skills"].get(s, 0)), lv)

                applies.append(_apply_sws_skill)
            if sk not in owned:
                total += lookup_cost(costs, "specialty", new_level=1)

                def _apply_sws_spec(s=sk):
                    if s not in _specialty_skills(char):
                        catalog = _data("specialties.json")
                        _append_specialty(SeededRng(0), char, s, catalog)

                applies.append(_apply_sws_spec)
        elif kind == "specialty_on":
            if _prereq_entry_met(char, p, soft=False):
                continue
            allowed = [str(s) for s in (p.get("skills") or [])]
            if not allowed:
                continue
            skills = char.get("skills") or {}
            sk = max(allowed, key=lambda s: (int(skills.get(s, 0)), s))
            if int(skills.get(sk, 0)) < 1:
                total += lookup_cost(costs, "skill", new_level=1)

                def _apply_spec_skill(s=sk):
                    char["skills"][s] = max(int(char["skills"].get(s, 0)), 1)

                applies.append(_apply_spec_skill)
            total += lookup_cost(costs, "specialty", new_level=1)

            def _apply_spec_on(s=sk):
                if s not in _specialty_skills(char):
                    catalog = _data("specialties.json")
                    _append_specialty(SeededRng(0), char, s, catalog)

            applies.append(_apply_spec_on)
        elif kind == "willpower_min":
            if _prereq_entry_met(char, p, soft=False):
                continue
            # Plan Resolve/Composure bumps without mutating char during costing.
            res = int(char["attributes"].get("resolve", 1))
            com = int(char["attributes"].get("composure", 1))
            while res + com < need:
                if res <= com and res < 5:
                    res += 1
                    total += lookup_cost(costs, "attribute", new_level=res)

                    def _apply_wp_res(lv=res):
                        char["attributes"]["resolve"] = max(
                            int(char["attributes"].get("resolve", 1)), lv
                        )

                    applies.append(_apply_wp_res)
                elif com < 5:
                    com += 1
                    total += lookup_cost(costs, "attribute", new_level=com)

                    def _apply_wp_com(lv=com):
                        char["attributes"]["composure"] = max(
                            int(char["attributes"].get("composure", 1)), lv
                        )

                    applies.append(_apply_wp_com)
                else:
                    break
    return total, applies


def _affinity_merit_dots_used(char: dict[str, Any], merit_by_id: dict[str, dict], affinity: str) -> int:
    used = 0
    for mid, dots in char["merits"].items():
        m = merit_by_id.get(mid)
        if not m:
            continue
        if m.get("category") == "affinity" and m.get("affinity_type") == affinity:
            used += int(dots)
    return used


def _top_two_affinity_sum(affinities: dict[str, int]) -> int:
    vals = sorted((int(v) for v in affinities.values()), reverse=True)
    return sum(vals[:2])


def _derive_advantages(char: dict[str, Any]) -> None:
    a = char["attributes"]
    s = char["skills"]
    size = int(char.get("size", 5))
    top_two = _top_two_affinity_sum(char["affinities"])
    max_integrity = max(1, 11 - top_two)
    integrity = min(int(char.get("integrity", 7)), max_integrity)
    char["integrity"] = integrity
    resistant = max(int(a["resolve"]), int(a["stamina"]), int(a["composure"]))
    char["advantages"] = {
        "health": size + int(a["stamina"]),
        "speed": 5 + int(a["strength"]) + int(a["dexterity"]),
        "willpower": int(a["resolve"]) + int(a["composure"]),
        "initiative": int(a["dexterity"]) + int(a["composure"]),
        "perception": int(a["wits"]) + int(a["composure"]),
        "defense": min(int(a["wits"]), int(a["dexterity"])) + int(s["athletics"]),
        "clash_of_wills": resistant + int(s["occult"]),
        "downtimes": int(a["resolve"]) + 1,
        "max_integrity": max_integrity,
        "integrity": integrity,
    }


def _enumerate_purchases(
    rng: SeededRng,
    char: dict[str, Any],
    costs: dict[str, Any],
    merit_defs: list[dict[str, Any]],
    merit_by_id: dict[str, dict],
    attr_cats: dict[str, list[str]],
    skill_list: list[str],
    biases: dict[str, Any],
    specialty_catalog: dict[str, list[str]],
    *,
    multi_affinity: bool,
    primary_affinity: str,
    source: str,
    signature_skills: frozenset[str] | None = None,
) -> list[PurchaseCandidate]:
    cands: list[PurchaseCandidate] = []
    attr_biases = biases.get("attribute_biases", {})
    skill_biases = biases.get("skill_biases", {})
    merit_bias_profile = {
        "merit_biases": biases.get("merit_biases", {}),
        "tag_affinities": biases.get("tag_affinities", {}),
    }
    affinity_biases = biases.get("affinity_biases", {})
    sig_skills = signature_skills or frozenset()

    for cat, traits in attr_cats.items():
        spend_group = f"{cat}_attrs"
        for trait in traits:
            cur = int(char["attributes"][trait])
            if cur >= MAX_ATTR:
                continue
            new_level = cur + 1
            cost = lookup_cost(costs, "attribute", new_level=new_level)

            def apply(t=trait, lv=new_level):
                char["attributes"][t] = lv

            cands.append(
                PurchaseCandidate(
                    item_id=trait,
                    category="attribute",
                    spend_group=spend_group,
                    new_level=new_level,
                    cost=cost,
                    weight=1.0,
                    item_bias=float(attr_biases.get(trait, 1.0)),
                    clan_factor=1.0,
                    source=source,
                    apply=apply,
                )
            )

    for skill in skill_list:
        cur = int(char["skills"][skill])
        if cur >= MAX_SKILL:
            continue
        new_level = cur + 1
        cost = lookup_cost(costs, "skill", new_level=new_level)

        def apply(sk=skill, lv=new_level):
            char["skills"][sk] = lv

        cands.append(
            PurchaseCandidate(
                item_id=skill,
                category="skill",
                spend_group="skills",
                new_level=new_level,
                cost=cost,
                weight=1.2,
                item_bias=float(skill_biases.get(skill, 1.0)),
                clan_factor=1.0,
                source=source,
                apply=apply,
                is_signature=skill in sig_skills,
            )
        )

    # Affinity dots
    allowed = list(AFFINITY_TYPES) if multi_affinity else [primary_affinity]
    for aff in allowed:
        cur = int(char["affinities"][aff])
        if cur >= MAX_AFFINITY:
            continue
        if not multi_affinity and aff != primary_affinity:
            continue
        new_level = cur + 1
        cost = lookup_cost(costs, "affinity", new_level=new_level)

        def apply(a=aff, lv=new_level):
            char["affinities"][a] = lv

        cands.append(
            PurchaseCandidate(
                item_id=aff,
                category="affinity",
                spend_group="affinity",
                new_level=new_level,
                cost=cost,
                weight=1.1,
                item_bias=float(affinity_biases.get(aff, 1.0)),
                clan_factor=1.0,
                source=source,
                apply=apply,
            )
        )

    pool_per = int(_data("creation.json").get("affinity_merit_dots_per_affinity_level", 3))
    for m in merit_defs:
        mid = m["id"]
        if mid in OMITTED_MERIT_IDS:
            continue
        if m.get("style_steps"):
            continue
        cur = int(char["merits"].get(mid, 0))
        dmin = int(m.get("dots_min", 1))
        dmax = int(m.get("dots_max", dmin))
        if cur >= dmax:
            continue
        target = dmin if cur == 0 else cur + 1
        if target > dmax:
            continue
        if not _merit_xp_prereqs_ok(char, m):
            continue

        category = m.get("category", "general")
        aff_type = m.get("affinity_type")
        if category == "affinity":
            if not aff_type:
                continue
            if not multi_affinity and aff_type != primary_affinity:
                continue
            rating = int(char["affinities"].get(aff_type, 0))
            if rating < 1:
                continue
            used = _affinity_merit_dots_used(char, merit_by_id, aff_type)
            room = rating * pool_per - used
            need_dots = target - cur
            if need_dots > room:
                continue
            spend_group = "affinity_merits"
        else:
            spend_group = "merits"

        base_cost = _merit_xp_cost(costs, mid, current=cur, target=target)
        bundle_cost, bundle_applies = _bundle_prereq_cost(char, costs, m.get("prereqs", []))
        # Only bundle if prereqs not already met
        if _prereqs_met(char, m.get("prereqs", []), soft=False):
            bundle_cost, bundle_applies = 0, []
        total_cost = base_cost + bundle_cost
        is_package = cur == 0 and dmin == dmax and target > 1

        def apply(merit_id=mid, lv=target, extras=bundle_applies):
            for fn in extras:
                fn()
            char["merits"][merit_id] = lv

        cands.append(
            PurchaseCandidate(
                item_id=mid,
                category="merit",
                spend_group=spend_group,
                new_level=target,
                cost=total_cost,
                weight=1.0,
                item_bias=resolve_merit_bias(merit_bias_profile, mid),
                clan_factor=1.0,
                source=source,
                apply=apply,
                current_level=cur,
                package=is_package,
                efficiency_fn=(
                    None
                    if is_package
                    else (lambda cur_lv, new_lv, merit=mid: spi_merit_efficiency(merit, cur_lv, new_lv))
                ),
            )
        )

    # Extra specialties via XP
    if len(char["specialties"]) < 8:
        cost = lookup_cost(costs, "specialty", new_level=1)

        def apply_spec():
            # Prefer a skill with dots but no specialty yet
            owned = {sp.split(":")[0] for sp in char["specialties"] if ":" in sp}
            for sk in skill_list:
                if int(char["skills"].get(sk, 0)) >= 1 and sk not in owned:
                    _append_specialty(rng, char, sk, specialty_catalog)
                    return
            fallback = "investigation" if "investigation" in skill_list else skill_list[0]
            _append_specialty(rng, char, fallback, specialty_catalog)

        cands.append(
            PurchaseCandidate(
                item_id="specialty",
                category="specialty",
                spend_group="specialties",
                new_level=len(char["specialties"]) + 1,
                cost=cost,
                weight=0.6,
                item_bias=1.0,
                clan_factor=1.0,
                source=source,
                apply=apply_spec,
            )
        )

    return cands


def generate_character(
    seed: int,
    options: dict[str, Any],
    venue_config: dict[str, Any],
) -> GenerationResult:
    rng = SeededRng(seed)
    log: list[LogEntry] = []
    char = _empty_character()

    creation = _data("creation.json")
    attrs_meta = _data("attributes.json")
    skills_meta = _data("skills.json")
    specialty_catalog = _data("specialties.json")
    divisions = _data("divisions.json")
    factions = _data("factions.json")
    costs = _data("costs.json")
    merits_payload = _data("merits.json")
    merit_defs: list[dict[str, Any]] = list(merits_payload.get("merits", []))
    merit_by_id = {m["id"]: m for m in merit_defs}
    vv = _data("virtues_vices.json")

    division_ids = list(divisions.keys())
    faction_ids = list(factions.keys())
    arch_ids = [a["id"] for a in list_archetypes()]

    division = _pick_id(rng, options, "division", division_ids)
    faction = _pick_id(rng, options, "faction", faction_ids)
    archetype_id = _pick_id(rng, options, "archetype", arch_ids)
    sub_id = resolve_sub_id(archetype_id, options)
    arch = effective_profile(archetype_id, sub_id)

    multi_affinity = bool(options.get("multi_affinity", False))
    affinity_lock = str(options.get("affinity", options.get("affinity_lock", "any")) or "any")
    if affinity_lock not in AFFINITY_TYPES:
        affinity_lock = "any"

    # Primary affinity from lock or merged archetype+subtype biases
    if affinity_lock != "any":
        primary_affinity = affinity_lock
    else:
        ab = arch.get("affinity_biases") or {}
        if ab:
            ids = list(ab.keys())
            weights = [float(ab[i]) for i in ids]
            primary_affinity = str(rng.weighted_choice(ids, weights))
        else:
            primary_affinity = str(rng.choice(list(AFFINITY_TYPES)))

    char["division"] = division
    char["faction"] = faction
    char["archetype"] = archetype_id
    char["sub_archetype"] = sub_id
    char["division_status"] = int(creation.get("division_status_default", 1))
    char["options"] = {"multi_affinity": multi_affinity, "affinity_lock": affinity_lock}
    char["virtue"] = str(rng.choice(vv["virtues"]))
    char["vice"] = str(rng.choice(vv["vices"]))
    char["size"] = int(creation.get("size_default", 5))
    char["integrity"] = int(creation.get("integrity_default", 7))

    log.append(LogEntry(phase="identity", message=f"Division: {divisions[division]['label']}"))
    log.append(LogEntry(phase="identity", message=f"Faction: {factions[faction]['label']}"))
    log.append(
        LogEntry(
            phase="identity",
            message=f"Archetype: {arch.get('label', archetype_id)} / {arch.get('sub_label', sub_id)}",
        )
    )
    log.append(LogEntry(phase="identity", message=f"Primary Affinity: {_title(primary_affinity)}"))

    div = divisions[division]
    fac = factions[faction]
    attr_biases = _merge_bias(
        arch.get("attribute_biases", {}),
        div.get("attribute_biases", {}),
        fac.get("attribute_biases", {}),
    )
    skill_biases = _merge_bias(
        arch.get("skill_biases", {}),
        div.get("skill_biases", {}),
        fac.get("skill_biases", {}),
    )
    merit_biases = _merge_bias(
        arch.get("merit_biases", {}),
        div.get("merit_biases", {}),
        fac.get("merit_biases", {}),
    )
    tag_affinities = _merge_bias(
        arch.get("tag_affinities", {}),
        div.get("tag_affinities", {}),
        fac.get("tag_affinities", {}),
    )
    merit_bias_profile = {
        "merit_biases": merit_biases,
        "tag_affinities": tag_affinities,
    }
    affinity_biases = _merge_bias(
        arch.get("affinity_biases", {}),
        fac.get("affinity_biases", {}),
    )
    affinity_biases[primary_affinity] = affinity_biases.get(primary_affinity, 1.0) * 1.4

    attr_pools = [
        ("primary", int(creation["attributes"]["primary"])),
        ("secondary", int(creation["attributes"]["secondary"])),
        ("tertiary", int(creation["attributes"]["tertiary"])),
    ]
    skill_pools = [
        ("primary", int(creation["skills"]["primary"])),
        ("secondary", int(creation["skills"]["secondary"])),
        ("tertiary", int(creation["skills"]["tertiary"])),
    ]
    attr_cats = {c: list(attrs_meta[c]) for c in ATTR_CATS}
    skill_cats = {c: list(skills_meta[c]) for c in SKILL_CATS}

    _assign_category_pools(
        rng,
        char["attributes"],
        attr_cats,
        attr_pools,
        attr_biases,
        max_rating=MAX_ATTR,
        log=log,
        phase="creation_attributes",
    )
    _assign_category_pools(
        rng,
        char["skills"],
        skill_cats,
        skill_pools,
        skill_biases,
        max_rating=MAX_SKILL,
        log=log,
        phase="creation_skills",
    )
    signature_skills = ensure_signature_skill_floor(
        rng,
        char["skills"],
        skill_biases,
        skill_cats,
        log,
        floor=3,
        max_rating=MAX_SKILL,
    )

    # Free Affinity 1
    char["affinities"][primary_affinity] = 1
    log.append(
        LogEntry(
            phase="creation_affinity",
            message=f"Free Affinity 1 → {_title(primary_affinity)}",
            detail={"affinity": primary_affinity},
        )
    )

    # Specialties
    n_spec = int(creation.get("specialties", 3))
    skill_ranked = sorted(
        skills_meta["all"],
        key=lambda s: (skill_biases.get(s, 1.0) * (0.5 + rng.uniform()) * max(1, char["skills"][s])),
        reverse=True,
    )
    for sk in skill_ranked:
        if len(char["specialties"]) >= n_spec:
            break
        if char["skills"][sk] <= 0:
            continue
        entry = _append_specialty(rng, char, sk, specialty_catalog)
        log.append(LogEntry(phase="creation_specialties", message=f"Specialty: {entry}"))

    _spend_merit_dots(
        rng,
        char,
        merit_defs,
        int(creation.get("merit_dots", 7)),
        merit_bias_profile,
        max_affinity_merits=int(creation.get("max_affinity_merit_dots_at_creation", 3)),
        primary_affinity=primary_affinity,
        log=log,
    )

    venue_id = str(venue_config.get("id", "fixed_35"))
    xp_budget, xp_lines = resolve_xp_budget(venue_id, options)
    for line in xp_lines:
        log.append(LogEntry(phase="xp_budget", message=line))

    biases_pack = {
        "attribute_biases": attr_biases,
        "skill_biases": skill_biases,
        "merit_biases": merit_biases,
        "tag_affinities": tag_affinities,
        "affinity_biases": affinity_biases,
    }
    source = f"archetype:{archetype_id}/{sub_id}"

    def enumerate_fn() -> list[PurchaseCandidate]:
        return _enumerate_purchases(
            rng,
            char,
            costs,
            merit_defs,
            merit_by_id,
            attr_cats,
            list(skills_meta["all"]),
            biases_pack,
            specialty_catalog,
            multi_affinity=multi_affinity,
            primary_affinity=primary_affinity,
            source=source,
            signature_skills=signature_skills,
        )

    # Jitter SPI category targets
    targets = {
        k: v * (0.85 + 0.3 * rng.uniform()) for k, v in SPI_CATEGORY_TARGETS.items()
    }
    total_t = sum(targets.values())
    targets = {k: v / total_t for k, v in targets.items()}

    remaining, xp_log, spend_logs = spend_xp(
        rng,
        xp_budget,
        enumerate_fn,
        source=source,
        category_targets=targets,
    )
    log.extend(spend_logs)

    # Enforce single-affinity if toggle off (belt and suspenders)
    if not multi_affinity:
        for aff in AFFINITY_TYPES:
            if aff != primary_affinity:
                char["affinities"][aff] = 0

    _derive_advantages(char)

    return GenerationResult(
        engine_version=ENGINE_VERSION,
        schema="0.1",
        game_id="spi",
        venue_id=venue_id,
        seed=seed,
        options=dict(options),
        character=char,
        creation_log=log,
        xp_log=xp_log,
        xp_budget=xp_budget,
        xp_spent=xp_budget - remaining,
        xp_remaining=remaining,
    )
