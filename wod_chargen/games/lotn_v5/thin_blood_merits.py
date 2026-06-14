"""Thin-blood merit/flaw pairs — separate from standard merits and flaws."""

from __future__ import annotations

from typing import Any, Literal

from wod_chargen.core.data_loader import load_json_cached
from wod_chargen.core.models import LogEntry, XpLogEntry
from wod_chargen.core.rng import SeededRng
from wod_chargen.games.lotn_v5.disciplines import (
    assign_power_at_level,
    assign_powers_for_discipline,
    caitiff_discipline_pool,
    owned_power_ids,
    record_formula_selection,
)
from wod_chargen.games.lotn_v5.merits_flaws import (
    load_catalog,
    trait_def,
    trait_eligible,
    trait_increment,
    trait_rules,
)

DATA = "wod_chargen.games.lotn_v5.data"

TraitKind = Literal["merit", "flaw"]

_EFFECT_MERITS = frozenset({"thin_blood_alchemist", "discipline_affinity"})
_MAX_PAIRS = 3


def thin_blood_pair_count(char: dict[str, Any]) -> int:
    return len(char.get("thin_blood_merits", {}))


def validate_thin_blood_merit_flaw_pairs(char: dict[str, Any]) -> list[str]:
    if char.get("character_type") != "thin_blood":
        return []
    merits = thin_blood_pair_count(char)
    flaws = len(char.get("thin_blood_flaws", {}))
    errors: list[str] = []
    if merits != flaws:
        errors.append(f"thin-blood merit/flaw count mismatch ({merits} merits, {flaws} flaws)")
    if merits > _MAX_PAIRS:
        errors.append(f"thin-blood pairs exceed cap ({merits} > {_MAX_PAIRS})")
    return errors


def thin_blood_traits_for_type(kind: TraitKind) -> list[dict[str, Any]]:
    key = "merits" if kind == "merit" else "flaws"
    return [e for e in load_catalog()[key] if e.get("thin_blood_only")]


def has_thin_blood_alchemist(char: dict[str, Any]) -> bool:
    return int(char.get("thin_blood_merits", {}).get("thin_blood_alchemist", 0)) > 0


def has_discipline_affinity(char: dict[str, Any]) -> bool:
    return int(char.get("thin_blood_merits", {}).get("discipline_affinity", 0)) > 0


def has_merit_driven_disciplines(char: dict[str, Any]) -> bool:
    return has_thin_blood_alchemist(char) or has_discipline_affinity(char)


def _tb_bucket(char: dict[str, Any], kind: TraitKind) -> dict[str, int]:
    key = "thin_blood_merits" if kind == "merit" else "thin_blood_flaws"
    return char.setdefault(key, {})


def _tb_trait_eligible(
    entry: dict[str, Any],
    kind: TraitKind,
    char: dict[str, Any],
    *,
    phase: str,
) -> bool:
    bucket = _tb_bucket(char, kind)
    current = int(bucket.get(entry["id"], 0))
    if trait_increment(entry, current, char, kind=kind) is None:
        return False
    return trait_eligible(entry, kind, char, phase=phase)  # type: ignore[arg-type]


def _eligible_tb_merits(char: dict[str, Any], *, phase: str) -> list[dict[str, Any]]:
    return [
        entry
        for entry in thin_blood_traits_for_type("merit")
        if _tb_trait_eligible(entry, "merit", char, phase=phase)
    ]


def _pair_compatible(merit_entry: dict[str, Any], flaw_entry: dict[str, Any]) -> bool:
    if flaw_entry["id"] in trait_rules(merit_entry).get("forbidden_with", []):
        return False
    if merit_entry["id"] in trait_rules(flaw_entry).get("forbidden_with", []):
        return False
    return True


def _eligible_tb_flaws_for_merit(
    char: dict[str, Any],
    merit_entry: dict[str, Any],
    *,
    phase: str,
) -> list[dict[str, Any]]:
    simulated = dict(char)
    simulated["thin_blood_merits"] = {
        **char.get("thin_blood_merits", {}),
        merit_entry["id"]: 1,
    }
    out: list[dict[str, Any]] = []
    for entry in thin_blood_traits_for_type("flaw"):
        if not _tb_trait_eligible(entry, "flaw", char, phase=phase):
            continue
        if not _pair_compatible(merit_entry, entry):
            continue
        if not trait_eligible(entry, "flaw", simulated, phase=phase):  # type: ignore[arg-type]
            continue
        out.append(entry)
    return out


