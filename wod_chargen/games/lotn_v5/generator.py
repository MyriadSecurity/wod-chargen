"""Main LoTN V5 procedural generation pipeline."""

from __future__ import annotations

from typing import Any

from wod_chargen.core.costs import lookup_cost
from wod_chargen.core.data_loader import load_json_cached
from wod_chargen.core.models import GenerationResult, LogEntry, XpLogEntry
from wod_chargen.core.rng import SeededRng
from wod_chargen.core.share import ENGINE_VERSION
from wod_chargen.core.spender import PurchaseCandidate, spend_xp
from wod_chargen.core.xp_strategy import creation_pick_weight
from wod_chargen.games.lotn_v5.archetypes import effective_profile
from wod_chargen.games.lotn_v5.clan_discipline_adapt import (
    adapt_profile_for_clan,
    off_clan_signature_factor,
    resolve_discipline_bias,
)
from wod_chargen.games.lotn_v5.predators import (
    apply_predator_biases,
    apply_predator_package,
    predator_background_biases,
    resolve_predator,
)
from wod_chargen.games.lotn_v5.backgrounds import (
    _can_add_dot,
    apply_background_purchase,
    apply_modifier_purchase,
    apply_xp_background_disadv_trade,
    background_defs,
    empty_backgrounds,
    enumerate_xp_background_types,
    enumerate_xp_modifier_purchases,
    entries_for_type,
    modifier_item_key,
    modifier_xp_item_bias,
    record_xp_modifier_purchase,
    run_background_creation,
    validate_full_modifier_accounting,
)
from wod_chargen.games.lotn_v5.disciplines import (
    assign_power_at_level,
    assign_powers_for_discipline,
    discipline_pool_for_char,
    enumerate_ceremony_candidates,
    enumerate_ritual_candidates,
    owned_power_ids,
    record_formula_selection,
    record_ceremony,
    record_ritual,
    validate_discipline_selections,
)
from wod_chargen.games.lotn_v5.generation import (
    apply_mandatory_blood_potency,
    assign_generation_and_blood_potency,
    blood_potency_cap,
    generation_row,
)
from wod_chargen.games.lotn_v5.merits_flaws import (
    enumerate_xp_merit_purchases,
    run_merit_flaw_creation,
)
from wod_chargen.games.lotn_v5.loresheets import (
    apply_loresheet_benefits,
    enumerate_loresheet_purchases,
    resolve_loresheet_bias,
)
from wod_chargen.venues import resolve_xp_budget

DATA = "wod_chargen.games.lotn_v5.data"
DEFAULT_CAP = 5


def _resolve_caps(creation: dict[str, Any], char: dict[str, Any] | None = None) -> dict[str, int]:
    """Per-category rating ceilings (LoTN V5 defaults + creation/generation overrides)."""
    bp_cap = 3
    if char is not None:
        meta = char.get("generation_meta") or {}
        if meta.get("max_blood_potency") is not None:
            bp_cap = int(meta["max_blood_potency"])
        elif char.get("generation") is not None:
            row = generation_row(int(char["generation"]))
            if row is not None:
                bp_cap = blood_potency_cap(row)

    return {
        "attribute": DEFAULT_CAP,
        "skill": DEFAULT_CAP,
        "background": 3,
        "discipline": int(creation.get("discipline_max", DEFAULT_CAP)),
        "loresheet": 3,
        "blood_potency": bp_cap,
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
        "discipline_powers": {},
        "rituals": [],
        "ceremonies": [],
        "formula_powers": {},
        "discipline_meta": {},
        "backgrounds": empty_backgrounds(),
        "background_meta": {},
        "merit_flaw_meta": {},
        "merits": {},
        "flaws": {},
        "specialties": [],
        "predator_meta": {},
        "loresheets": {},
        "ghoul_powers": {},
        "thin_blood_formulas": {},
    }


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

    weights = [creation_pick_weight(biases.get(i, 1.0), 0, max_rating, dots) for i in eligible]
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
    pool = frozenset(clan_pool)
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

    weights = [
        creation_pick_weight(resolve_discipline_bias(profile, d, pool), 0, max_rating, dots)
        for d in eligible
    ]
    disc = rng.weighted_choice(eligible, weights)
    char["disciplines"][disc] = dots
    log.append(
        LogEntry(
            phase="base",
            message=f"Discipline {disc} +{dots} → {dots}",
            detail={"discipline": disc, "slot": slot_key, "pool_rating": dots, "rating": dots, "previous": 0},
        )
    )
    assign_powers_for_discipline(rng, char, disc, dots, profile, log, phase="base")
    return disc


