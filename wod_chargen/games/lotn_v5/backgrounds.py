"""LoTN V5 backgrounds — entries, spheres, modifiers, and procedural assignment."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from wod_chargen.core.data_loader import load_json_cached
from wod_chargen.core.rng import SeededRng

DATA = "wod_chargen.games.lotn_v5.data"

ModifierKind = Literal["advantage", "disadvantage"]
ModifierSource = Literal["creation_pool", "disadv_trade", "xp", "free"]
_MODIFIER_KEY = {"advantage": "advantages", "disadvantage": "disadvantages"}

_NAME_TEMPLATES = {
    "allies": ["{sphere} ally", "contact in {sphere}", "{sphere} fixer"],
    "contacts": ["{sphere} informant", "{sphere} insider", "{sphere} source"],
    "haven": ["{label} apartment", "safehouse", "bolthole"],
    "mask": ["{label} cover", "night identity", "alias"],
}

_MAX_FREE_ADV_FROM_DISADV = 5


@dataclass
class BackgroundCreationLedger:
    """Tracks creation pool and disadvantage-trade accounting (SRD)."""

    pool_total: int
    pool_spent_connection: int = 0
    pool_spent_modifier: int = 0
    pool_unplaced: int = 0
    disadv_dots_added: int = 0
    adv_from_disadv_granted: int = 0
    free_adv_from_disadv_cap: int = _MAX_FREE_ADV_FROM_DISADV
    xp_spent_modifier: int = 0

    @property
    def pool_spent(self) -> int:
        return self.pool_spent_connection + self.pool_spent_modifier + self.pool_unplaced

    @property
    def pool_remaining(self) -> int:
        return self.pool_total - self.pool_spent

    def disadv_trade_credit(self, *, grant: bool = True) -> int:
        if not grant:
            return 0
        return min(self.disadv_dots_added, self.free_adv_from_disadv_cap)

    @property
    def disadv_trade_remaining(self) -> int:
        return self.disadv_trade_credit() - self.adv_from_disadv_granted

    def to_meta(self) -> dict[str, Any]:
        return {
            "creation_pool": {
                "total": self.pool_total,
                "connection": self.pool_spent_connection,
                "modifier": self.pool_spent_modifier,
                "unplaced": self.pool_unplaced,
            },
            "disadvantage_dots": self.disadv_dots_added,
            "adv_from_disadv_trade": self.adv_from_disadv_granted,
            "free_adv_from_disadv_cap": self.free_adv_from_disadv_cap,
            "xp_spent_modifier": self.xp_spent_modifier,
        }

    @classmethod
    def from_meta(cls, meta: dict[str, Any]) -> BackgroundCreationLedger:
        pool = meta.get("creation_pool", {})
        return cls(
            pool_total=int(pool.get("total", 0)),
            pool_spent_connection=int(pool.get("connection", 0)),
            pool_spent_modifier=int(pool.get("modifier", 0)),
            pool_unplaced=int(pool.get("unplaced", 0)),
            disadv_dots_added=int(meta.get("disadvantage_dots", 0)),
            adv_from_disadv_granted=int(meta.get("adv_from_disadv_trade", 0)),
            free_adv_from_disadv_cap=int(meta.get("free_adv_from_disadv_cap", _MAX_FREE_ADV_FROM_DISADV)),
            xp_spent_modifier=int(meta.get("xp_spent_modifier", 0)),
        )


def load_background_catalog() -> dict[str, Any]:
    return load_json_cached(DATA, "backgrounds.json")


def background_defs() -> dict[str, Any]:
    return load_background_catalog()["backgrounds"]


def sphere_defs() -> list[dict[str, str]]:
    return load_background_catalog()["spheres"]


def sphere_label(sphere_id: str) -> str:
    for sphere in sphere_defs():
        if sphere["id"] == sphere_id:
            return sphere["label"]
    return sphere_id.replace("_", " ").title()


def level_label(bg_type: str, dots: int) -> str:
    spec = background_defs().get(bg_type, {})
    for level in spec.get("levels", []):
        if level["dots"] == dots:
            return level["label"]
    return f"Level {dots}"


def level_summary(bg_type: str, dots: int) -> str:
    spec = background_defs().get(bg_type, {})
    for level in spec.get("levels", []):
        if level["dots"] == dots:
            return level.get("summary", level["label"])
    return ""


def background_label(bg_type: str) -> str:
    spec = background_defs().get(bg_type, {})
    return spec.get("label", bg_type.replace("_", " ").title())


def empty_backgrounds() -> list[dict[str, Any]]:
    return []


def total_background_dots(entries: list[dict[str, Any]]) -> int:
    return sum(int(e.get("dots", 0)) for e in entries)


def total_modifier_dots(entries: list[dict[str, Any]], kind: ModifierKind) -> int:
    key = _MODIFIER_KEY[kind]
    total = 0
    for entry in entries:
        for mod in entry.get(key, []):
            total += _modifier_rating_value(mod)
    return total


def entries_for_type(entries: list[dict[str, Any]], bg_type: str) -> list[dict[str, Any]]:
    return [e for e in entries if e.get("type") == bg_type]


def modifier_max_dots(mod_def: dict[str, Any]) -> int:
    return int(mod_def.get("max_dots", mod_def.get("dots", 1)))


def modifier_catalog_label(bg_type: str, mod_id: str, kind: ModifierKind) -> str:
    spec = background_defs().get(bg_type, {})
    key = _MODIFIER_KEY[kind]
    for mod in spec.get(key, []):
        if mod["id"] == mod_id:
            return mod["label"]
    return mod_id.replace("_", " ").title()


def _modifier_rating_value(mod: Any) -> int:
    if isinstance(mod, dict):
        return int(mod.get("dots", 0))
    if isinstance(mod, str):
        return 1
    return 0


def _modifier_id(mod: Any) -> str | None:
    if isinstance(mod, dict):
        return mod.get("id")
    if isinstance(mod, str):
        return mod
    return None


def get_modifier_rating(entry: dict[str, Any], mod_id: str, kind: ModifierKind) -> int:
    key = _MODIFIER_KEY[kind]
    for mod in entry.get(key, []):
        if _modifier_id(mod) == mod_id:
            return _modifier_rating_value(mod)
    return 0


def set_modifier_rating(
    entry: dict[str, Any],
    mod_id: str,
    kind: ModifierKind,
    dots: int,
) -> None:
    key = _MODIFIER_KEY[kind]
    mods: list[Any] = entry.setdefault(key, [])
    for idx, mod in enumerate(mods):
        if _modifier_id(mod) == mod_id:
            mods[idx] = {"id": mod_id, "dots": dots}
            return
    mods.append({"id": mod_id, "dots": dots})


def entry_display_name(entry: dict[str, Any]) -> str:
    return entry.get("name") or background_label(entry.get("type", ""))


def modifier_item_key(entry: dict[str, Any], mod_id: str, kind: ModifierKind) -> str:
    prefix = "mod" if kind == "advantage" else "dis"
    return f"{entry['type']}/{entry_display_name(entry)}/{prefix}:{mod_id}"


def can_add_modifier_dot(
    entry: dict[str, Any],
    mod_def: dict[str, Any],
    kind: ModifierKind,
    char: dict[str, Any] | None = None,
) -> bool:
    if int(entry.get("dots", 0)) <= 0:
        return False
    mod_id = mod_def["id"]
    cur = get_modifier_rating(entry, mod_id, kind)
    if cur >= modifier_max_dots(mod_def):
        return False
    required_bg = int(mod_def.get("requires_dots", 1))
    if int(entry.get("dots", 0)) < required_bg:
        return False
    if char and kind == "advantage" and entry.get("type") == "haven":
        from wod_chargen.games.lotn_v5.merits_flaws import haven_advantage_blocked

        if haven_advantage_blocked(char):
            return False
    return True


def _eligible_modifier_targets(
    entries: list[dict[str, Any]],
    kind: ModifierKind,
    char: dict[str, Any] | None = None,
) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    targets: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for entry in entries:
        if int(entry.get("dots", 0)) <= 0:
            continue
        spec = background_defs().get(entry["type"], {})
        catalog = spec.get(_MODIFIER_KEY[kind], [])
        for mod_def in catalog:
            if can_add_modifier_dot(entry, mod_def, kind, char):
                targets.append((entry, mod_def))
    return targets


def _source_tag(source: ModifierSource) -> str:
    return {
        "creation_pool": "creation pool",
        "disadv_trade": "disadvantage trade",
        "xp": "XP",
        "free": "free",
    }[source]


def _pick_sphere(rng: SeededRng, profile: Any) -> str:
    spheres = [s["id"] for s in sphere_defs()]
    weights = [profile.skill_biases.get("persuasion", 1.0)] * len(spheres)
    social_bias = getattr(profile, "weights", {}).get("social_attrs", 1.0)
    for i, sphere in enumerate(spheres):
        if sphere in ("high_society", "media", "political"):
            weights[i] *= social_bias
        if sphere in ("street", "underworld", "police"):
            weights[i] *= profile.weights.get("skills", 1.0)
    return rng.weighted_choice(spheres, weights)


def _procedural_name(rng: SeededRng, bg_type: str, sphere_id: str | None) -> str:
    templates = _NAME_TEMPLATES.get(bg_type, ["{label}"])
    label = background_label(bg_type)
    sphere = sphere_label(sphere_id) if sphere_id else label
    template = rng.choice(templates)
    return template.format(label=label, sphere=sphere)


def _pick_target_entry(
    rng: SeededRng,
    entries: list[dict[str, Any]],
    bg_type: str,
    spec: dict[str, Any],
    *,
    prefer_new_instance: bool = False,
) -> dict[str, Any] | None:
    typed = entries_for_type(entries, bg_type)
    max_dots = int(spec.get("max_dots", 3))
    if spec.get("purchase_mode") == "single_rating":
        if typed:
            return typed[0] if typed[0]["dots"] < max_dots else None
        return None
    stackable = [e for e in typed if e["dots"] < max_dots]
    if prefer_new_instance and _can_add_new_instance(entries, bg_type, spec):
        return None
    if stackable and (not prefer_new_instance or rng.uniform() < 0.35):
        return rng.choice(stackable)
    if _can_add_new_instance(entries, bg_type, spec):
        return None
    return rng.choice(stackable) if stackable else None


def _can_add_new_instance(entries: list[dict[str, Any]], bg_type: str, spec: dict[str, Any]) -> bool:
    typed = entries_for_type(entries, bg_type)
    max_instances = spec.get("max_instances")
    if max_instances is not None and len(typed) >= int(max_instances):
        return False
    if spec.get("purchase_mode") == "single_rating":
        return not typed
    return True


def _can_add_dot(
    entries: list[dict[str, Any]],
    bg_type: str,
    spec: dict[str, Any],
    char: dict[str, Any] | None = None,
) -> bool:
    if char is not None:
        from wod_chargen.games.lotn_v5.merits_flaws import (
            background_connection_blocked,
            max_haven_connection_dots_allowed,
        )

        if background_connection_blocked(char, bg_type):
            return False
        if bg_type == "haven":
            cap = max_haven_connection_dots_allowed(char)
            if cap is not None and total_background_dots(entries_for_type(entries, "haven")) >= cap:
                return False

    max_dots = int(spec.get("max_dots", 3))
    typed = entries_for_type(entries, bg_type)
    if spec.get("purchase_mode") == "single_rating":
        if not typed:
            return True
        return typed[0]["dots"] < max_dots
    if any(e["dots"] < max_dots for e in typed):
        return True
    return _can_add_new_instance(entries, bg_type, spec)


def _new_entry(rng: SeededRng, bg_type: str, spec: dict[str, Any], profile: Any) -> dict[str, Any]:
    sphere_id = _pick_sphere(rng, profile) if spec.get("requires_sphere") else None
    return {
        "type": bg_type,
        "dots": 0,
        "sphere": sphere_id,
        "name": _procedural_name(rng, bg_type, sphere_id),
        "advantages": [],
        "disadvantages": [],
    }


def grant_background_rating(
    rng: SeededRng,
    entries: list[dict[str, Any]],
    bg_type: str,
    dots: int,
    profile: Any,
    *,
    sphere: str | None = None,
    name: str | None = None,
    from_predator: bool = False,
    char: dict[str, Any] | None = None,
) -> str | None:
    """Grant background dots from predator packages (outside creation pool)."""
    if dots <= 0:
        return None
    spec = background_defs().get(bg_type)
    if not spec:
        return None
    if char is not None:
        from wod_chargen.games.lotn_v5.merits_flaws import (
            background_connection_blocked,
            max_haven_connection_dots_allowed,
        )

        if background_connection_blocked(char, bg_type):
            return None
        if bg_type == "haven":
            cap = max_haven_connection_dots_allowed(char)
            if cap is not None and total_background_dots(entries_for_type(entries, "haven")) >= cap:
                return None
    max_dots = int(spec.get("max_dots", 3))
    typed = entries_for_type(entries, bg_type)

    if spec.get("purchase_mode") == "multi_instance" and _can_add_new_instance(entries, bg_type, spec):
        grant = min(dots, max_dots)
        sphere_id = sphere
        if sphere_id is None and spec.get("requires_sphere"):
            sphere_id = _pick_sphere(rng, profile)
        entry = {
            "type": bg_type,
            "dots": grant,
            "sphere": sphere_id,
            "name": name or _procedural_name(rng, bg_type, sphere_id),
            "advantages": [],
            "disadvantages": [],
        }
        if from_predator:
            entry["from_predator"] = True
        entries.append(entry)
        sphere_txt = f" ({sphere_label(sphere_id)})" if sphere_id else ""
        return (
            f"Predator: {background_label(bg_type)}{sphere_txt} → {grant} "
            f"({level_label(bg_type, grant)})"
        )

    entry = typed[0] if typed else None
    if entry is None:
        sphere_id = sphere
        if sphere_id is None and spec.get("requires_sphere"):
            sphere_id = _pick_sphere(rng, profile)
        entry = {
            "type": bg_type,
            "dots": 0,
            "sphere": sphere_id,
            "name": name or _procedural_name(rng, bg_type, sphere_id),
            "advantages": [],
            "disadvantages": [],
        }
        if from_predator:
            entry["from_predator"] = True
        entries.append(entry)

    before = int(entry["dots"])
    entry["dots"] = min(max_dots, before + dots)
    added = entry["dots"] - before
    if added <= 0:
        return None
    if from_predator:
        entry["from_predator"] = True
    sphere_txt = f" ({sphere_label(entry['sphere'])})" if entry.get("sphere") else ""
    name_txt = entry_display_name(entry)
    return (
        f"Predator: {background_label(bg_type)} {name_txt}{sphere_txt} +{added} "
        f"→ {entry['dots']} ({level_label(bg_type, entry['dots'])})"
    )


def _assign_one_background_dot(
    rng: SeededRng,
    entries: list[dict[str, Any]],
    profile: Any,
    *,
    biases: dict[str, float] | None = None,
    prefer_new_instance: bool = True,
    char: dict[str, Any] | None = None,
) -> str | None:
    defs = background_defs()
    eligible_types = [t for t in defs if _can_add_dot(entries, t, defs[t], char)]
    if not eligible_types:
        return None
    weights = [defs[t].get("creation_bias", 1.0) * (biases or {}).get(t, 1.0) for t in eligible_types]
    bg_type = rng.weighted_choice(eligible_types, weights)
    spec = defs[bg_type]
    entry = _pick_target_entry(rng, entries, bg_type, spec, prefer_new_instance=prefer_new_instance)
    if entry is None:
        entry = _new_entry(rng, bg_type, spec, profile)
        entries.append(entry)
    entry["dots"] += 1
    lvl = level_label(bg_type, entry["dots"])
    sphere = f" ({sphere_label(entry['sphere'])})" if entry.get("sphere") else ""
    name = entry_display_name(entry)
    return f"Background {name}{sphere} +1 → {entry['dots']} ({lvl}) [creation pool]"


def _assign_one_modifier_dot(
    rng: SeededRng,
    entries: list[dict[str, Any]],
    kind: ModifierKind,
    *,
    source: ModifierSource,
    only_entries: list[dict[str, Any]] | None = None,
    char: dict[str, Any] | None = None,
) -> tuple[str, dict[str, Any], str, int] | None:
    """Apply one modifier dot; optionally restrict to a subset of background entries."""
    if only_entries is not None:
        targets: list[tuple[dict[str, Any], dict[str, Any]]] = []
        for entry in only_entries:
            if int(entry.get("dots", 0)) <= 0:
                continue
            spec = background_defs().get(entry["type"], {})
            for mod_def in spec.get(_MODIFIER_KEY[kind], []):
                if can_add_modifier_dot(entry, mod_def, kind, char):
                    targets.append((entry, mod_def))
    else:
        targets = _eligible_modifier_targets(entries, kind, char)
    if not targets:
        return None
    entry, mod_def = rng.choice(targets)
    mod_id = mod_def["id"]
    new_level = apply_modifier_purchase(entry, mod_id, kind)
    label = mod_def["label"]
    name = entry_display_name(entry)
    if kind == "advantage":
        prefix = "Background modifier"
    else:
        prefix = "Background disadvantage"
    line = f"{prefix} {label} on {name} +1 → {new_level} [{_source_tag(source)}]"
    return line, entry, mod_id, new_level


def validate_creation_modifier_accounting(
    entries: list[dict[str, Any]],
    ledger: BackgroundCreationLedger,
) -> None:
    """Every creation-time modifier advantage must be pool- or disadv-trade funded."""
    total_adv = total_modifier_dots(entries, "advantage")
    expected = ledger.pool_spent_modifier + ledger.adv_from_disadv_granted
    if total_adv != expected:
        raise ValueError(
            f"Background modifier accounting mismatch: {total_adv} adv dots on sheet, "
            f"expected {expected} (pool={ledger.pool_spent_modifier}, "
            f"disadv trade={ledger.adv_from_disadv_granted})"
        )
    if ledger.adv_from_disadv_granted > ledger.disadv_trade_credit():
        raise ValueError("More advantage dots from disadv trade than disadv dots allow")
    if ledger.pool_spent > ledger.pool_total:
        raise ValueError("Creation pool overspent")


def validate_full_modifier_accounting(
    entries: list[dict[str, Any]],
    meta: dict[str, Any],
) -> None:
    """Creation + XP modifier advantages must balance against recorded sources."""
    ledger = BackgroundCreationLedger.from_meta(meta)
    total_adv = total_modifier_dots(entries, "advantage")
    predator_adv = int(meta.get("predator_modifier_dots", 0))
    xp_disadv_trade = int(meta.get("xp_adv_from_disadv_trade", 0))
    expected = (
        ledger.pool_spent_modifier
        + ledger.adv_from_disadv_granted
        + ledger.xp_spent_modifier
        + xp_disadv_trade
        + predator_adv
    )
    if total_adv != expected:
        raise ValueError(
            f"Full modifier accounting mismatch: {total_adv} adv dots, expected {expected}"
        )


def record_xp_modifier_purchase(meta: dict[str, Any], *, dots: int = 1) -> None:
    meta["xp_spent_modifier"] = int(meta.get("xp_spent_modifier", 0)) + dots


def record_xp_disadvantage_purchase(meta: dict[str, Any], *, dots: int = 1) -> None:
    meta["xp_disadvantage_dots"] = int(meta.get("xp_disadvantage_dots", 0)) + dots


def record_xp_disadv_trade_advantage(meta: dict[str, Any], *, dots: int = 1) -> None:
    meta["xp_adv_from_disadv_trade"] = int(meta.get("xp_adv_from_disadv_trade", 0)) + dots


def xp_disadv_trade_remaining(meta: dict[str, Any]) -> int:
    credit = int(meta.get("xp_disadvantage_dots", 0))
    spent = int(meta.get("xp_adv_from_disadv_trade", 0))
    return max(0, credit - spent)


def modifier_xp_item_bias(entry: dict[str, Any], kind: ModifierKind) -> float:
    """Favor bare entries and predator-granted backgrounds for modifier XP."""
    bias = 1.0
    adv_dots = total_modifier_dots([entry], "advantage")
    dis_dots = total_modifier_dots([entry], "disadvantage")
    if kind == "advantage" and adv_dots == 0:
        bias *= 2.0
    if kind == "disadvantage" and dis_dots == 0:
        bias *= 2.5
    if entry.get("from_predator"):
        bias *= 1.35
    return bias


def run_background_creation(
    rng: SeededRng,
    entries: list[dict[str, Any]],
    pool_dots: int,
    profile: Any,
    *,
    biases: dict[str, float] | None = None,
    predator_disadvantages_grant_adv: bool = True,
    char: dict[str, Any] | None = None,
) -> tuple[list[str], BackgroundCreationLedger]:
    """Creation pool, free disadvantages, and disadv-matched modifier advantages."""
    lines: list[str] = []
    ledger = BackgroundCreationLedger(pool_total=pool_dots)

    while ledger.pool_remaining > 0:
        can_bg = any(_can_add_dot(entries, t, background_defs()[t], char) for t in background_defs())
        can_mod = bool(_eligible_modifier_targets(entries, "advantage", char))
        spent = False

        if not can_bg and not can_mod:
            lines.append(
                f"Creation pool +1 unplaced ({ledger.pool_remaining} remaining, no open slots)"
            )
            ledger.pool_unplaced += 1
            continue

        bg_dots = total_background_dots(entries)
        mod_weight = 0.12 if bg_dots < 2 else 0.28 if bg_dots < 5 else 0.35
        pick_mod = can_mod and (not can_bg or rng.uniform() < mod_weight)

        if pick_mod:
            result = _assign_one_modifier_dot(
                rng, entries, "advantage", source="creation_pool", char=char
            )
            if result:
                lines.append(result[0])
                ledger.pool_spent_modifier += 1
                spent = True

        if not spent:
            line = _assign_one_background_dot(rng, entries, profile, biases=biases, char=char)
            if line:
                lines.append(line)
                ledger.pool_spent_connection += 1
                spent = True

        if not spent:
            lines.append(
                f"Creation pool +1 unplaced ({ledger.pool_remaining} remaining, no open slots)"
            )
            ledger.pool_unplaced += 1

    rated = [e for e in entries if int(e.get("dots", 0)) > 0]
    if rated and rng.uniform() < 0.7:
        disad_attempts = rng.choice([1, 1, 2, 2, 3])
        for _ in range(disad_attempts):
            result = _assign_one_modifier_dot(rng, entries, "disadvantage", source="free", char=char)
            if result:
                lines.append(result[0])
                ledger.disadv_dots_added += 1
            else:
                break

    grant = ledger.disadv_trade_credit(grant=predator_disadvantages_grant_adv)
    while ledger.disadv_trade_remaining > 0 and grant > 0:
        result = _assign_one_modifier_dot(rng, entries, "advantage", source="disadv_trade", char=char)
        if result:
            lines.append(result[0])
            ledger.adv_from_disadv_granted += 1
        else:
            lines.append("Background modifier +1 unplaced (disadvantage trade, no eligible targets)")
            break

    validate_creation_modifier_accounting(entries, ledger)
    return lines, ledger


def assign_background_dots(
    rng: SeededRng,
    entries: list[dict[str, Any]],
    count: int,
    profile: Any,
    *,
    biases: dict[str, float] | None = None,
) -> list[str]:
    """Assign creation dots as connection ratings only (testing helper)."""
    lines: list[str] = []
    for _ in range(count):
        line = _assign_one_background_dot(rng, entries, profile, biases=biases)
        lines.append(line or "Background +1 unplaced (no open slots)")
    return lines


def apply_background_purchase(
    entries: list[dict[str, Any]],
    bg_type: str,
    rng: SeededRng,
    profile: Any,
    *,
    mark_xp: bool = False,
) -> tuple[dict[str, Any], int]:
    """Raise an existing entry or add a new one. Returns (entry, new_dot_level)."""
    spec = background_defs()[bg_type]
    entry = _pick_target_entry(rng, entries, bg_type, spec)
    if entry is None:
        entry = _new_entry(rng, bg_type, spec, profile)
        entries.append(entry)
    entry["dots"] += 1
    if mark_xp:
        entry["xp_purchased"] = True
    return entry, entry["dots"]


def apply_xp_background_disadv_trade(
    rng: SeededRng,
    entries: list[dict[str, Any]],
    meta: dict[str, Any],
) -> list[tuple[str, str, int, str]]:
    """After XP spend: free disadv + matching adv on backgrounds bought with XP only."""
    xp_entries = [e for e in entries if e.get("xp_purchased") and int(e.get("dots", 0)) > 0]
    if not xp_entries or rng.uniform() >= 0.7:
        return []

    log: list[tuple[str, str, int, str]] = []
    for _ in range(rng.choice([1, 1, 2])):
        result = _assign_one_modifier_dot(
            rng, entries, "disadvantage", source="free", only_entries=xp_entries
        )
        if not result:
            break
        _line, entry, mod_id, new_level = result
        record_xp_disadvantage_purchase(meta)
        log.append(
            (modifier_item_key(entry, mod_id, "disadvantage"), "background_disadvantage", new_level, "free")
        )

    while xp_disadv_trade_remaining(meta) > 0:
        result = _assign_one_modifier_dot(
            rng, entries, "advantage", source="disadv_trade", only_entries=xp_entries
        )
        if not result:
            break
        _line, entry, mod_id, new_level = result
        record_xp_disadv_trade_advantage(meta)
        log.append(
            (modifier_item_key(entry, mod_id, "advantage"), "background_modifier", new_level, "disadv_trade")
        )

    return log


def apply_modifier_purchase(
    entry: dict[str, Any],
    mod_id: str,
    kind: ModifierKind,
) -> int:
    spec = background_defs()[entry["type"]]
    mod_def = next(m for m in spec[_MODIFIER_KEY[kind]] if m["id"] == mod_id)
    if not can_add_modifier_dot(entry, mod_def, kind):
        raise ValueError(f"Cannot add {kind} {mod_id} on {entry_display_name(entry)}")
    new_level = get_modifier_rating(entry, mod_id, kind) + 1
    set_modifier_rating(entry, mod_id, kind, new_level)
    return new_level


def background_type_ids() -> list[str]:
    return list(background_defs().keys())


def enumerate_xp_background_types(char: dict[str, Any], max_rating: int) -> list[str]:
    """Background types that can still receive an XP dot purchase."""
    entries = char.get("backgrounds", [])
    available: list[str] = []
    for bg_type, spec in background_defs().items():
        if _can_add_dot(entries, bg_type, spec, char):
            cap = min(int(spec.get("max_dots", 3)), max_rating)
            typed = entries_for_type(entries, bg_type)
            if spec.get("purchase_mode") == "single_rating":
                cur = typed[0]["dots"] if typed else 0
                if cur < cap:
                    available.append(bg_type)
            else:
                if any(e["dots"] < cap for e in typed) or _can_add_dot(entries, bg_type, spec, char):
                    available.append(bg_type)
    return available


def enumerate_xp_modifier_purchases(
    char: dict[str, Any],
    *,
    kinds: tuple[ModifierKind, ...] = ("advantage", "disadvantage"),
    only_xp_purchased: bool = False,
) -> list[tuple[dict[str, Any], dict[str, Any], ModifierKind, int]]:
    """Return (entry, mod_def, kind, new_level) for purchasable modifier dots."""
    results: list[tuple[dict[str, Any], dict[str, Any], ModifierKind, int]] = []
    for entry in char.get("backgrounds", []):
        if int(entry.get("dots", 0)) <= 0:
            continue
        if only_xp_purchased and not entry.get("xp_purchased"):
            continue
        spec = background_defs().get(entry["type"], {})
        for kind in kinds:
            for mod_def in spec.get(_MODIFIER_KEY[kind], []):
                if not can_add_modifier_dot(entry, mod_def, kind, char):
                    continue
                cur = get_modifier_rating(entry, mod_def["id"], kind)
                results.append((entry, mod_def, kind, cur + 1))
    return results