def _pick_free_formula(rng: SeededRng, char: dict[str, Any], profile: Any) -> str | None:
    tba = int(char.get("disciplines", {}).get("thin_blood_alchemy", 0))
    formulas = load_json_cached(DATA, "thin_blood_formulas.json")["formulas"]
    owned = owned_power_ids(char)
    eligible = [
        f
        for f in formulas
        if f["id"] not in owned
        and char.get("thin_blood_formulas", {}).get(f["id"], 0) < 1
        and tba >= int(f.get("level", 1))
    ]
    if not eligible:
        return None
    from wod_chargen.games.lotn_v5.trait_biases import resolve_trait_bias

    weights = [
        max(
            float(profile.weights.get("thin_blood_formulas", 1.5))
            * resolve_trait_bias(profile, f["id"], "merits"),
            0.01,
        )
        for f in eligible
    ]
    pick = rng.weighted_choice(eligible, weights)
    return pick["id"]


def _pick_affinity_discipline(rng: SeededRng, char: dict[str, Any], profile: Any) -> str:
    pool = caitiff_discipline_pool()
    from wod_chargen.games.lotn_v5.clan_discipline_adapt import resolve_discipline_bias

    clan_pool = frozenset(pool)
    weights = [max(resolve_discipline_bias(profile, disc_id, clan_pool), 0.01) for disc_id in pool]
    return rng.weighted_choice(pool, weights)


def assign_resonance_discipline(
    rng: SeededRng,
    char: dict[str, Any],
    profile: Any,
    log: list[LogEntry],
) -> None:
    """Grant every thin-blood a random first dot outside their in-clan pool."""
    from wod_chargen.games.lotn_v5.clan_discipline_adapt import char_clan_pool, resolve_discipline_bias

    in_clan = char_clan_pool(char)
    owned = {disc_id for disc_id, rating in char.get("disciplines", {}).items() if int(rating) > 0}
    pool = [
        disc_id
        for disc_id in caitiff_discipline_pool()
        if disc_id not in in_clan and disc_id not in owned
    ]
    if not pool:
        log.append(
            LogEntry(
                phase="base",
                message="Resonance Discipline unplaced (no eligible disciplines)",
                detail={"in_clan": sorted(in_clan), "owned": sorted(owned)},
            )
        )
        return

    clan_pool = frozenset(pool)
    weights = [max(resolve_discipline_bias(profile, disc_id, clan_pool), 0.01) for disc_id in pool]
    disc = rng.weighted_choice(pool, weights)

    meta = char.setdefault("discipline_meta", {})
    meta["resonance_discipline"] = disc
    meta["resonance_rating"] = 1

    if int(char.get("disciplines", {}).get(disc, 0)) < 1:
        char.setdefault("disciplines", {})[disc] = 1
        assign_powers_for_discipline(
            rng, char, disc, 1, profile, log, phase="base", source="resonance_discipline"
        )

    log.append(
        LogEntry(
            phase="base",
            message=f"Resonance Discipline: {disc} •1",
            detail={"discipline": disc, "resonance": True},
        )
    )


def apply_thin_blood_merit_effect(
    rng: SeededRng,
    char: dict[str, Any],
    merit_id: str,
    profile: Any,
    log: list[LogEntry],
    *,
    caps: dict[str, int],
    phase: str = "merits",
) -> None:
    """Grant mechanical benefits for thin-blood merits with special rules."""
    if merit_id not in _EFFECT_MERITS:
        return

    if merit_id == "thin_blood_alchemist":
        tba = int(char.get("disciplines", {}).get("thin_blood_alchemy", 0))
        if tba < 1:
            char.setdefault("disciplines", {})["thin_blood_alchemy"] = 1
            assign_powers_for_discipline(
                rng, char, "thin_blood_alchemy", 1, profile, log, phase=phase, source="thin_blood_alchemist"
            )
            log.append(
                LogEntry(
                    phase=phase,
                    message="Thin-Blood Merit Thin-Blood Alchemist: free Thin-Blood Alchemy dot",
                    detail={"merit": merit_id},
                )
            )
        formula_id = _pick_free_formula(rng, char, profile)
        if formula_id and len(char.get("thin_blood_formulas", {})) < caps.get("thin_blood_formula", 3):
            record_formula_selection(char, formula_id)
            log.append(
                LogEntry(
                    phase=phase,
                    message=f"Thin-Blood Merit Thin-Blood Alchemist: free formula {formula_id}",
                    detail={"merit": merit_id, "formula": formula_id},
                )
            )
        return

    if merit_id == "discipline_affinity":
        if has_discipline_affinity(char) and char.get("discipline_meta", {}).get("affinity_discipline"):
            return
        meta = char.setdefault("discipline_meta", {})
        if meta.get("affinity_discipline"):
            return
        disc = _pick_affinity_discipline(rng, char, profile)
        meta["affinity_discipline"] = disc
        current = int(char.get("disciplines", {}).get(disc, 0))
        if current < 1:
            char.setdefault("disciplines", {})[disc] = 1
            assign_powers_for_discipline(
                rng, char, disc, 1, profile, log, phase=phase, source="discipline_affinity"
            )
        log.append(
            LogEntry(
                phase=phase,
                message=f"Thin-Blood Merit Discipline Affinity: free {disc} dot",
                detail={"merit": merit_id, "discipline": disc},
            )
        )


