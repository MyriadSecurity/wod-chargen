"""Main LoTN V5 procedural generation pipeline."""

from __future__ import annotations

from typing import Any

from wod_chargen.core.costs import lookup_cost
from wod_chargen.core.data_loader import load_json_cached
from wod_chargen.core.models import GenerationResult, LogEntry
from wod_chargen.core.rng import SeededRng
from wod_chargen.core.share import ENGINE_VERSION
from wod_chargen.core.spender import PurchaseCandidate, spend_xp
from wod_chargen.games.lotn_v5.archetypes import effective_profile
from wod_chargen.venues import resolve_xp_budget

DATA = "wod_chargen.games.lotn_v5.data"
DEFAULT_CAP = 5


def _resolve_caps(creation: dict[str, Any]) -> dict[str, int]:
    """Per-category rating ceilings (LoTN V5 defaults + creation overrides)."""
    return {
        "attribute": DEFAULT_CAP,
        "skill": DEFAULT_CAP,
        "background": DEFAULT_CAP,
        "discipline": int(creation.get("discipline_max", DEFAULT_CAP)),
        "merit": 3,
        "loresheet": 3,
        "blood_potency": 3,
        "thin_blood_formula": int(creation.get("formula_max", DEFAULT_CAP)),
        "ghoul_power": 1,
    }


def _empty_character(options: dict[str, Any]) -> dict[str, Any]:
    return {
        "character_type": options.get("type", "vampire"),
        "clan": options.get("clan"),
        "domitor_clan": options.get("domitor_clan"),
        "archetype": options.get("arch"),
        "sub_archetype": options.get("sub"),
        "predator": None,
        "generation": 13,
        "blood_potency": 1,
        "humanity": 7,
        "attributes": {},
        "skills": {},
        "disciplines": {},
        "backgrounds": {},
        "merits": {},
        "loresheets": {},
        "ghoul_powers": {},
        "thin_blood_formulas": {},
    }


def _placement_weight(bias: float, current: int, max_rating: int) -> float:
    """Archetype bias tempered by remaining room — spreads pool dots instead of stacking."""
    room = max_rating - current
    if room <= 0:
        return 0.0
    return bias * room


def _pool_count(pool: dict[str, int], rating: int) -> int:
    return int(pool.get(str(rating), pool.get(rating, 0)))


def _assign_one_dot_pick(
    rng: SeededRng,
    dots: int,
    items: list[str],
    biases: dict[str, float],
    target: dict[str, int],
    log: list[LogEntry],
    phase: str,
    label: str,
    *,
    max_rating: int,
) -> str | None:
    """Assign one creation pool chunk to a single unused trait.

    LoTN creation: each attribute/skill/background receives at most one pool
    assignment. A +4 pick cannot be followed by a +1 on the same trait.
    """
    eligible = [i for i in items if target.get(i, 0) == 0 and dots <= max_rating]
    if not eligible:
        log.append(
            LogEntry(
                phase=phase,
                message=f"{label} +{dots} unplaced (no unused traits)",
                detail={"pool_rating": dots, "rating": 0},
            )
        )
        return None

    weights = [_placement_weight(biases.get(i, 1.0), 0, max_rating) for i in eligible]
    pick = rng.weighted_choice(eligible, weights)
    target[pick] = dots
    log.append(
        LogEntry(
            phase=phase,
            message=f"{label} {pick} +{dots} → {dots}",
            detail={"pool_rating": dots, "rating": dots, "previous": 0},
        )
    )
    return pick


def _assign_dots_at_rating(
    rng: SeededRng,
    rating: int,
    count: int,
    items: list[str],
    biases: dict[str, float],
    target: dict[str, int],
    log: list[LogEntry],
    phase: str,
    label: str,
    *,
    max_rating: int,
) -> None:
    for _ in range(count):
        _assign_one_dot_pick(
            rng, rating, items, biases, target, log, phase, label, max_rating=max_rating
        )


def _assign_dots(
    rng: SeededRng,
    pool: dict[str, int],
    items: list[str],
    biases: dict[str, float],
    target: dict[str, int],
    log: list[LogEntry],
    phase: str,
    label: str,
    *,
    max_rating: int = DEFAULT_CAP,
) -> None:
    for rating in sorted({int(k) for k in pool}, reverse=True):
        count = _pool_count(pool, rating)
        if count > 0:
            _assign_dots_at_rating(
                rng, rating, count, items, biases, target, log, phase, label, max_rating=max_rating
            )