def _apply_predator(
    options: dict[str, Any],
    rng: SeededRng,
    char: dict[str, Any],
    log: list[LogEntry],
) -> dict[str, Any]:
    pick = resolve_predator(options, rng)
    char["predator"] = pick["id"]
    log.append(LogEntry(phase="base", message=f"Predator type: {pick['label']}", detail={"id": pick["id"]}))
    return pick


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
    *,
    background_biases: dict[str, float] | None = None,
) -> None:
    attrs_data = load_json_cached(DATA, "attributes.json")
    skills_data = load_json_cached(DATA, "skills.json")

    all_attrs = attrs_data["all"]
    all_skills = skills_data["all"]

    char["humanity"] = creation.get("humanity", 7)

    bg_dots = int(creation.get("backgrounds", 0))

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
    disc_spec = creation.get("disciplines", {})
    discipline_slots_by_rating: dict[int, list[str]] = {}
    for slot_key in ("primary", "secondary", "tertiary"):
        dots = disc_spec.get(slot_key, 0)
        if dots > 0:
            discipline_slots_by_rating.setdefault(dots, []).append(slot_key)

    clan_pool = discipline_pool_for_char(char, char.get("character_type", "vampire"))

    for label, pool, items, biases, target, max_rating in dot_categories:
        for rating in sorted({int(k) for k in pool}, reverse=True):
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

    for rating in sorted(discipline_slots_by_rating.keys(), reverse=True):
        for slot_key in discipline_slots_by_rating[rating]:
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

    if bg_dots:
        bg_bias = {"contacts": 1.2, "resources": 1.0}
        for bg_type, mult in getattr(profile, "background_biases", {}).items():
            bg_bias[bg_type] = bg_bias.get(bg_type, 1.0) * mult
        if background_biases:
            bg_bias.update(background_biases)
        bg_lines, ledger = run_background_creation(
            rng,
            char["backgrounds"],
            bg_dots,
            profile,
            biases=bg_bias,
            char=char,
        )
        char["background_meta"] = ledger.to_meta()
        for line in bg_lines:
            log.append(LogEntry(phase="base", message=line, detail={}))


