"""Generation and Blood Potency assignment (LoTN Step 3)."""

from __future__ import annotations

from typing import Any

from wod_chargen.core.data_loader import load_json_cached
from wod_chargen.core.models import LogEntry
from wod_chargen.core.rng import SeededRng

from wod_chargen.games.lotn_v5.paths import DATA_PKG as DATA

# Neonate-heavy defaults; Storyteller may override via creation.json or options.
_DEFAULT_WEIGHTS: dict[str, dict[int, float]] = {
    "vampire": {13: 4.0, 12: 3.0, 11: 1.5, 10: 0.5, 9: 0.2},
    "thin_blood": {14: 2.0, 15: 2.0, 16: 1.0},
}


def load_generation_catalog() -> dict[str, Any]:
    return load_json_cached(DATA, "generation_blood_potency.json")


def generation_row(generation_number: int) -> dict[str, Any] | None:
    for row in load_generation_catalog()["generations"]:
        if int(row["generation_number"]) == int(generation_number):
            return row
    return None


def _venue_max_generation(venue_config: dict[str, Any]) -> int:
    rules = venue_config.get("house_rules") or {}
    return int(rules.get("max_generation", 13))


def _venue_min_generation(venue_config: dict[str, Any]) -> int:
    rules = venue_config.get("house_rules") or {}
    return int(rules.get("min_generation", 9))


def _eligible_generation_numbers(ctype: str, venue_config: dict[str, Any]) -> list[int]:
    max_gen = _venue_max_generation(venue_config)
    min_gen = _venue_min_generation(venue_config)
    numbers: list[int] = []
    for row in load_generation_catalog()["generations"]:
        gen = int(row["generation_number"])
        if row.get("ghoul"):
            continue
        if ctype == "thin_blood":
            if not row.get("thin_blood"):
                continue
        elif ctype == "vampire":
            if row.get("thin_blood") or gen > max_gen or gen < min_gen:
                continue
        else:
            continue
        numbers.append(gen)
    return sorted(numbers)


def _generation_weights(ctype: str, creation: dict[str, Any]) -> dict[int, float]:
    configured = (creation.get("generation_weights") or {}).get(ctype)
    if isinstance(configured, dict):
        return {int(k): float(v) for k, v in configured.items()}
    return dict(_DEFAULT_WEIGHTS.get(ctype, {}))


def pick_generation_number(
    rng: SeededRng,
    ctype: str,
    venue_config: dict[str, Any],
    creation: dict[str, Any],
    *,
    explicit: int | None = None,
) -> int:
    eligible = _eligible_generation_numbers(ctype, venue_config)
    if not eligible:
        return int(creation.get("generation_default", 13))

    if explicit is not None:
        if int(explicit) not in eligible:
            raise ValueError(f"Generation {explicit} is not allowed for {ctype} in this venue")
        return int(explicit)

    weights_map = _generation_weights(ctype, creation)
    choices = [(gen, weights_map.get(gen, 0.25)) for gen in eligible]
    weights = [max(w, 0.01) for _, w in choices]
    return rng.weighted_choice([gen for gen, _ in choices], weights)


def starting_blood_potency(row: dict[str, Any]) -> int:
    """Free first dot for true vampires (9th–13th); thin-bloods stay at 0."""
    if row.get("thin_blood"):
        return 0
    return 1


def blood_potency_cap(row: dict[str, Any]) -> int:
    return int(row.get("max_blood_potency", 0))


def assign_generation_and_blood_potency(
    rng: SeededRng,
    char: dict[str, Any],
    ctype: str,
    venue_config: dict[str, Any],
    creation: dict[str, Any],
    options: dict[str, Any],
    log: list[LogEntry],
) -> None:
    """Set generation, starting Blood Potency, and generation_meta on the character."""
    if ctype == "ghoul":
        char["blood_potency"] = 0
        char.pop("generation_meta", None)
        char.pop("generation", None)
        return

    explicit = options.get("generation")
    gen_num = pick_generation_number(
        rng,
        ctype,
        venue_config,
        creation,
        explicit=int(explicit) if explicit is not None else None,
    )
    row = generation_row(gen_num)
    if row is None:
        raise ValueError(f"No generation catalog row for {gen_num}")

    char["generation"] = gen_num
    char["blood_potency"] = starting_blood_potency(row)
    char["generation_meta"] = {
        "label": row["label"],
        "min_blood_potency": int(row["min_blood_potency"]),
        "max_blood_potency": int(row["max_blood_potency"]),
        "notes": row.get("notes"),
        "thin_blood": bool(row.get("thin_blood")),
    }

    if row.get("thin_blood"):
        bp_note = "thin-blood (Blood Potency 0)"
    elif int(row.get("min_blood_potency", 1)) > starting_blood_potency(row):
        bp_note = f"Blood Potency •{char['blood_potency']} (9th Gen minimum at creation)"
    else:
        bp_note = f"Blood Potency •{char['blood_potency']} (free starting dot)"

    log.append(
        LogEntry(
            phase="base",
            message=f"Generation {row['label']} — {bp_note}",
            detail={"generation": gen_num, "blood_potency": char["blood_potency"]},
        )
    )


def apply_mandatory_blood_potency(
    char: dict[str, Any],
    costs: dict[str, Any],
    budget: int,
) -> tuple[int, list[Any], list[LogEntry]]:
    """Spend XP to reach generation minimum Blood Potency before discretionary buys."""
    from wod_chargen.core.costs import lookup_cost
    from wod_chargen.core.models import XpLogEntry

    meta = char.get("generation_meta")
    if not meta:
        return budget, [], []

    min_bp = int(meta.get("min_blood_potency", 1))
    cur = int(char.get("blood_potency", 0))
    if cur >= min_bp:
        return budget, [], []

    gen_label = meta.get("label") or f"Generation {char.get('generation', '?')}"
    logs: list[LogEntry] = []
    xp_entries: list[XpLogEntry] = []
    remaining = budget

    for target in range(cur + 1, min_bp + 1):
        cost = lookup_cost(costs, "blood_potency", new_level=target)
        if remaining < cost:
            logs.append(
                LogEntry(
                    phase="xp_spend",
                    message=(
                        f"Blood Potency •{target} mandatory for {gen_label} "
                        f"({cost} XP required, {remaining} available)"
                    ),
                    detail={"mandatory": True, "shortfall": cost - remaining, "target": target},
                )
            )
            return remaining, xp_entries, logs

        char["blood_potency"] = target
        remaining -= cost
        xp_entries.append(
            XpLogEntry(
                item="blood_potency",
                category="blood_potency",
                spend_group="blood_potency",
                new_level=target,
                cost=cost,
                group_weight=1.0,
                item_bias=1.0,
                clan_factor=1.0,
                efficiency_bias=1.0,
                roll=0.0,
                score=0.0,
                source="mandatory",
            )
        )
        logs.append(
            LogEntry(
                phase="xp_spend",
                message=(
                    f"Blood Potency +1 → •{target} ({cost} XP) "
                    f"[mandatory, {gen_label}]"
                ),
                detail={"mandatory": True, "target": target},
            )
        )

    return remaining, xp_entries, logs