def _assign_one_discipline_pick(
    rng: SeededRng,
    char: dict[str, Any],
    clan_pool: list[str],
    profile: Any,
    dots: int,
    slot_key: str,
    log: list[LogEntry],
    *,
    max_rating: int,
) -> str | None:
    """Assign one free discipline slot to an unused in-clan discipline."""
    eligible = [d for d in clan_pool if char["disciplines"].get(d, 0) == 0 and dots <= max_rating]
    if not eligible:
        log.append(
            LogEntry(
                phase="base",
                message=f"Discipline +{dots} unplaced (no unused in-clan disciplines)",
                detail={"slot": slot_key, "pool_rating": dots, "rating": 0},
            )
        )
        return None

    weights = [_placement_weight(profile.discipline_biases.get(d, 1.0), 0, max_rating) for d in eligible]
    disc = rng.weighted_choice(eligible, weights)
    char["disciplines"][disc] = dots
    log.append(
        LogEntry(
            phase="base",
            message=f"Discipline {disc} +{dots} → {dots}",
            detail={"discipline": disc, "slot": slot_key, "pool_rating": dots, "rating": dots, "previous": 0},
        )
    )
    return disc


def _pick_predator(rng: SeededRng, char: dict[str, Any], log: list[LogEntry]) -> None:
    types = load_json_cached(DATA, "predator_types.json")["types"]
    pick = rng.weighted_choice(types, [t["weight"] for t in types])
    char["predator"] = pick["id"]
    log.append(LogEntry(phase="base", message=f"Predator type: {pick['label']}", detail={"id": pick["id"]}))


def _clan_disciplines(clan_id: str | None) -> list[str]:
    if not clan_id:
        return []
    clans = load_json_cached(DATA, "clans.json")
    return clans.get(clan_id, {}).get("disciplines", [])


def _apply_base_creation(
    rng: SeededRng,
    char: dict[str, Any],
    profile: Any,
    creation: dict[str, Any],
    log: list[LogEntry],
    caps: dict[str, int],
) -> None:
    attrs_data = load_json_cached(DATA, "attributes.json")
    skills_data = load_json_cached(DATA, "skills.json")

    all_attrs = attrs_data["all"]
    all_skills = skills_data["all"]

    char["humanity"] = creation.get("humanity", 7)

    bg_dots = creation.get("backgrounds", 0)
    bgs = load_json_cached(DATA, "advantages.json")["backgrounds"] if bg_dots else []
    bg_pool = {"1": bg_dots} if bg_dots else {}

    dot_categories: list[tuple[str, dict[str, int], list[str], dict[str, float], dict[str, int], int]] = [
        (
            "Attribute",
            creation["attributes"],
            all_attrs,
            profile.attribute_biases,
            char["attributes"],
            caps["attribute"],
        ),
        (
            "Skill",
            creation["skills"],
            all_skills,
            profile.skill_biases,
            char["skills"],
            caps["skill"],
        ),
    ]
    if bg_dots:
        dot_categories.append(
            (
                "Background",
                bg_pool,
                bgs,
                {"contacts": 1.2, "resources": 1.0},
                char["backgrounds"],
                caps["background"],
            )
        )

    disc_spec = creation.get("disciplines", {})
    discipline_slots_by_rating: dict[int, list[str]] = {}
    for slot_key in ("primary", "secondary", "tertiary"):
        dots = disc_spec.get(slot_key, 0)
        if dots > 0:
            discipline_slots_by_rating.setdefault(dots, []).append(slot_key)

    ratings: set[int] = set()
    for _label, pool, _items, _biases, _target, _cap in dot_categories:
        ratings.update(int(k) for k in pool)
    ratings.update(discipline_slots_by_rating)

    clan_pool = _clan_disciplines(char.get("clan") or char.get("domitor_clan"))

    for rating in sorted(ratings, reverse=True):
        for label, pool, items, biases, target, max_rating in dot_categories:
            count = _pool_count(pool, rating)
            if count > 0:
                _assign_dots_at_rating(
                    rng,
                    rating,
                    count,
                    items,
                    biases,
                    target,
                    log,
                    "base",
                    label,
                    max_rating=max_rating,
                )

        for slot_key in discipline_slots_by_rating.get(rating, []):
            if clan_pool:
                _assign_one_discipline_pick(
                    rng,
                    char,
                    clan_pool,
                    profile,
                    disc_spec[slot_key],
                    slot_key,
                    log,
                    max_rating=caps["discipline"],
                )

    char["blood_potency"] = creation.get("blood_potency", char.get("blood_potency", 1))


