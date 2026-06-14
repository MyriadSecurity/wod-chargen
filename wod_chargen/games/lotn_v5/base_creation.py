"""Base character creation dot assignment for LoTN V5."""

from __future__ import annotations

from typing import Any

from wod_chargen.core.data_loader import load_json_cached
from wod_chargen.core.models import LogEntry
from wod_chargen.core.rng import SeededRng
from wod_chargen.core.xp_strategy import creation_pick_weight
from wod_chargen.games.lotn_v5.backgrounds import run_background_creation
from wod_chargen.games.lotn_v5.clan_discipline_adapt import resolve_discipline_bias
from wod_chargen.games.lotn_v5.disciplines import assign_powers_for_discipline, discipline_pool_for_char
from wod_chargen.games.lotn_v5.paths import DATA_PKG as DATA

DEFAULT_CAP = 5


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


def apply_base_creation(
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

