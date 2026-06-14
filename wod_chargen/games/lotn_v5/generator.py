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
from wod_chargen.games.lotn_v5.base_creation import apply_base_creation
from wod_chargen.games.lotn_v5.clan_discipline_adapt import adapt_profile_for_clan
from wod_chargen.games.lotn_v5.predators import (
    apply_predator_biases,
    apply_predator_package,
    predator_background_biases,
    resolve_predator,
)
from wod_chargen.games.lotn_v5.backgrounds import (
    can_add_dot,
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
    caitiff_owned_disciplines,
    discipline_pool_for_char,
    enumerate_ceremony_candidates,
    enumerate_ghoul_power_candidates,
    initialize_ghoul_domitor_disciplines,
    record_ghoul_power,
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
from wod_chargen.games.lotn_v5.paths import DATA_PKG as DATA
from wod_chargen.games.lotn_v5.thin_blood_merits import (
    assign_resonance_discipline,
    has_discipline_affinity,
    has_thin_blood_alchemist,
    run_thin_blood_merit_flaw_creation,
    validate_thin_blood_merit_flaw_pairs,
)
from wod_chargen.games.lotn_v5.xp_purchases import enumerate_purchases
from wod_chargen.venues import resolve_xp_budget

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
        "thin_blood_merits": {},
        "thin_blood_flaws": {},
    }


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
        picked = initialize_ghoul_domitor_disciplines(rng, char)
        if picked:
            log.append(
                LogEntry(
                    phase="base",
                    message=f"Domitor disciplines (Caitiff): {', '.join(picked)}",
                    detail={"domitor_disciplines": picked},
                )
            )
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
    apply_base_creation(rng, char, profile, creation, log, caps, background_biases=bg_biases)

    if predator_data:
        for line in apply_predator_package(predator_data, char, rng, profile, caps=caps):
            log.append(LogEntry(phase="predator", message=line, detail={"predator": predator_data["id"]}))

    mf_lines, mf_ledger = run_merit_flaw_creation(rng, char, profile, ctype)
    char["merit_flaw_meta"] = mf_ledger.to_meta()
    for line in mf_lines:
        log.append(LogEntry(phase="merits", message=line, detail={}))

    run_thin_blood_merit_flaw_creation(rng, char, profile, log, caps=caps)

    if ctype == "thin_blood":
        assign_resonance_discipline(rng, char, profile, log)

    xp_budget, xp_lines = resolve_xp_budget(venue_id, options)
    for line in xp_lines:
        log.append(LogEntry(phase="xp_budget", message=line, detail={}))

    xp_log: list = []
    xp_budget, mandatory_xp, mandatory_logs = apply_mandatory_blood_potency(
        char, costs, xp_budget
    )
    xp_log.extend(mandatory_xp)
    log.extend(mandatory_logs)

    xp_budget_total = xp_budget
    spent_before = xp_budget
    discipline_logs: list[LogEntry] = []

    def enumerate() -> list[PurchaseCandidate]:
        return enumerate_purchases(
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

    remaining, spend_xp_log, spend_logs = spend_xp(
        rng, xp_budget, enumerate, source=source
    )
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

    for err in validate_thin_blood_merit_flaw_pairs(char):
        log.append(LogEntry(phase="validation", message=f"Thin-Blood: {err}", detail={}))

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
        xp_budget=xp_budget_total,
        xp_spent=xp_spent,
        xp_remaining=remaining,
    )