def _enumerate_purchases(
    char: dict[str, Any],
    profile: Any,
    costs: dict[str, Any],
    ctype: str,
    source: str,
    caps: dict[str, int],
) -> list[PurchaseCandidate]:
    candidates: list[PurchaseCandidate] = []
    clan_pool = set(_clan_disciplines(char.get("clan") or char.get("domitor_clan")))

    def add_attr(attr: str, cat_weight: float, spend_group: str) -> None:
        cur = char["attributes"].get(attr, 0)
        if cur >= caps["attribute"]:
            return
        new_level = cur + 1
        cost = lookup_cost(costs, "attribute", new_level=new_level)

        def apply() -> None:
            char["attributes"][attr] = new_level

        candidates.append(
            PurchaseCandidate(
                item_id=attr,
                category="attribute",
                spend_group=spend_group,
                cost=cost,
                weight=cat_weight,
                item_bias=profile.attribute_biases.get(attr, 1.0),
                clan_factor=1.0,
                source=source,
                apply=apply,
            )
        )

    attrs = load_json_cached(DATA, "attributes.json")
    for group, wkey in [("physical", "physical_attrs"), ("social", "social_attrs"), ("mental", "mental_attrs")]:
        cw = profile.weights.get(wkey, 1.0)
        for attr in attrs[group]:
            add_attr(attr, cw, wkey)

    skills_data = load_json_cached(DATA, "skills.json")
    sw = profile.weights.get("skills", 1.0)
    for skill in skills_data["all"]:
        cur = char["skills"].get(skill, 0)
        if cur >= caps["skill"]:
            continue
        new_level = cur + 1
        cost = lookup_cost(costs, "skill", new_level=new_level)

        def apply_skill(s=skill, nl=new_level) -> None:
            char["skills"][s] = nl

        candidates.append(
            PurchaseCandidate(
                item_id=skill,
                category="skill",
                spend_group="skills",
                cost=cost,
                weight=sw,
                item_bias=profile.skill_biases.get(skill, 1.0),
                clan_factor=1.0,
                source=source,
                apply=apply_skill,
            )
        )

    dw = profile.weights.get("in_clan_disciplines", 1.0)
    for disc in set(char["disciplines"]) | clan_pool:
        cur = char["disciplines"].get(disc, 0)
        if cur >= caps["discipline"]:
            continue
        new_level = cur + 1
        in_clan = disc in clan_pool
        if ctype == "ghoul" and not in_clan:
            continue
        cost_key = "discipline_in_clan" if in_clan else "discipline_out_of_clan"
        if ctype == "thin_blood" and not in_clan:
            continue
        cost = lookup_cost(costs, cost_key, new_level=new_level)
        clan_factor = 1.0 if in_clan else 0.3

        def apply_disc(d=disc, nl=new_level) -> None:
            char["disciplines"][d] = nl

        candidates.append(
            PurchaseCandidate(
                item_id=disc,
                category="discipline",
                spend_group="in_clan_disciplines",
                cost=cost,
                weight=dw,
                item_bias=profile.discipline_biases.get(disc, 1.0),
                clan_factor=clan_factor,
                source=source,
                apply=apply_disc,
            )
        )

    bw = profile.weights.get("backgrounds", 1.0)
    for bg in load_json_cached(DATA, "advantages.json")["backgrounds"]:
        cur = char["backgrounds"].get(bg, 0)
        if cur >= caps["background"]:
            continue
        new_level = cur + 1
        cost = lookup_cost(costs, "background", new_level=new_level)

        def apply_bg(b=bg, nl=new_level) -> None:
            char["backgrounds"][b] = nl

        candidates.append(
            PurchaseCandidate(
                item_id=bg,
                category="background",
                spend_group="backgrounds",
                cost=cost,
                weight=bw,
                item_bias=1.0,
                clan_factor=1.0,
                source=source,
                apply=apply_bg,
            )
        )

    mw = profile.weights.get("merits", 1.0)
    for merit in load_json_cached(DATA, "advantages.json")["merits"]:
        cur = char["merits"].get(merit, 0)
        if cur >= caps["merit"]:
            continue
        new_level = cur + 1
        cost = lookup_cost(costs, "merit", new_level=new_level)

        def apply_merit(m=merit, nl=new_level) -> None:
            char["merits"][m] = nl

        candidates.append(
            PurchaseCandidate(
                item_id=merit,
                category="merit",
                spend_group="merits",
                cost=cost,
                weight=mw,
                item_bias=1.0,
                clan_factor=1.0,
                source=source,
                apply=apply_merit,
            )
        )

    if ctype == "ghoul":
        for power in load_json_cached(DATA, "ghoul_powers.json")["powers"]:
            pid = power["id"]
            if char["ghoul_powers"].get(pid, 0) >= caps["ghoul_power"]:
                continue
            cost = lookup_cost(costs, "ghoul_power")

            def apply_power(p=pid) -> None:
                char["ghoul_powers"][p] = 1

            candidates.append(
                PurchaseCandidate(
                    item_id=pid,
                    category="ghoul_power",
                    spend_group="ghoul_powers",
                    cost=cost,
                    weight=profile.weights.get("in_clan_disciplines", 1.0),
                    item_bias=profile.discipline_biases.get(pid, 1.0),
                    clan_factor=1.0,
                    source=source,
                    apply=apply_power,
                )
            )

    if ctype == "thin_blood":
        fw = profile.weights.get("thin_blood_formulas", 1.5)
        for formula in load_json_cached(DATA, "thin_blood_formulas.json")["formulas"]:
            fid = formula["id"]
            cur = char["thin_blood_formulas"].get(fid, 0)
            if cur >= caps["thin_blood_formula"]:
                continue
            new_level = cur + 1
            cost = lookup_cost(costs, "thin_blood_formula", new_level=new_level)

            def apply_formula(f=fid, nl=new_level) -> None:
                char["thin_blood_formulas"][f] = nl

            candidates.append(
                PurchaseCandidate(
                    item_id=fid,
                    category="thin_blood_formula",
                    spend_group="thin_blood_formulas",
                    cost=cost,
                    weight=fw,
                    item_bias=1.2,
                    clan_factor=1.0,
                    source=source,
                    apply=apply_formula,
                )
            )

    if ctype in ("vampire", "thin_blood"):
        for ls in ("loresheet_a", "loresheet_b"):
            cur = char["loresheets"].get(ls, 0)
            if cur >= caps["loresheet"]:
                continue
            new_level = cur + 1
            cost = lookup_cost(costs, "loresheet", new_level=new_level)

            def apply_ls(l=ls, nl=new_level) -> None:
                char["loresheets"][l] = nl

            candidates.append(
                PurchaseCandidate(
                    item_id=ls,
                    category="loresheet",
                    spend_group="loresheets",
                    cost=cost,
                    weight=profile.weights.get("merits", 0.5),
                    item_bias=1.0,
                    clan_factor=1.0,
                    source=source,
                    apply=apply_ls,
                )
            )

    if ctype == "vampire" and char.get("blood_potency", 0) < caps["blood_potency"]:
        cur = char["blood_potency"]
        new_level = cur + 1
        cost = lookup_cost(costs, "blood_potency", new_level=new_level)

        def apply_bp() -> None:
            char["blood_potency"] = new_level

        candidates.append(
            PurchaseCandidate(
                item_id="blood_potency",
                category="blood_potency",
                spend_group="blood_potency",
                cost=cost,
                weight=0.4,
                item_bias=1.0,
                clan_factor=1.0,
                source=source,
                apply=apply_bp,
            )
        )

    return candidates


