"""LoTN V5 merits and flaws — catalog, creation trade, and XP purchases."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from wod_chargen.core.costs import lookup_cost
from wod_chargen.core.data_loader import load_json_cached
from wod_chargen.core.rng import SeededRng
from wod_chargen.core.spender import PurchaseCandidate
from wod_chargen.games.lotn_v5.backgrounds import (
    entries_for_type,
    total_background_dots,
    total_modifier_dots,
)

DATA = "wod_chargen.games.lotn_v5.data"

_MAX_FREE_MERIT_FROM_FLAWS = 10
_TAKE_FLAWS_CHANCE = 0.55

TraitKind = Literal["merit", "flaw"]
TraitPhase = Literal["creation", "xp"]


@dataclass
class MeritFlawCreationLedger:
    """Tracks optional Step 8 flaw-for-merit trade at creation."""

    flaw_credit: int = 0
    merit_from_trade: int = 0
    free_merit_cap: int = _MAX_FREE_MERIT_FROM_FLAWS

    @property
    def trade_budget(self) -> int:
        return min(self.flaw_credit, self.free_merit_cap)

    @property
    def trade_remaining(self) -> int:
        return max(0, self.trade_budget - self.merit_from_trade)

    def to_meta(self) -> dict[str, Any]:
        return {
            "flaw_credit": self.flaw_credit,
            "merit_from_trade": self.merit_from_trade,
            "free_merit_cap": self.free_merit_cap,
        }

    @classmethod
    def from_meta(cls, meta: dict[str, Any]) -> MeritFlawCreationLedger:
        return cls(
            flaw_credit=int(meta.get("flaw_credit", 0)),
            merit_from_trade=int(meta.get("merit_from_trade", 0)),
            free_merit_cap=int(meta.get("free_merit_cap", _MAX_FREE_MERIT_FROM_FLAWS)),
        )


def load_catalog() -> dict[str, Any]:
    return load_json_cached(DATA, "merits_flaws.json")


def _trait_index(kind: TraitKind) -> dict[str, dict[str, Any]]:
    key = "merits" if kind == "merit" else "flaws"
    return {entry["id"]: entry for entry in load_catalog()[key]}


def trait_def(trait_id: str, kind: TraitKind) -> dict[str, Any] | None:
    return _trait_index(kind).get(trait_id)


def trait_label(trait_id: str, kind: TraitKind) -> str:
    entry = trait_def(trait_id, kind)
    if entry:
        return str(entry["label"])
    return trait_id.replace("_", " ").title()


def _eligible_for_type(entry: dict[str, Any], ctype: str) -> bool:
    if entry.get("thin_blood_only"):
        return False
    if entry.get("ghoul_only") and ctype != "ghoul":
        return False
    if ctype == "thin_blood" and entry.get("category") == "ghoul":
        return False
    return True


def traits_for_type(kind: TraitKind, ctype: str) -> list[dict[str, Any]]:
    key = "merits" if kind == "merit" else "flaws"
    return [e for e in load_catalog()[key] if _eligible_for_type(e, ctype)]


def trait_rules(entry: dict[str, Any]) -> dict[str, Any]:
    rules = entry.get("rules")
    return dict(rules) if isinstance(rules, dict) else {}


def trait_base_id(trait_key: str) -> str:
    return trait_key.split(":", 1)[0]


def trait_instance_detail(trait_key: str) -> str | None:
    if ":" not in trait_key:
        return None
    return trait_key.split(":", 1)[1]


def instance_trait_key(base_id: str, detail: str) -> str:
    return f"{base_id}:{detail}"


def trait_display_label(trait_key: str, kind: TraitKind) -> str:
    base_id = trait_base_id(trait_key)
    entry = trait_def(base_id, kind)
    label = str(entry["label"]) if entry else base_id.replace("_", " ").title()
    detail = trait_instance_detail(trait_key)
    if detail and entry and trait_rules(entry).get("instance_key") == "sphere":
        from wod_chargen.games.lotn_v5.backgrounds import sphere_label

        return f"{label} ({sphere_label(detail)})"
    return label


def poor_level(char: dict[str, Any]) -> int:
    return int(char.get("flaws", {}).get("poor", 0))


def no_haven_flaw_active(char: dict[str, Any]) -> bool:
    return int(char.get("flaws", {}).get("no_haven", 0)) > 0


def total_haven_advantage_dots(char: dict[str, Any]) -> int:
    return total_modifier_dots(entries_for_type(char.get("backgrounds", []), "haven"), "advantage")


def max_haven_connection_dots_allowed(char: dict[str, Any]) -> int | None:
    """Total Haven connection dots allowed while Poor/No Haven apply; None = no Poor cap."""
    if no_haven_flaw_active(char) or poor_level(char) >= 3:
        return 0
    if poor_level(char) >= 1:
        return 1
    return None


def max_haven_advantage_dots_allowed(char: dict[str, Any]) -> int | None:
    """Total Haven advantage dots allowed; None = no Poor cap."""
    if no_haven_flaw_active(char) or poor_level(char) >= 2:
        return 0
    if poor_level(char) >= 1:
        return 1
    return None


def background_connection_blocked(char: dict[str, Any], bg_type: str) -> bool:
    if bg_type == "resources" and poor_level(char) > 0:
        return True
    if bg_type == "haven" and (no_haven_flaw_active(char) or poor_level(char) >= 3):
        return True
    return False


def poor_rating_eligible(char: dict[str, Any], new_rating: int) -> bool:
    if _background_type_dots(char, "resources") > 0:
        return False
    haven_dots = _background_type_dots(char, "haven")
    haven_adv = total_haven_advantage_dots(char)
    if new_rating >= 3 and haven_dots > 0:
        return False
    if new_rating >= 1 and haven_dots > 1:
        return False
    if new_rating >= 2 and haven_adv > 0:
        return False
    if new_rating >= 1 and haven_adv > 1:
        return False
    return True


def haven_advantage_blocked(char: dict[str, Any]) -> bool:
    cap = max_haven_advantage_dots_allowed(char)
    if cap is None:
        return False
    return total_haven_advantage_dots(char) >= cap


def _used_instance_details(char: dict[str, Any], base_id: str) -> set[str]:
    used: set[str] = set()
    prefix = f"{base_id}:"
    for key in char.get("flaws", {}):
        if key.startswith(prefix):
            used.add(key[len(prefix) :])
    return used


def available_instance_details(char: dict[str, Any], entry: dict[str, Any]) -> list[str]:
    rules = trait_rules(entry)
    if rules.get("instance_key") != "sphere":
        return []
    from wod_chargen.games.lotn_v5.backgrounds import sphere_defs

    used = _used_instance_details(char, entry["id"])
    return [s["id"] for s in sphere_defs() if s["id"] not in used]


def _migrate_legacy_enemy(char: dict[str, Any], rng: SeededRng, profile: Any) -> None:
    flaws = char.setdefault("flaws", {})
    legacy = int(flaws.get("enemy", 0))
    if legacy <= 0:
        return
    from wod_chargen.games.lotn_v5.backgrounds import _pick_sphere

    available = available_instance_details(char, trait_def("enemy", "flaw") or {"id": "enemy", "rules": {}})
    sphere = available[0] if len(available) == 1 else _pick_sphere(rng, profile)
    flaws[instance_trait_key("enemy", sphere)] = legacy
    del flaws["enemy"]


def _instance_max_dots(entry: dict[str, Any]) -> int:
    rules = trait_rules(entry)
    if rules.get("max_dots_per_instance") is not None:
        return int(rules["max_dots_per_instance"])
    max_dots = entry.get("max_dots")
    return int(max_dots) if max_dots is not None else int(entry.get("dot_cost", 1))


def instance_trait_available(entry: dict[str, Any], char: dict[str, Any]) -> bool:
    if not trait_rules(entry).get("instance_key"):
        return False
    base_id = entry["id"]
    max_per = _instance_max_dots(entry)
    flaws = char.get("flaws", {})
    if int(flaws.get(base_id, 0)) > 0 and int(flaws[base_id]) < max_per:
        return True
    for key, rating in flaws.items():
        if trait_base_id(key) == base_id and int(rating) > 0 and int(rating) < max_per:
            return True
    return bool(available_instance_details(char, entry))


def _apply_instance_flaw_increment(
    rng: SeededRng,
    char: dict[str, Any],
    entry: dict[str, Any],
    profile: Any,
) -> tuple[str, int, int, int] | None:
    """Apply one dot to an instanced flaw. Returns (key, old, new, credit) or None."""
    if not trait_eligible(entry, "flaw", char):
        return None
    _migrate_legacy_enemy(char, rng, profile)
    base_id = entry["id"]
    max_per = _instance_max_dots(entry)
    flaws = char.setdefault("flaws", {})
    options: list[tuple[str, str]] = []

    for key, rating in list(flaws.items()):
        if trait_base_id(key) != base_id or int(rating) >= max_per:
            continue
        options.append(("inc", key))

    for detail in available_instance_details(char, entry):
        options.append(("new", detail))

    if not options:
        return None

    action, detail = rng.choice(options)
    if action == "new":
        key = instance_trait_key(base_id, detail)
        flaws[key] = 1
        return key, 0, 1, 1

    key = detail
    old = int(flaws[key])
    flaws[key] = old + 1
    return key, old, old + 1, 1


def apply_enemy_flaw(
    rng: SeededRng,
    char: dict[str, Any],
    profile: Any,
    dots: int,
    *,
    ignore_rules: bool = False,
) -> tuple[int, str | None]:
    """Grant Enemy flaw dots in an unused Sphere (one Enemy per sphere)."""
    entry = trait_def("enemy", "flaw")
    if entry is None or dots <= 0:
        return 0, None
    _migrate_legacy_enemy(char, rng, profile)
    flaws = char.setdefault("flaws", {})
    available = available_instance_details(char, entry)
    if available:
        sphere = rng.choice(available)
        key = instance_trait_key("enemy", sphere)
        added = apply_trait_dots(flaws, key, "flaw", dots, char, ignore_rules=ignore_rules)
        return added, key if added else None
    for key, rating in list(flaws.items()):
        if trait_base_id(key) == "enemy" and int(rating) < _instance_max_dots(entry):
            added = apply_trait_dots(flaws, key, "flaw", dots, char, ignore_rules=ignore_rules)
            return added, key if added else None
    return 0, None


def _background_type_dots(char: dict[str, Any], bg_type: str) -> int:
    return total_background_dots(entries_for_type(char.get("backgrounds", []), bg_type))


def _trait_present(char: dict[str, Any], trait_id: str) -> bool:
    merits = char.get("merits", {})
    flaws = char.get("flaws", {})
    tb_merits = char.get("thin_blood_merits", {})
    tb_flaws = char.get("thin_blood_flaws", {})
    if (
        int(merits.get(trait_id, 0)) > 0
        or int(flaws.get(trait_id, 0)) > 0
        or int(tb_merits.get(trait_id, 0)) > 0
        or int(tb_flaws.get(trait_id, 0)) > 0
    ):
        return True
    prefix = f"{trait_id}:"
    for bucket in (merits, flaws, tb_merits, tb_flaws):
        for key, rating in bucket.items():
            if (key == trait_id or key.startswith(prefix)) and int(rating) > 0:
                return True
    return False


def _category_trait_ids(kind: TraitKind, category: str, ctype: str) -> set[str]:
    return {e["id"] for e in traits_for_type(kind, ctype) if e.get("category") == category}


def _conflicts_with_present(
    entry: dict[str, Any],
    kind: TraitKind,
    char: dict[str, Any],
) -> bool:
    """True when an already-assigned merit/flaw blocks this pick."""
    entry_id = entry["id"]
    ctype = str(char.get("character_type", "vampire"))
    rules = trait_rules(entry)

    for other_id in rules.get("forbidden_with", []):
        if other_id != entry_id and _trait_present(char, other_id):
            return True

    for spec in rules.get("forbidden_with_categories", []):
        target_kind: TraitKind = spec["kind"]
        category = spec["category"]
        traits = char.get("merits" if target_kind == "merit" else "flaws", {})
        cat_ids = _category_trait_ids(target_kind, category, ctype)
        if any(int(traits.get(tid, 0)) > 0 for tid in cat_ids):
            return True

    for check_kind in ("merit", "flaw"):
        traits = char.get("merits" if check_kind == "merit" else "flaws", {})
        tb_traits = char.get("thin_blood_merits" if check_kind == "merit" else "thin_blood_flaws", {})
        for trait_id, rating in {**traits, **tb_traits}.items():
            if int(rating) <= 0:
                continue
            other = trait_def(trait_base_id(trait_id), check_kind)  # type: ignore[arg-type]
            if other is None:
                continue
            other_rules = trait_rules(other)
            if entry_id in other_rules.get("forbidden_with", []):
                return True
            for spec in other_rules.get("forbidden_with_categories", []):
                if spec["kind"] == kind and entry.get("category") == spec["category"]:
                    return True
    return False


def trait_eligible(
    entry: dict[str, Any],
    kind: TraitKind,
    char: dict[str, Any],
    *,
    phase: TraitPhase = "creation",
    ignore_rules: bool = False,
) -> bool:
    """Whether a merit/flaw may be assigned given current character state."""
    if ignore_rules:
        return True

    rules = trait_rules(entry)
    if rules.get("creation_only") and phase == "xp":
        return False

    clan = str(char.get("clan") or char.get("domitor_clan") or "")
    if clan and clan in rules.get("forbidden_clans", []):
        return False

    max_bp = rules.get("requires_max_blood_potency")
    if max_bp is not None and int(char.get("blood_potency", 1)) > int(max_bp):
        return False

    max_gen = rules.get("requires_max_generation")
    if max_gen is not None and int(char.get("generation", 13)) > int(max_gen):
        return False

    for bg_type, min_dots in rules.get("requires_background_min", {}).items():
        if _background_type_dots(char, bg_type) < int(min_dots):
            return False

    for bg_type, max_dots in rules.get("requires_background_max", {}).items():
        if _background_type_dots(char, bg_type) > int(max_dots):
            return False

    if _conflicts_with_present(entry, kind, char):
        return False

    entry_id = entry["id"]
    flaws = char.get("flaws", {})
    if entry_id == "no_haven" and _background_type_dots(char, "haven") > 0:
        return False

    current = int(flaws.get(entry_id, 0))
    step = trait_increment(entry, current, char, kind=kind)
    if step is not None and entry_id == "poor":
        new_level = current + step[0]
        if not poor_rating_eligible(char, new_level):
            return False

    if trait_rules(entry).get("instance_key") and kind == "flaw":
        return instance_trait_available(entry, char)

    return True


def effective_max_dots(
    entry: dict[str, Any],
    kind: TraitKind,
    char: dict[str, Any] | None = None,
) -> int | None:
    max_dots = entry.get("max_dots")
    if max_dots is None:
        return None
    cap = int(max_dots)
    rules = trait_rules(entry)
    if char is not None and rules.get("max_dots_from_health_minus") is not None:
        stamina = int(char.get("attributes", {}).get("stamina", 1))
        health_cap = (stamina + 3) - int(rules["max_dots_from_health_minus"])
        cap = min(cap, max(0, health_cap))
    return cap


def max_trait_rating(trait_id: str, kind: TraitKind, char: dict[str, Any] | None = None) -> int:
    entry = trait_def(trait_base_id(trait_id), kind)
    if entry is None:
        return 0
    max_dots = effective_max_dots(entry, kind, char)
    if max_dots is not None:
        if trait_rules(entry).get("instance_key"):
            return int(max_dots)
        return int(max_dots)
    return int(entry.get("dot_cost", 1))


def trait_increment(
    entry: dict[str, Any],
    current: int,
    char: dict[str, Any] | None = None,
    *,
    kind: TraitKind = "merit",
) -> tuple[int, int] | None:
    """Return (rating_increment, credit_cost) for one purchase, or None if maxed."""
    dot_cost = int(entry.get("dot_cost", 1))
    max_dots = effective_max_dots(entry, kind, char)
    if max_dots is not None:
        if current >= int(max_dots):
            return None
        return (1, dot_cost)
    if current > 0:
        return None
    if dot_cost <= 0:
        return (1, 0)
    return (dot_cost, dot_cost)


def _eligible_trait_targets(
    traits: dict[str, int],
    catalog: list[dict[str, Any]],
    char: dict[str, Any],
    kind: TraitKind,
    *,
    phase: TraitPhase = "creation",
) -> list[tuple[dict[str, Any], int]]:
    targets: list[tuple[dict[str, Any], int]] = []
    for entry in catalog:
        if trait_rules(entry).get("instance_key"):
            if instance_trait_available(entry, char) and trait_eligible(entry, kind, char, phase=phase):
                targets.append((entry, 0))
            continue
        if not trait_eligible(entry, kind, char, phase=phase):
            continue
        current = int(traits.get(entry["id"], 0))
        if trait_increment(entry, current, char, kind=kind) is not None:
            targets.append((entry, current))
    return targets


def _pick_trait(
    rng: SeededRng,
    traits: dict[str, int],
    catalog: list[dict[str, Any]],
    char: dict[str, Any],
    kind: TraitKind,
    profile: Any,
    *,
    item_bias: float = 1.0,
    phase: TraitPhase = "creation",
) -> tuple[dict[str, Any], int] | None:
    from wod_chargen.games.lotn_v5.trait_biases import resolve_trait_bias

    targets = _eligible_trait_targets(traits, catalog, char, kind, phase=phase)
    if not targets:
        return None
    category = "merits" if kind == "merit" else "flaws"
    weights = [
        item_bias * resolve_trait_bias(profile, entry["id"], category)
        for entry, _current in targets
    ]
    return rng.weighted_choice(targets, weights)


def _apply_trait_increment(
    traits: dict[str, int],
    entry: dict[str, Any],
    current: int,
    char: dict[str, Any],
    *,
    kind: TraitKind,
) -> tuple[int, int]:
    step = trait_increment(entry, current, char, kind=kind)
    assert step is not None
    rating_inc, credit = step
    new_rating = current + rating_inc
    traits[entry["id"]] = new_rating
    return new_rating, credit


def _dots_display(rating: int) -> str:
    return "•" * rating


def apply_trait_dots(
    traits: dict[str, int],
    trait_id: str,
    kind: TraitKind,
    requested_dots: int,
    char: dict[str, Any] | None = None,
    *,
    ignore_rules: bool = False,
) -> int:
    """Raise a merit or flaw rating, respecting catalog caps and prerequisites."""
    if requested_dots <= 0:
        return 0

    entry = trait_def(trait_base_id(trait_id), kind)
    current = int(traits.get(trait_id, 0))
    if entry is None:
        traits[trait_id] = current + requested_dots
        return requested_dots

    if char is not None and not trait_eligible(entry, kind, char, ignore_rules=ignore_rules):
        return 0

    added = 0
    while added < requested_dots:
        step = trait_increment(entry, current, char, kind=kind)
        if step is None:
            break
        rating_inc, _credit = step
        if entry.get("max_dots") is not None or effective_max_dots(entry, kind, char) is not None:
            take = min(1, requested_dots - added)
            current += take
            added += take
        else:
            current += rating_inc
            added += rating_inc
            break
    if added:
        traits[trait_id] = current
    return added


def run_merit_flaw_creation(
    rng: SeededRng,
    char: dict[str, Any],
    profile: Any,
    ctype: str,
) -> tuple[list[str], MeritFlawCreationLedger]:
    """Optional Step 8 — take flaws for merit credit, spend up to 10 free merit dots."""
    lines: list[str] = []
    ledger = MeritFlawCreationLedger()
    merits = char.setdefault("merits", {})
    flaws = char.setdefault("flaws", {})
    flaw_catalog = traits_for_type("flaw", ctype)
    merit_catalog = [m for m in traits_for_type("merit", ctype) if int(m.get("dot_cost", 1)) > 0]

    if flaw_catalog and rng.uniform() < _TAKE_FLAWS_CHANCE:
        attempts = rng.choice([1, 1, 2, 2, 3])
        for _ in range(attempts):
            picked = _pick_trait(
                rng,
                flaws,
                flaw_catalog,
                char,
                "flaw",
                profile,
                item_bias=profile.weights.get("merits", 1.0),
            )
            if picked is None:
                break
            entry, current = picked
            if trait_rules(entry).get("instance_key"):
                result = _apply_instance_flaw_increment(rng, char, entry, profile)
                if result is None:
                    break
                key, old, new_rating, credit = result
                ledger.flaw_credit += credit
                lines.append(
                    f"Flaw {trait_display_label(key, 'flaw')} +{new_rating - old} "
                    f"→ {_dots_display(new_rating)} [creation, +{credit} merit credit]"
                )
                continue
            new_rating, credit = _apply_trait_increment(flaws, entry, current, char, kind="flaw")
            ledger.flaw_credit += credit
            lines.append(
                f"Flaw {entry['label']} +{new_rating - current} → {_dots_display(new_rating)} "
                f"[creation, +{credit} merit credit]"
            )

    merit_bias = profile.weights.get("merits", 1.0)
    from wod_chargen.games.lotn_v5.trait_biases import resolve_trait_bias

    while ledger.trade_remaining > 0:
        affordable = [
            (entry, current)
            for entry, current in _eligible_trait_targets(merits, merit_catalog, char, "merit")
            if trait_increment(entry, current, char, kind="merit") is not None
            and trait_increment(entry, current, char, kind="merit")[1] <= ledger.trade_remaining
        ]
        if not affordable:
            if ledger.trade_remaining > 0 and ledger.merit_from_trade > 0:
                lines.append(
                    f"Merit +{ledger.trade_remaining} unplaced (flaw trade, no affordable merits)"
                )
            break

        weights = [
            merit_bias * resolve_trait_bias(profile, entry["id"], "merits")
            for entry, _current in affordable
        ]
        picked = rng.weighted_choice(affordable, weights)
        entry, current = picked
        new_rating, credit = _apply_trait_increment(merits, entry, current, char, kind="merit")
        ledger.merit_from_trade += credit
        lines.append(
            f"Merit {entry['label']} +{new_rating - current} → {_dots_display(new_rating)} "
            f"[flaw trade]"
        )

    return lines, ledger


def xp_merit_purchase_cost(
    entry: dict[str, Any],
    current: int,
    costs: dict[str, Any],
    char: dict[str, Any] | None = None,
) -> int | None:
    step = trait_increment(entry, current, char, kind="merit")
    if step is None:
        return None
    rating_inc, _credit = step
    per_dot_xp = lookup_cost(costs, "merit", new_level=current + rating_inc)
    dot_cost = int(entry.get("dot_cost", 1))
    if entry.get("max_dots") is not None:
        return dot_cost * per_dot_xp
    return dot_cost * per_dot_xp


def enumerate_xp_merit_purchases(
    char: dict[str, Any],
    profile: Any,
    costs: dict[str, Any],
    ctype: str,
    source: str,
) -> list[PurchaseCandidate]:
    candidates: list[PurchaseCandidate] = []
    merits = char.setdefault("merits", {})
    weight = profile.weights.get("merits", 1.0)

    from wod_chargen.games.lotn_v5.trait_biases import resolve_trait_bias

    for entry in traits_for_type("merit", ctype):
        if int(entry.get("dot_cost", 1)) <= 0:
            continue
        if not trait_eligible(entry, "merit", char, phase="xp"):
            continue
        merit_id = entry["id"]
        current = int(merits.get(merit_id, 0))
        step = trait_increment(entry, current, char, kind="merit")
        if step is None:
            continue
        rating_inc, _credit = step
        new_level = current + rating_inc
        cost = xp_merit_purchase_cost(entry, current, costs, char)
        if cost is None:
            continue

        def apply_merit(m=merit_id, nl=new_level) -> None:
            merits[m] = nl

        candidates.append(
            PurchaseCandidate(
                item_id=merit_id,
                category="merit",
                spend_group="merits",
                new_level=new_level,
                cost=cost,
                weight=weight,
                item_bias=resolve_trait_bias(profile, merit_id, "merits"),
                clan_factor=1.0,
                source=source,
                apply=apply_merit,
            )
        )

    return candidates
