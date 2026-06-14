"""Loresheet catalog, eligibility, and procedural weight resolution."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from wod_chargen.core.data_loader import load_json_cached
from wod_chargen.games.lotn_v5.trait_biases import resolve_trait_bias

from wod_chargen.games.lotn_v5.paths import DATA_PKG as DATA

INELIGIBLE = 0.05


@lru_cache(maxsize=1)
def load_loresheets() -> dict[str, Any]:
    return load_json_cached(DATA, "loresheets.json")


@lru_cache(maxsize=1)
def load_loresheet_themes() -> dict[str, Any]:
    return load_json_cached(DATA, "loresheet_themes.json")


@lru_cache(maxsize=1)
def load_loresheet_packages() -> dict[str, Any]:
    return load_json_cached(DATA, "loresheet_packages.json")


@lru_cache(maxsize=1)
def loresheet_by_id() -> dict[str, dict[str, Any]]:
    data = load_loresheets()
    return {ls["id"]: ls for ls in data["loresheets"]}


def loresheet_ids() -> frozenset[str]:
    return frozenset(loresheet_by_id().keys())


def active_loresheet_id(char: dict[str, Any]) -> str | None:
    """Return the single chosen loresheet id, if any."""
    sheets = char.get("loresheets") or {}
    if not sheets:
        return None
    if len(sheets) > 1:
        # Prefer highest total dots if legacy data had multiple keys
        return max(sheets.items(), key=lambda kv: kv[1])[0]
    return next(iter(sheets))


def active_loresheet_dots(char: dict[str, Any]) -> int:
    ls_id = active_loresheet_id(char)
    if not ls_id:
        return 0
    return int((char.get("loresheets") or {}).get(ls_id, 0))


def _char_clan(char: dict[str, Any]) -> str | None:
    return char.get("clan") or char.get("domitor_clan")


def is_loresheet_eligible(ls_id: str, char: dict[str, Any], *, sect: str | None = None) -> bool:
    """Hard eligibility: clan restrictions and one-loresheet rule."""
    spec = loresheet_by_id().get(ls_id)
    if spec is None:
        return False

    active = active_loresheet_id(char)
    if active and active != ls_id:
        return False

    restriction_clan = spec.get("restriction_clan")
    if restriction_clan:
        clan = _char_clan(char)
        if clan != restriction_clan:
            return False

    restriction_sect = spec.get("restriction_sect")
    if restriction_sect and sect:
        if sect != restriction_sect:
            return False

    return True


def resolve_loresheet_bias(
    ls_id: str,
    profile: Any,
    char: dict[str, Any],
    *,
    sect: str | None = None,
) -> float:
    """Combined archetype × clan bias for a loresheet pick."""
    if not is_loresheet_eligible(ls_id, char, sect=sect):
        return INELIGIBLE

    theme = resolve_trait_bias(profile, ls_id, "loresheets")
    clan = _char_clan(char)
    clan_bias = 1.0
    if clan:
        clans = load_json_cached(DATA, "clans.json")
        clan_bias = float(clans.get(clan, {}).get("loresheet_biases", {}).get(ls_id, 1.0))

    from wod_chargen.games.lotn_v5.trait_biases import BIAS_MAX, BIAS_MIN

    return max(BIAS_MIN, min(BIAS_MAX, theme * clan_bias))


def enumerate_loresheet_purchases(
    char: dict[str, Any],
    profile: Any,
    *,
    sect: str | None = None,
) -> list[tuple[str, int]]:
    """Return (loresheet_id, new_dot_level) pairs available for XP spend."""
    data = load_loresheets()
    max_dots = int(data.get("rules", {}).get("max_dots", 3))
    active = active_loresheet_id(char)
    cur_dots = active_loresheet_dots(char)

    if cur_dots >= max_dots:
        return []

    new_level = cur_dots + 1
    if active:
        if is_loresheet_eligible(active, char, sect=sect):
            return [(active, new_level)]
        return []

    out: list[tuple[str, int]] = []
    for ls_id in sorted(loresheet_by_id()):
        if is_loresheet_eligible(ls_id, char, sect=sect):
            out.append((ls_id, 1))
    return out


def level_narratives(ls_id: str, dots: int) -> list[dict[str, str]]:
    spec = loresheet_by_id().get(ls_id)
    if not spec or dots <= 0:
        return []
    out: list[dict[str, str]] = []
    for level in spec.get("levels", []):
        if int(level["dots"]) > dots:
            continue
        narrative = level.get("narrative")
        if narrative:
            out.append({"id": level["id"], "label": level["label"], "narrative": narrative})
    return out


def apply_loresheet_benefits(
    char: dict[str, Any],
    rng: Any,
    profile: Any,
    *,
    caps: dict[str, int],
) -> list[str]:
    """Apply mechanical packages for all purchased loresheet levels."""
    from wod_chargen.games.lotn_v5.benefit_packages import apply_benefit_package

    ls_id = active_loresheet_id(char)
    dots = active_loresheet_dots(char)
    if not ls_id or dots <= 0:
        return []

    packages = load_loresheet_packages().get("packages", {})
    spec = loresheet_by_id()[ls_id]
    lines: list[str] = []
    narratives: list[dict[str, str]] = []

    for level in spec.get("levels", []):
        if int(level["dots"]) > dots:
            continue
        key = f"{ls_id}/{level['id']}"
        package = packages.get(key)
        if package:
            lines.extend(
                apply_benefit_package(
                    package,
                    char,
                    rng,
                    profile,
                    caps=caps,
                    log_prefix="Loresheet",
                )
            )
        narrative = level.get("narrative")
        if narrative:
            narratives.append(
                {"id": level["id"], "label": level["label"], "narrative": narrative}
            )

    if lines or narratives:
        char["loresheet_meta"] = {
            "id": ls_id,
            "label": spec["label"],
            "dots": dots,
            "narratives": narratives,
            "package_applied": bool(lines),
        }
    return lines
