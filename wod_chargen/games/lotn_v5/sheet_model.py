"""LoTN V5 character sheet view-model — labels resolved for rendering."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from wod_chargen.core.data_loader import load_json_cached
from wod_chargen.core.models import GenerationResult
from wod_chargen.games.lotn_v5.archetypes import get_archetype
from wod_chargen.games.lotn_v5.backgrounds import (
    background_defs,
    background_label,
    level_label,
    level_summary,
    modifier_max_dots,
    sphere_label,
)
from wod_chargen.games.lotn_v5.clan_symbols import clan_symbol_path
from wod_chargen.games.lotn_v5.disciplines import (
    discipline_power_ids_for_track,
    ghoul_domitor_discipline_pool,
    power_label,
)
from wod_chargen.games.lotn_v5.merits_flaws import trait_base_id, trait_def, trait_display_label
from wod_chargen.games.lotn_v5.paths import DATA_PKG as DATA
from wod_chargen.games.lotn_v5.thin_blood_merits import thin_blood_trait_label


def _title(key: str) -> str:
    return key.replace("_", " ").title()


@dataclass(frozen=True)
class DotRow:
    value: int
    max_dots: int = 5


@dataclass(frozen=True)
class StatLine:
    label: str
    dots: DotRow


@dataclass(frozen=True)
class TraitColumn:
    title: str
    stats: tuple[StatLine, ...]


@dataclass(frozen=True)
class TraitPanel:
    title: str
    columns: tuple[TraitColumn, ...]


@dataclass(frozen=True)
class MetaItem:
    label: str
    value: str


@dataclass(frozen=True)
class SheetHeader:
    clan_symbol_src: str | None = None
    clan_symbol_alt: str | None = None
    meta: tuple[MetaItem, ...] = ()


@dataclass(frozen=True)
class RatedTraitsSection:
    title: str
    stats: tuple[StatLine, ...]


@dataclass(frozen=True)
class DisciplineCard:
    name: str
    rating: DotRow
    powers: tuple[str, ...] = ()
    ghoul_powers: bool = False


@dataclass(frozen=True)
class DisciplinesSection:
    title: str
    cards: tuple[DisciplineCard, ...]


@dataclass(frozen=True)
class LoresheetSection:
    stats: tuple[StatLine, ...]
    notes: tuple[str, ...] = ()


@dataclass(frozen=True)
class BackgroundModifier:
    label: str
    dots: DotRow


@dataclass(frozen=True)
class BackgroundCard:
    type_label: str
    sphere_label: str | None
    dots: DotRow
    level_text: str
    advantages: tuple[BackgroundModifier, ...] = ()
    disadvantages: tuple[BackgroundModifier, ...] = ()


@dataclass(frozen=True)
class BackgroundsSection:
    cards: tuple[BackgroundCard, ...]


@dataclass(frozen=True)
class ConvictionsSection:
    items: tuple[str, ...]
    seed: int


@dataclass(frozen=True)
class NamedItemsSection:
    title: str
    items: tuple[str, ...]


@dataclass(frozen=True)
class SheetModel:
    header: SheetHeader
    convictions: ConvictionsSection | None = None
    attributes: TraitPanel | None = None
    skills: TraitPanel | None = None
    merits: RatedTraitsSection | None = None
    flaws: RatedTraitsSection | None = None
    thin_blood_merits: RatedTraitsSection | None = None
    thin_blood_flaws: RatedTraitsSection | None = None
    loresheet: LoresheetSection | None = None
    resonance_discipline: DisciplinesSection | None = None
    disciplines: DisciplinesSection | None = None
    rituals: NamedItemsSection | None = None
    ceremonies: NamedItemsSection | None = None
    formulas: NamedItemsSection | None = None
    specialties: tuple[str, ...] = ()
    backgrounds: BackgroundsSection | None = None


def _discipline_labels() -> dict[str, str]:
    catalog = load_json_cached(DATA, "discipline_powers.json")
    return {disc["id"]: disc["label"] for disc in catalog.get("disciplines", [])}


def _discipline_label(disc_id: str) -> str:
    return _discipline_labels().get(disc_id, _title(disc_id))


def _lookup_label(mapping: dict[str, Any], item_id: str | None) -> str:
    if not item_id:
        return "—"
    entry = mapping.get(item_id)
    if isinstance(entry, dict):
        return entry.get("label", _title(item_id))
    return _title(item_id)


def _stat_line(label: str, value: int, *, max_dots: int = 5) -> StatLine:
    return StatLine(label=label, dots=DotRow(value=value, max_dots=max_dots))


def _trait_panel(
    panel_title: str,
    categories: list[tuple[str, list[str]]],
    values: dict[str, int],
) -> TraitPanel:
    columns: list[TraitColumn] = []
    for category_title, trait_ids in categories:
        stats = tuple(_stat_line(_title(trait_id), values.get(trait_id, 0)) for trait_id in trait_ids)
        columns.append(TraitColumn(title=category_title, stats=stats))
    return TraitPanel(title=panel_title, columns=tuple(columns))


def _is_thin_blood_trait_key(trait_key: str, kind: str) -> bool:
    entry = trait_def(trait_base_id(trait_key), kind)  # type: ignore[arg-type]
    return bool(entry and entry.get("thin_blood_only"))


def _standard_traits(items: dict[str, int], kind: str) -> dict[str, int]:
    return {
        key: value
        for key, value in items.items()
        if value > 0 and not _is_thin_blood_trait_key(key, kind)
    }


def _rated_traits_section(title: str, items: dict[str, int], *, kind: str | None = None) -> RatedTraitsSection | None:
    rated = {k: v for k, v in items.items() if v > 0}
    if not rated:
        return None
    stats = tuple(
        _stat_line(
            trait_display_label(key, kind) if kind in ("merit", "flaw") else _title(key),
            value,
        )
        for key, value in sorted(rated.items())
    )
    return RatedTraitsSection(title=title, stats=stats)


def _thin_blood_traits_section(title: str, items: dict[str, int], *, kind: str) -> RatedTraitsSection | None:
    rated = {k: v for k, v in items.items() if v > 0}
    if not rated:
        return None
    stats = tuple(
        _stat_line(thin_blood_trait_label(key, kind), 1)  # type: ignore[arg-type]
        for key in sorted(rated)
    )
    return RatedTraitsSection(title=title, stats=stats)


def _disciplines_section(
    character: dict[str, Any],
    *,
    exclude: set[str] | None = None,
) -> DisciplinesSection | None:
    skip = exclude or set()
    is_ghoul = character.get("character_type") == "ghoul"
    discs = {k: v for k, v in character.get("disciplines", {}).items() if v > 0 and k not in skip}
    if not discs:
        return None
    picks = character.get("discipline_powers", {})
    dot_cap = 1 if is_ghoul else 5
    cards: list[DisciplineCard] = []
    for disc_id, rating in sorted(discs.items()):
        picks_for_disc = picks.get(disc_id, {})
        power_lines: list[str] = []
        ghoul_powers = False
        if is_ghoul:
            power_ids = discipline_power_ids_for_track(character, disc_id)
            if power_ids:
                ghoul_powers = True
                power_lines = [power_label(pid) for pid in power_ids]
        elif picks_for_disc:
            for level in sorted(picks_for_disc.keys(), key=lambda x: int(x) if x.isdigit() else 0):
                if level == "extra":
                    continue
                pid = picks_for_disc[level]
                power_lines.append(f"•{level} {power_label(pid)}")
        cards.append(
            DisciplineCard(
                name=_discipline_label(disc_id),
                rating=DotRow(value=int(rating), max_dots=dot_cap),
                powers=tuple(power_lines),
                ghoul_powers=ghoul_powers,
            )
        )
    return DisciplinesSection(
        title="Domitor Disciplines" if is_ghoul else "Disciplines",
        cards=tuple(cards),
    )


def _resonance_discipline_section(character: dict[str, Any]) -> DisciplinesSection | None:
    if character.get("character_type") != "thin_blood":
        return None
    disc_id = (character.get("discipline_meta") or {}).get("resonance_discipline")
    if not disc_id:
        return None
    rating = int((character.get("discipline_meta") or {}).get("resonance_rating", 1))
    picks = character.get("discipline_powers", {}).get(disc_id, {})
    level_one = picks.get("1")
    power_lines: list[str] = []
    if level_one:
        power_lines.append(f"•1 {power_label(level_one)}")
    return DisciplinesSection(
        title="Resonance Discipline",
        cards=(
            DisciplineCard(
                name=_discipline_label(disc_id),
                rating=DotRow(value=rating, max_dots=5),
                powers=tuple(power_lines),
            ),
        ),
    )


def _power_id_list_section(title: str, power_ids: list[str]) -> NamedItemsSection | None:
    if not power_ids:
        return None
    return NamedItemsSection(title=title, items=tuple(power_label(pid) for pid in sorted(power_ids)))


def _formula_section(character: dict[str, Any]) -> NamedItemsSection | None:
    formulas = {k: v for k, v in character.get("thin_blood_formulas", {}).items() if v > 0}
    if not formulas:
        return None
    return NamedItemsSection(
        title="Thin-Blood Formulas",
        items=tuple(power_label(fid) for fid in sorted(formulas.keys())),
    )


def _loresheet_section(character: dict[str, Any]) -> LoresheetSection | None:
    sheets = character.get("loresheets") or {}
    rated = {k: v for k, v in sheets.items() if int(v) > 0}
    if not rated:
        return None
    catalog = {
        ls["id"]: ls["label"]
        for ls in load_json_cached(DATA, "loresheets.json").get("loresheets", [])
    }
    stats = tuple(
        _stat_line(catalog.get(ls_id, _title(ls_id)), int(dots))
        for ls_id, dots in sorted(rated.items())
    )
    meta = character.get("loresheet_meta") or {}
    notes = tuple(
        f"{entry.get('label', entry.get('id', ''))}: {entry.get('narrative', '')}"
        for entry in (meta.get("narratives") or [])
    )
    return LoresheetSection(stats=stats, notes=notes)


def _modifier_list(items: list[Any], catalog: list[dict[str, Any]]) -> tuple[BackgroundModifier, ...]:
    catalog_by_id = {entry["id"]: entry for entry in catalog}
    out: list[BackgroundModifier] = []
    for raw in items:
        if isinstance(raw, dict):
            mod_id = raw.get("id", "")
            dots = int(raw.get("dots", 1))
        else:
            mod_id = str(raw)
            dots = 1
        mod_def = catalog_by_id.get(mod_id, {})
        label = mod_def.get("label", mod_id.replace("_", " ").title())
        max_dots = modifier_max_dots(mod_def) if mod_def else max(dots, 1)
        out.append(BackgroundModifier(label=label, dots=DotRow(value=dots, max_dots=max_dots)))
    return tuple(out)


def _background_section(entries: list[dict[str, Any]]) -> BackgroundsSection | None:
    rated = [e for e in entries if int(e.get("dots", 0)) > 0]
    if not rated:
        return None
    defs = background_defs()
    cards: list[BackgroundCard] = []
    for entry in rated:
        bg_type = entry.get("type", "")
        spec = defs.get(bg_type, {})
        dots = int(entry.get("dots", 0))
        cards.append(
            BackgroundCard(
                type_label=background_label(bg_type),
                sphere_label=sphere_label(entry["sphere"]) if entry.get("sphere") else None,
                dots=DotRow(value=dots, max_dots=int(spec.get("max_dots", 3))),
                level_text=f"{level_label(bg_type, dots)} — {level_summary(bg_type, dots)}",
                advantages=_modifier_list(entry.get("advantages", []), spec.get("advantages", [])),
                disadvantages=_modifier_list(entry.get("disadvantages", []), spec.get("disadvantages", [])),
            )
        )
    return BackgroundsSection(cards=tuple(cards))


def _build_header(character: dict[str, Any]) -> SheetHeader:
    clans = load_json_cached(DATA, "clans.json")
    types = load_json_cached(DATA, "character_types.json")
    predators = {t["id"]: t["label"] for t in load_json_cached(DATA, "predator_types.json")["types"]}

    ctype = character.get("character_type", "vampire")
    arch_id = character.get("archetype", "")
    sub_id = character.get("sub_archetype", "")
    arch = get_archetype(arch_id)
    sub = next((s for s in arch.sub_archetypes if s.id == sub_id), None)

    meta: list[MetaItem] = [
        MetaItem("Type", types.get(ctype, {}).get("label", _title(ctype))),
    ]
    if character.get("clan"):
        meta.append(MetaItem("Clan", _lookup_label(clans, character["clan"])))
    if character.get("domitor_clan"):
        meta.append(MetaItem("Domitor", _lookup_label(clans, character["domitor_clan"])))
    meta.append(MetaItem("Archetype", arch.label))
    if sub:
        meta.append(MetaItem("Subtype", sub.label))
    if character.get("predator"):
        meta.append(MetaItem("Predator", predators.get(character["predator"], _title(character["predator"]))))
    if ctype == "ghoul":
        domitor_pool = character.get("domitor_disciplines") or ghoul_domitor_discipline_pool(character)
        if domitor_pool:
            pool_text = ", ".join(_discipline_label(d) for d in domitor_pool)
            meta.append(MetaItem("Domitor pool", pool_text))
    elif ctype in ("vampire", "thin_blood"):
        meta.append(MetaItem("Generation", str(character.get("generation", "—"))))
        meta.append(MetaItem("Blood Potency", str(character.get("blood_potency", 0))))
    meta.append(MetaItem("Humanity", str(character.get("humanity", "—"))))

    clan_id = character.get("clan") or character.get("domitor_clan")
    symbol_src: str | None = None
    symbol_alt: str | None = None
    if clan_id and clan_id in clans:
        symbol_src = clans[clan_id].get("symbol", clan_symbol_path(clan_id))
        symbol_alt = clans[clan_id]["label"]

    return SheetHeader(clan_symbol_src=symbol_src, clan_symbol_alt=symbol_alt, meta=tuple(meta))


def build_sheet_model(
    result: GenerationResult,
    *,
    convictions: list[dict[str, str]] | None = None,
    convictions_seed: int | None = None,
) -> SheetModel:
    """Build a presentation-ready sheet model from a generation result."""
    character = result.character
    attrs = load_json_cached(DATA, "attributes.json")
    skills = load_json_cached(DATA, "skills.json")
    trait_categories = [
        ("Physical", "physical"),
        ("Social", "social"),
        ("Mental", "mental"),
    ]

    convictions_section: ConvictionsSection | None = None
    if convictions and convictions_seed is not None:
        convictions_section = ConvictionsSection(
            items=tuple(entry["text"] for entry in convictions),
            seed=convictions_seed,
        )

    resonance_id = (character.get("discipline_meta") or {}).get("resonance_discipline")
    disc_exclude = {resonance_id} if resonance_id else set()

    specialties = tuple(
        f"{_title(spec['skill'])} ({spec['name']})"
        for spec in character.get("specialties", [])
    )

    return SheetModel(
        header=_build_header(character),
        convictions=convictions_section,
        attributes=_trait_panel(
            "Attributes",
            [(label, attrs[cat_id]) for label, cat_id in trait_categories],
            character["attributes"],
        ),
        skills=_trait_panel(
            "Skills",
            [(label, skills[cat_id]) for label, cat_id in trait_categories],
            character["skills"],
        ),
        merits=_rated_traits_section("Merits", _standard_traits(character.get("merits", {}), "merit"), kind="merit"),
        flaws=_rated_traits_section("Flaws", _standard_traits(character.get("flaws", {}), "flaw"), kind="flaw"),
        thin_blood_merits=_thin_blood_traits_section(
            "Thin-Blood Merits",
            character.get("thin_blood_merits", {}),
            kind="merit",
        ),
        thin_blood_flaws=_thin_blood_traits_section(
            "Thin-Blood Flaws",
            character.get("thin_blood_flaws", {}),
            kind="flaw",
        ),
        loresheet=_loresheet_section(character),
        resonance_discipline=_resonance_discipline_section(character),
        disciplines=_disciplines_section(character, exclude=disc_exclude),
        rituals=_power_id_list_section("Rituals", character.get("rituals", [])),
        ceremonies=_power_id_list_section("Ceremonies", character.get("ceremonies", [])),
        formulas=_formula_section(character),
        specialties=specialties,
        backgrounds=_background_section(character.get("backgrounds", [])),
    )