def _enumerate_purchases(
    char: dict[str, Any],
    profile: Any,
    costs: dict[str, Any],
    ctype: str,
    source: str,
    caps: dict[str, int],
    rng: SeededRng,
    *,
    predator_bg_biases: dict[str, float] | None = None,
    discipline_logs: list[LogEntry] | None = None,
) -> list[PurchaseCandidate]:
    candidates: list[PurchaseCandidate] = []
    dlogs = discipline_logs if discipline_logs is not None else []
    clan_pool = set(discipline_pool_for_char(char, ctype))

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
                new_level=new_level,
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
                new_level=new_level,
                cost=cost,
                weight=sw,
                item_bias=profile.skill_biases.get(skill, 1.0),
                clan_factor=1.0,
                source=source,
                apply=apply_skill,
            )
        )

    dw = profile.weights.get("in_clan_disciplines", 1.0)
    for disc in sorted(set(char["disciplines"]) | clan_pool):
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
        clan_factor = 1.0 if in_clan else off_clan_signature_factor(profile, disc, clan_pool)

        def apply_disc(d=disc, nl=new_level) -> None:
            char["disciplines"][d] = nl
            assign_power_at_level(
                rng, char, d, nl, profile, dlogs, phase="xp", source=source
            )

        candidates.append(
            PurchaseCandidate(
                item_id=disc,
                category="discipline",
                spend_group="in_clan_disciplines",
                new_level=new_level,
                cost=cost,
                weight=dw,
                item_bias=resolve_discipline_bias(profile, disc, clan_pool),
                clan_factor=clan_factor,
                source=source,
                apply=apply_disc,
            )
        )

    bw = profile.weights.get("backgrounds", 1.0)
    conn_w = bw * 0.55
    mod_w = bw * 0.3

    def _connection_item_bias(bg_type: str, entry: dict[str, Any] | None) -> float:
        spec = background_defs()[bg_type]
        bias = float(spec.get("creation_bias", 1.0))
        if predator_bg_biases:
            bias *= predator_bg_biases.get(bg_type, 1.0)
        if entry and entry.get("from_predator"):
            bias *= 1.5
        return bias

    for bg_type in enumerate_xp_background_types(char, caps["background"]):
        spec = background_defs()[bg_type]
        max_dots = min(int(spec.get("max_dots", 3)), caps["background"])
        typed = entries_for_type(char["backgrounds"], bg_type)

        def add_candidate(entry: dict[str, Any] | None, *, create_new: bool) -> None:
            if create_new:
                cur = 0
                entry_ref: dict[str, Any] | None = None
            else:
                assert entry is not None
                cur = entry["dots"]
                entry_ref = entry
            new_level = cur + 1
            if new_level > max_dots:
                return
            cost = lookup_cost(costs, "background", new_level=new_level)

            def apply_bg(
                t=bg_type,
                e=entry_ref,
                create=create_new,
            ) -> None:
                if create:
                    apply_background_purchase(
                        char["backgrounds"], t, rng, profile, mark_xp=True
                    )
                else:
                    assert e is not None
                    e["dots"] += 1
                    e["xp_purchased"] = True

            item_key = (
                f"{bg_type}/{entry_ref['name']}"
                if entry_ref
                else f"{bg_type}/new"
            )
            candidates.append(
                PurchaseCandidate(
                    item_id=item_key,
                    category="background",
                    spend_group="background_connections",
                    new_level=new_level,
                    cost=cost,
                    weight=conn_w,
                    item_bias=_connection_item_bias(bg_type, entry_ref),
                    clan_factor=1.0,
                    source=source,
                    apply=apply_bg,
                )
            )

        if spec.get("purchase_mode") == "single_rating":
            entry = typed[0] if typed else None
            if entry is None or entry["dots"] < max_dots:
                add_candidate(entry, create_new=entry is None)
        else:
            for entry in typed:
                if entry["dots"] < max_dots:
                    add_candidate(entry, create_new=False)
            if _can_add_dot(char["backgrounds"], bg_type, spec, char):
                add_candidate(None, create_new=True)

    for entry, mod_def, kind, new_level in enumerate_xp_modifier_purchases(
        char, kinds=("advantage",), only_xp_purchased=True
    ):
        mod_id = mod_def["id"]
        cost = lookup_cost(costs, "background", new_level=new_level)

        def apply_mod(
            e=entry,
            mid=mod_id,
        ) -> None:
            apply_modifier_purchase(e, mid, "advantage")
            record_xp_modifier_purchase(char.setdefault("background_meta", {}))

        from wod_chargen.games.lotn_v5.trait_biases import resolve_trait_bias

        candidates.append(
            PurchaseCandidate(
                item_id=modifier_item_key(entry, mod_id, kind),
                category="background_modifier",
                spend_group="background_modifiers",
                new_level=new_level,
                cost=cost,
                weight=mod_w,
                item_bias=modifier_xp_item_bias(entry, kind)
                * resolve_trait_bias(profile, mod_id, "modifiers"),
                clan_factor=1.0,
                source=source,
                apply=apply_mod,
            )
        )

    candidates.extend(
        enumerate_xp_merit_purchases(char, profile, costs, ctype, source)
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
                    new_level=1,
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
        tba = char["disciplines"].get("thin_blood_alchemy", 0)
        for formula in load_json_cached(DATA, "thin_blood_formulas.json")["formulas"]:
            fid = formula["id"]
            if char["thin_blood_formulas"].get(fid, 0) >= 1:
                continue
            if fid in owned_power_ids(char):
                continue
            req_level = int(formula.get("level", 1))
            if tba < req_level:
                continue
            new_level = 1
            cost = lookup_cost(costs, "thin_blood_formula", new_level=new_level)

            def apply_formula(f=fid) -> None:
                record_formula_selection(char, f)

            candidates.append(
                PurchaseCandidate(
                    item_id=fid,
                    category="thin_blood_formula",
                    spend_group="thin_blood_formulas",
                    new_level=new_level,
                    cost=cost,
                    weight=fw,
                    item_bias=1.0,
                    clan_factor=1.0,
                    source=source,
                    apply=apply_formula,
                )
            )

    rw = profile.weights.get("in_clan_disciplines", 0.5)
    for power in enumerate_ritual_candidates(char):
        pid = power["id"]
        level = int(power["level"])
        cost = lookup_cost(costs, "ritual", new_level=level)

        def apply_ritual(p=pid) -> None:
            record_ritual(char, p, dlogs, phase="xp", source=source)

        candidates.append(
            PurchaseCandidate(
                item_id=pid,
                category="ritual",
                spend_group="in_clan_disciplines",
                new_level=level,
                cost=cost,
                weight=rw,
                item_bias=1.0,
                clan_factor=1.0,
                source=source,
                apply=apply_ritual,
            )
        )

    for power in enumerate_ceremony_candidates(char):
        pid = power["id"]
        level = int(power["level"])
        cost = lookup_cost(costs, "ceremony", new_level=level)

        def apply_ceremony(p=pid) -> None:
            record_ceremony(char, p, dlogs, phase="xp", source=source)

        candidates.append(
            PurchaseCandidate(
                item_id=pid,
                category="ceremony",
                spend_group="in_clan_disciplines",
                new_level=level,
                cost=cost,
                weight=rw,
                item_bias=1.0,
                clan_factor=1.0,
                source=source,
                apply=apply_ceremony,
            )
        )

    if ctype in ("vampire", "thin_blood"):
        sect = char.get("sect")
        ls_w = profile.weights.get(
            "loresheets",
            max(profile.weights.get("merits", 0.5) * 2.0, 1.4),
        )
        for ls_id, new_level in enumerate_loresheet_purchases(char, profile, sect=sect):
            cost = lookup_cost(costs, "loresheet", new_level=new_level)

            def apply_ls(l=ls_id, nl=new_level) -> None:
                char["loresheets"][l] = nl

            candidates.append(
                PurchaseCandidate(
                    item_id=ls_id,
                    category="loresheet",
                    spend_group="loresheets",
                    new_level=new_level,
                    cost=cost,
                    weight=ls_w,
                    item_bias=resolve_loresheet_bias(ls_id, profile, char, sect=sect),
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
                new_level=new_level,
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
    elif ctype == "thin_blood":
        pass

    clan_id = char.get("clan") or char.get("domitor_clan")
    profile = adapt_profile_for_clan(profile, clan_id)

    assign_generation_and_blood_potency(rng, char, ctype, venue_config, creation, options, log)
    caps = _resolve_caps(creation, char)

    if meta.get("bp_fixed") is not None:
        char["blood_potency"] = meta["bp_fixed"]

    predator_data: dict[str, Any] | None = None
    if meta.get("predator"):
        predator_data = _apply_predator(options, rng, char, log)
        profile = apply_predator_biases(profile, predator_data)

    bg_biases = predator_background_biases(predator_data) if predator_data else None
    _apply_base_creation(rng, char, profile, creation, log, caps, background_biases=bg_biases)

    if predator_data:
        for line in apply_predator_package(predator_data, char, rng, profile, caps=caps):
            log.append(LogEntry(phase="predator", message=line, detail={"predator": predator_data["id"]}))

    mf_lines, mf_ledger = run_merit_flaw_creation(rng, char, profile, ctype)
    char["merit_flaw_meta"] = mf_ledger.to_meta()
    for line in mf_lines:
        log.append(LogEntry(phase="merits", message=line, detail={}))

    xp_budget, xp_lines = resolve_xp_budget(venue_id, options)
    for line in xp_lines:
        log.append(LogEntry(phase="xp_budget", message=line, detail={}))

    xp_log: list = []
    xp_budget, mandatory_xp, mandatory_logs = apply_mandatory_blood_potency(
        char, costs, xp_budget
    )
    xp_log.extend(mandatory_xp)
    log.extend(mandatory_logs)

    spent_before = xp_budget
    discipline_logs: list[LogEntry] = []

    def enumerate() -> list[PurchaseCandidate]:
        return _enumerate_purchases(
            char,
            profile,
            costs,
            ctype,
            source,
            caps,
            rng,
            predator_bg_biases=bg_biases,
            discipline_logs=discipline_logs,
        )

    remaining, spend_xp_log, spend_logs = spend_xp(rng, xp_budget, enumerate, source=source)
    xp_log.extend(spend_xp_log)
    log.extend(spend_logs)
    log.extend(discipline_logs)
    xp_spent = spent_before - remaining

    for line in apply_loresheet_benefits(char, rng, profile, caps=caps):
        log.append(LogEntry(phase="loresheet", message=line, detail={}))

    bg_meta = char.setdefault("background_meta", {})
    for item_id, category, new_level, trade_source in apply_xp_background_disadv_trade(
        rng, char["backgrounds"], bg_meta, profile
    ):
        xp_log.append(
            XpLogEntry(
                item=item_id,
                category=category,
                spend_group="background_disadvantages"
                if category == "background_disadvantage"
                else "background_modifiers",
                new_level=new_level,
                cost=0,
                group_weight=0.0,
                item_bias=0.0,
                clan_factor=1.0,
                efficiency_bias=0.0,
                roll=0.0,
                score=0.0,
                source=trade_source,
            )
        )

    if char.get("background_meta"):
        validate_full_modifier_accounting(char["backgrounds"], char["background_meta"])

    selection_errors = validate_discipline_selections(char)
    if selection_errors:
        for err in selection_errors:
            log.append(LogEntry(phase="validation", message=f"Discipline: {err}", detail={}))

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