def generate_character(
    seed: int,
    options: dict[str, Any],
    venue_config: dict[str, Any],
) -> GenerationResult:
    ctype = options.get("type", "vampire")
    arch = options.get("arch", "diplomat")
    sub = options.get("sub", "silver_tongue")
    venue_id = venue_config.get("id", "mes_end_to_dawn")

    types_meta = load_json_cached(DATA, "character_types.json")
    if ctype not in types_meta:
        raise ValueError(f"Unknown character type: {ctype}")

    meta = types_meta[ctype]
    creation = load_json_cached(DATA, meta["creation_ref"])
    costs = load_json_cached(DATA, "costs.json")
    caps = _resolve_caps(creation)

    profile = effective_profile(
        arch,
        sub,
        ctype,
        venue_config.get("archetype_overrides"),
    )
    source = f"{arch}/{sub}"

    rng = SeededRng(seed)
    char = _empty_character(options)
    log: list[LogEntry] = []

    if ctype == "vampire":
        char["clan"] = options.get("clan", "brujah")
    elif ctype == "ghoul":
        char["domitor_clan"] = options.get("domitor_clan", "tremere")
        char["blood_potency"] = 0
    elif ctype == "thin_blood":
        char["blood_potency"] = 0

    if meta.get("bp_fixed") is not None:
        char["blood_potency"] = meta["bp_fixed"]

    _apply_base_creation(rng, char, profile, creation, log, caps)

    if meta.get("predator"):
        _pick_predator(rng, char, log)

    xp_budget, xp_lines = resolve_xp_budget(venue_id, options)
    for line in xp_lines:
        log.append(LogEntry(phase="xp_budget", message=line, detail={}))

    spent_before = xp_budget

    def enumerate() -> list[PurchaseCandidate]:
        return _enumerate_purchases(char, profile, costs, ctype, source, caps)

    remaining, xp_log, spend_logs = spend_xp(rng, xp_budget, enumerate, source=source)
    log.extend(spend_logs)
    xp_spent = spent_before - remaining

    return GenerationResult(
        engine_version=ENGINE_VERSION,
        schema="0.1",
        game_id="lotn_v5",
        venue_id=venue_id,
        seed=seed,
        options=dict(options),
        character=char,
        creation_log=log,
        xp_log=xp_log,
        xp_budget=xp_budget,
        xp_spent=xp_spent,
        xp_remaining=remaining,
    )
