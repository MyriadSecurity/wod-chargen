"""Discipline power catalog, eligibility, and procedural selection."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from wod_chargen.core.data_loader import load_json_cached
from wod_chargen.core.models import LogEntry
from wod_chargen.core.rng import SeededRng

DATA = "wod_chargen.games.lotn_v5.data"


def _named_formula_ids() -> frozenset[str]:
    formulas = load_json_cached(DATA, "thin_blood_formulas.json")["formulas"]
    return frozenset(f["id"] for f in formulas)


NAMED_FORMULA_IDS = _named_formula_ids()


@lru_cache(maxsize=1)
def load_power_catalog() -> dict[str, Any]:
    return load_json_cached(DATA, "discipline_powers.json")


@lru_cache(maxsize=1)
def load_tracks() -> dict[str, Any]:
    return load_json_cached(DATA, "discipline_tracks.json")["tracks"]


@lru_cache(maxsize=1)
def _power_index() -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for disc in load_power_catalog()["disciplines"]:
        disc_id = disc["id"]
        for power in disc["powers"]:
            entry = dict(power)
            entry["discipline_id"] = disc_id
            index[power["id"]] = entry
    return index


@lru_cache(maxsize=1)
def _powers_by_discipline_level() -> dict[str, dict[int, list[dict[str, Any]]]]:
    grouped: dict[str, dict[int, list[dict[str, Any]]]] = {}
    for disc in load_power_catalog()["disciplines"]:
        disc_id = disc["id"]
        grouped.setdefault(disc_id, {})
        for power in disc["powers"]:
            if disc_id == "thin_blood_alchemy" and power["label"].startswith("Counterfeit"):
                continue
            level = int(power["level"])
            grouped[disc_id].setdefault(level, []).append(power)
    return grouped


def power_by_id(power_id: str) -> dict[str, Any] | None:
    return _power_index().get(power_id)


def power_label(power_id: str) -> str:
    p = power_by_id(power_id)
    return p["label"] if p else power_id.replace("_", " ").title()


def track_kind(track_id: str) -> str:
    if track_id in load_tracks():
        return load_tracks()[track_id]["kind"]
    return "discipline"


def _is_named_formula_power(power: dict[str, Any]) -> bool:
    return power["id"] in NAMED_FORMULA_IDS


def powers_for_level(disc_id: str, level: int, *, named_only: bool = False) -> list[dict[str, Any]]:
    raw = list(_powers_by_discipline_level().get(disc_id, {}).get(level, []))
    if named_only or disc_id == "thin_blood_alchemy":
        return [p for p in raw if not p["label"].startswith("Counterfeit")]
    return raw


def owned_power_ids(char: dict[str, Any]) -> set[str]:
    return _owned_power_ids(char)


def _owned_power_ids(char: dict[str, Any]) -> set[str]:
    owned: set[str] = set()
    for levels in char.get("discipline_powers", {}).values():
        owned.update(levels.values())
    for levels in char.get("formula_powers", {}).values():
        owned.update(levels.values())
    owned.update(char.get("rituals", []))
    owned.update(char.get("ceremonies", []))
    return owned


def _discipline_rating(char: dict[str, Any], disc_id: str) -> int:
    return int(char.get("disciplines", {}).get(disc_id, 0))


def _level_slot_taken(char: dict[str, Any], disc_id: str, level: int) -> bool:
    levels = char.get("discipline_powers", {}).get(disc_id, {})
    return str(level) in levels


def _formula_level_taken(char: dict[str, Any], formula_id: str, level: int) -> bool:
    levels = char.get("formula_powers", {}).get(formula_id, {})
    return str(level) in levels


def _has_power(char: dict[str, Any], power_id: str) -> bool:
    return power_id in _owned_power_ids(char)


def _check_prerequisites(char: dict[str, Any], rules: dict[str, Any]) -> bool:
    for pid in rules.get("requires_all_powers", []):
        if not _has_power(char, pid):
            return False
    any_list = rules.get("requires_any_powers", [])
    if any_list and not any(_has_power(char, pid) for pid in any_list):
        return False
    return True


def _check_amalgam(char: dict[str, Any], rules: dict[str, Any]) -> bool:
    disc = rules.get("amalgam_discipline")
    if not disc:
        return True
    need = int(rules.get("amalgam_min_level", 1))
    return _discipline_rating(char, disc) >= need


def _parent_rating(char: dict[str, Any], track_id: str) -> int:
    meta = load_tracks().get(track_id, {})
    parent = meta.get("parent_discipline")
    if parent:
        return _discipline_rating(char, parent)
    return _discipline_rating(char, track_id)


def power_eligible(
    power: dict[str, Any],
    char: dict[str, Any],
    *,
    track_id: str | None = None,
    buying_level: int | None = None,
    ignore_rules: bool = False,
    verify_existing: bool = False,
) -> bool:
    """Return True if this power can be selected now."""
    disc_id = track_id or power.get("discipline_id", "")
    level = int(power["level"])
    rules = power.get("rules") or {}
    kind = rules.get("track") or track_kind(disc_id)

    if kind == "formula":
        formula_id = power["id"]
        if formula_id not in NAMED_FORMULA_IDS:
            return False
        tba = _discipline_rating(char, "thin_blood_alchemy")
        if tba < level:
            return False
        if char.get("thin_blood_formulas", {}).get(formula_id, 0) >= 1:
            return False
        if formula_id in _owned_power_ids(char):
            return False
    elif kind in ("ritual", "ceremony"):
        if not verify_existing and power["id"] in char.get(
            "rituals" if kind == "ritual" else "ceremonies", []
        ):
            return False
        if _parent_rating(char, disc_id) < level:
            return False
    else:
        target_level = buying_level or level
        if power["level"] != target_level:
            return False
        disc_rating = _discipline_rating(char, disc_id)
        if buying_level is not None:
            if buying_level != level:
                return False
        elif disc_rating < level:
            return False
        if not verify_existing and _level_slot_taken(char, disc_id, target_level):
            return False
        if not verify_existing:
            taken_at_level = {
                pid
                for pid in char.get("discipline_powers", {}).get(disc_id, {}).values()
                if power_by_id(pid) and int(power_by_id(pid)["level"]) == target_level
            }
            if power["id"] in taken_at_level:
                return False

    if ignore_rules:
        return True
    if not _check_amalgam(char, rules):
        return False
    return _check_prerequisites(char, rules)


def enumerate_eligible_powers(
    track_id: str,
    level: int,
    char: dict[str, Any],
    *,
    ignore_rules: bool = False,
) -> list[dict[str, Any]]:
    candidates = powers_for_level(track_id, level)
    return [p for p in candidates if power_eligible(p, char, track_id=track_id, buying_level=level, ignore_rules=ignore_rules)]


def pick_power(
    rng: SeededRng,
    candidates: list[dict[str, Any]],
    biases: dict[str, float] | None = None,
) -> dict[str, Any]:
    if not candidates:
        raise ValueError("No eligible discipline powers to pick")
    if len(candidates) == 1:
        return candidates[0]
    weights = [max(float((biases or {}).get(p["id"], 1.0)), 0.01) for p in candidates]
    idx = rng.weighted_choice(list(range(len(candidates))), weights)
    return candidates[idx]


def _ensure_char_discipline_fields(char: dict[str, Any]) -> None:
    char.setdefault("discipline_powers", {})
    char.setdefault("formula_powers", {})
    char.setdefault("rituals", [])
    char.setdefault("ceremonies", [])
    char.setdefault("discipline_meta", {})


def assign_power_at_level(
    rng: SeededRng,
    char: dict[str, Any],
    track_id: str,
    level: int,
    profile: Any,
    log: list[LogEntry],
    *,
    phase: str = "base",
    source: str = "",
) -> str | None:
    """Pick and record one power for a discipline track at the given level."""
    _ensure_char_discipline_fields(char)
    biases = getattr(profile, "discipline_power_biases", None) or {}
    kind = track_kind(track_id)

    if kind == "formula":
        eligible = [p for p in enumerate_eligible_powers(track_id, level, char) if p["id"] in NAMED_FORMULA_IDS]
        if not eligible:
            log.append(
                LogEntry(
                    phase=phase,
                    message=f"Formula level {level} — no eligible named formula",
                    detail={"track": track_id, "level": level},
                )
            )
            return None
        power = pick_power(rng, eligible, biases)
        record_formula_selection(char, power["id"])
        msg = f"Formula {power['label']} ({len(eligible)} options)"
    else:
        eligible = enumerate_eligible_powers(track_id, level, char)
        if not eligible:
            eligible = enumerate_eligible_powers(track_id, level, char, ignore_rules=True)
        if not eligible:
            log.append(
                LogEntry(
                    phase=phase,
                    message=f"Discipline {track_id} level {level} — no eligible power",
                    detail={"track": track_id, "level": level},
                )
            )
            return None
        power = pick_power(rng, eligible, biases)
        if kind == "ritual":
            char["rituals"].append(power["id"])
            msg = f"Ritual {power['label']} ({len(eligible)} options)"
        elif kind == "ceremony":
            char["ceremonies"].append(power["id"])
            msg = f"Ceremony {power['label']} ({len(eligible)} options)"
        else:
            slots = char["discipline_powers"].setdefault(track_id, {})
            slots[str(level)] = power["id"]
            msg = f"Discipline {track_id} level {level}: {power['label']} ({len(eligible)} options)"

    log.append(
        LogEntry(
            phase=phase,
            message=msg,
            detail={
                "track": track_id,
                "level": level,
                "power_id": power["id"],
                "eligible_count": len(eligible),
                "source": source,
            },
        )
    )
    return power["id"]


def assign_powers_for_discipline(
    rng: SeededRng,
    char: dict[str, Any],
    track_id: str,
    rating: int,
    profile: Any,
    log: list[LogEntry],
    *,
    phase: str = "base",
    source: str = "",
) -> None:
    for level in range(1, int(rating) + 1):
        if track_kind(track_id) == "discipline" and _level_slot_taken(char, track_id, level):
            continue
        assign_power_at_level(rng, char, track_id, level, profile, log, phase=phase, source=source)


def record_ritual(char: dict[str, Any], power_id: str, log: list[LogEntry], *, phase: str = "xp", source: str = "") -> None:
    _ensure_char_discipline_fields(char)
    if power_id in char["rituals"]:
        return
    char["rituals"].append(power_id)
    log.append(
        LogEntry(
            phase=phase,
            message=f"Ritual {power_label(power_id)}",
            detail={"power_id": power_id, "source": source},
        )
    )


def record_ceremony(char: dict[str, Any], power_id: str, log: list[LogEntry], *, phase: str = "xp", source: str = "") -> None:
    _ensure_char_discipline_fields(char)
    if power_id in char["ceremonies"]:
        return
    char["ceremonies"].append(power_id)
    log.append(
        LogEntry(
            phase=phase,
            message=f"Ceremony {power_label(power_id)}",
            detail={"power_id": power_id, "source": source},
        )
    )


def record_formula_selection(char: dict[str, Any], formula_id: str) -> None:
    _ensure_char_discipline_fields(char)
    if formula_id in _owned_power_ids(char):
        return
    power = power_by_id(formula_id)
    if power is None:
        return
    char.setdefault("thin_blood_formulas", {})[formula_id] = 1
    char["formula_powers"].setdefault(formula_id, {})["1"] = formula_id


def assign_formula_powers(
    rng: SeededRng,
    char: dict[str, Any],
    formula_id: str,
    rating: int,
    profile: Any,
    log: list[LogEntry],
    *,
    phase: str = "xp",
    source: str = "",
) -> None:
    for level in range(1, int(rating) + 1):
        if _formula_level_taken(char, formula_id, level):
            continue
        assign_power_at_level(rng, char, "thin_blood_alchemy", level, profile, log, phase=phase, source=source)


def validate_discipline_selections(char: dict[str, Any]) -> list[str]:
    """Return validation errors; empty if consistent."""
    errors: list[str] = []
    _ensure_char_discipline_fields(char)

    for disc_id, rating in char.get("disciplines", {}).items():
        if track_kind(disc_id) not in ("discipline", "formula"):
            continue
        picks = char.get("discipline_powers", {}).get(disc_id, {})
        for level in range(1, int(rating) + 1):
            if str(level) not in picks:
                errors.append(f"{disc_id}: missing power pick at level {level}")

    for formula_id, _rating in char.get("thin_blood_formulas", {}).items():
        picks = char.get("formula_powers", {}).get(formula_id, {})
        if formula_id in NAMED_FORMULA_IDS and "1" not in picks:
            errors.append(f"formula {formula_id}: missing power selection")

    for disc_id, levels in char.get("discipline_powers", {}).items():
        for level_str, pid in levels.items():
            power = power_by_id(pid)
            if power is None:
                errors.append(f"unknown power id {pid}")
                continue
            if int(power["level"]) != int(level_str):
                errors.append(f"{pid} at wrong level slot {level_str}")
            if not power_eligible(
                power, char, track_id=disc_id, buying_level=int(level_str), verify_existing=True
            ):
                errors.append(f"{pid} fails eligibility at assignment time")

    for pid in char.get("rituals", []):
        power = power_by_id(pid)
        if power and not power_eligible(
            power, char, track_id="blood_sorcery_rituals", buying_level=int(power["level"]), verify_existing=True
        ):
            errors.append(f"ritual {pid} ineligible")

    for pid in char.get("ceremonies", []):
        power = power_by_id(pid)
        if power and not power_eligible(
            power, char, track_id="ceremonies", buying_level=int(power["level"]), verify_existing=True
        ):
            errors.append(f"ceremony {pid} ineligible")

    return errors


def discipline_pool_for_char(char: dict[str, Any], ctype: str) -> list[str]:
    if ctype == "thin_blood":
        return ["thin_blood_alchemy"]
    clan = char.get("clan") or char.get("domitor_clan")
    if not clan:
        return []
    clans = load_json_cached(DATA, "clans.json")
    return list(clans.get(clan, {}).get("disciplines", []))


def enumerate_ritual_candidates(char: dict[str, Any]) -> list[dict[str, Any]]:
    owned = set(char.get("rituals", []))
    out: list[dict[str, Any]] = []
    bs = _discipline_rating(char, "blood_sorcery")
    for level in range(1, bs + 1):
        for power in powers_for_level("blood_sorcery_rituals", level):
            if power["id"] in owned:
                continue
            if power_eligible(power, char, track_id="blood_sorcery_rituals", buying_level=level):
                out.append(power)
    return out


def enumerate_ceremony_candidates(char: dict[str, Any]) -> list[dict[str, Any]]:
    owned = set(char.get("ceremonies", []))
    out: list[dict[str, Any]] = []
    ob = _discipline_rating(char, "oblivion")
    for level in range(1, ob + 1):
        for power in powers_for_level("ceremonies", level):
            if power["id"] in owned:
                continue
            if power_eligible(power, char, track_id="ceremonies", buying_level=level):
                out.append(power)
    return out