def _tb_pair_weight(profile: Any, merit_entry: dict[str, Any]) -> float:
    from wod_chargen.games.lotn_v5.trait_biases import resolve_trait_bias

    merit_bias = float(profile.weights.get("merits", 1.0))
    thin_bias = float(profile.weights.get("thin_blood_merits", 1.75))
    return max(
        merit_bias * thin_bias * resolve_trait_bias(profile, merit_entry["id"], "merits"),
        0.01,
    )


def _tb_flaw_weight(profile: Any, flaw_entry: dict[str, Any]) -> float:
    from wod_chargen.games.lotn_v5.trait_biases import resolve_trait_bias

    merit_bias = float(profile.weights.get("merits", 1.0))
    thin_bias = float(profile.weights.get("thin_blood_merits", 1.75))
    return max(
        merit_bias * thin_bias * resolve_trait_bias(profile, flaw_entry["id"], "flaws"),
        0.01,
    )


def _take_tb_merit_flaw_pair(
    rng: SeededRng,
    char: dict[str, Any],
    profile: Any,
    log: list[LogEntry],
    *,
    caps: dict[str, int],
    phase: str,
) -> bool:
    """Take one thin-blood merit and one paired thin-blood flaw."""
    if thin_blood_pair_count(char) >= _MAX_PAIRS:
        return False
    merit_catalog = _eligible_tb_merits(char, phase=phase)
    if not merit_catalog:
        return False

    merits = _tb_bucket(char, "merit")
    flaws = _tb_bucket(char, "flaw")

    weighted_merits: list[tuple[dict[str, Any], list[dict[str, Any]]]] = []
    merit_weights: list[float] = []
    for merit_entry in merit_catalog:
        flaw_options = _eligible_tb_flaws_for_merit(char, merit_entry, phase=phase)
        if not flaw_options:
            continue
        weighted_merits.append((merit_entry, flaw_options))
        merit_weights.append(_tb_pair_weight(profile, merit_entry))

    if not weighted_merits:
        return False

    merit_entry, flaw_options = rng.weighted_choice(weighted_merits, merit_weights)
    flaw_weights = [_tb_flaw_weight(profile, flaw_entry) for flaw_entry in flaw_options]
    flaw_entry = rng.weighted_choice(flaw_options, flaw_weights)

    merit_id = merit_entry["id"]
    flaw_id = flaw_entry["id"]
    merits[merit_id] = 1
    flaws[flaw_id] = 1

    log.append(
        LogEntry(
            phase=phase,
            message=f"Thin-Blood Merit {merit_entry['label']} + Flaw {flaw_entry['label']}",
            detail={"merit": merit_id, "flaw": flaw_id, "paired": True},
        )
    )
    apply_thin_blood_merit_effect(rng, char, merit_id, profile, log, caps=caps, phase=phase)
    return True


def fill_thin_blood_merit_flaw_pairs(
    rng: SeededRng,
    char: dict[str, Any],
    profile: Any,
    log: list[LogEntry],
    *,
    caps: dict[str, int],
    max_pairs: int,
    phase: str,
) -> int:
    """Take up to max_pairs merit+flaw pairs (no XP cost). Returns pairs taken."""
    limit = min(max_pairs, max(0, _MAX_PAIRS - thin_blood_pair_count(char)))
    taken = 0
    for _ in range(limit):
        if not _take_tb_merit_flaw_pair(rng, char, profile, log, caps=caps, phase=phase):
            break
        taken += 1
    return taken


def run_thin_blood_merit_flaw_creation(
    rng: SeededRng,
    char: dict[str, Any],
    profile: Any,
    log: list[LogEntry],
    *,
    caps: dict[str, int],
) -> None:
    """Grant up to three thin-blood merit/flaw pairs at creation (one flaw per merit)."""
    if char.get("character_type") != "thin_blood":
        return
    fill_thin_blood_merit_flaw_pairs(
        rng, char, profile, log, caps=caps, max_pairs=_MAX_PAIRS, phase="creation"
    )


def spend_merit_driven_discipline_xp(
    rng: SeededRng,
    char: dict[str, Any],
    profile: Any,
    costs: dict[str, Any],
    caps: dict[str, int],
    budget: int,
    *,
    source: str,
    discipline_logs: list[LogEntry],
    log: list[LogEntry],
) -> tuple[int, list[XpLogEntry]]:
    """Spend XP on merit-gated disciplines and formulas before general allocation."""
    from wod_chargen.core.costs import lookup_cost

    if char.get("character_type") != "thin_blood" or not has_merit_driven_disciplines(char):
        return budget, []

    remaining = budget
    xp_log: list[XpLogEntry] = []
    max_disc = int(caps.get("discipline", 2))

    def _buy_discipline_dot(
        disc_id: str,
        *,
        cost_key: str,
        spend_group: str,
        label: str,
    ) -> None:
        nonlocal remaining
        while int(char.get("disciplines", {}).get(disc_id, 0)) < max_disc:
            cur = int(char.get("disciplines", {}).get(disc_id, 0))
            new_level = cur + 1
            cost = lookup_cost(costs, cost_key, new_level=new_level)
            if cost > remaining:
                return
            char.setdefault("disciplines", {})[disc_id] = new_level
            assign_power_at_level(
                rng, char, disc_id, new_level, profile, discipline_logs, phase="xp", source=source
            )
            remaining -= cost
            xp_log.append(
                XpLogEntry(
                    item=disc_id,
                    category="discipline",
                    spend_group=spend_group,
                    new_level=new_level,
                    cost=cost,
                    group_weight=1.0,
                    item_bias=1.0,
                    clan_factor=1.0,
                    efficiency_bias=1.0,
                    roll=1.0,
                    score=1.0,
                    source=f"{source}:merit_discipline",
                )
            )
            log.append(
                LogEntry(
                    phase="xp",
                    message=f"Merit priority: {label} •{new_level} ({cost} XP)",
                    detail={"discipline": disc_id, "merit_priority": True},
                )
            )

    if has_thin_blood_alchemist(char):
        _buy_discipline_dot(
            "thin_blood_alchemy",
            cost_key="discipline_in_clan",
            spend_group="thin_blood_disciplines",
            label="Thin-Blood Alchemy",
        )

    if has_discipline_affinity(char):
        affinity = (char.get("discipline_meta") or {}).get("affinity_discipline")
        if affinity:
            _buy_discipline_dot(
                affinity,
                cost_key="discipline_out_of_clan",
                spend_group="affinity_discipline",
                label=affinity.replace("_", " ").title(),
            )

    if has_thin_blood_alchemist(char):
        tba = int(char.get("disciplines", {}).get("thin_blood_alchemy", 0))
        formula_cap = int(caps.get("thin_blood_formula", 3))
        formulas = sorted(
            load_json_cached(DATA, "thin_blood_formulas.json")["formulas"],
            key=lambda entry: (int(entry.get("level", 1)), entry["id"]),
        )
        owned = owned_power_ids(char)
        for formula in formulas:
            if len(char.get("thin_blood_formulas", {})) >= formula_cap:
                break
            fid = formula["id"]
            if char.get("thin_blood_formulas", {}).get(fid, 0) >= 1 or fid in owned:
                continue
            if tba < int(formula.get("level", 1)):
                continue
            cost = lookup_cost(costs, "thin_blood_formula", new_level=1)
            if cost > remaining:
                break
            record_formula_selection(char, fid)
            remaining -= cost
            xp_log.append(
                XpLogEntry(
                    item=fid,
                    category="thin_blood_formula",
                    spend_group="thin_blood_formulas",
                    new_level=1,
                    cost=cost,
                    group_weight=1.0,
                    item_bias=1.0,
                    clan_factor=1.0,
                    efficiency_bias=1.0,
                    roll=1.0,
                    score=1.0,
                    source=f"{source}:merit_discipline",
                )
            )
            log.append(
                LogEntry(
                    phase="xp",
                    message=f"Merit priority: Formula {formula['label']} ({cost} XP)",
                    detail={"formula": fid, "merit_priority": True},
                )
            )

    return remaining, xp_log


def thin_blood_trait_label(trait_id: str, kind: TraitKind) -> str:
    entry = trait_def(trait_id, kind)
    if entry:
        return str(entry["label"])
    return trait_id.replace("_", " ").title()
