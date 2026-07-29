"""SPI character sheet view-model."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from wod_chargen.core.data_loader import load_json_cached
from wod_chargen.core.models import GenerationResult
from wod_chargen.games.spi.archetypes import get_archetype
from wod_chargen.games.spi.paths import DATA_PKG


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
    description: str | None = None


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
    meta: tuple[MetaItem, ...] = ()


@dataclass(frozen=True)
class RatedTraitsSection:
    title: str
    stats: tuple[StatLine, ...]


@dataclass(frozen=True)
class SpiSheetModel:
    header: SheetHeader
    attributes: TraitPanel
    skills: TraitPanel
    specialties: tuple[str, ...]
    affinities: RatedTraitsSection
    merits_general: RatedTraitsSection
    merits_affinity: RatedTraitsSection
    advantages: tuple[MetaItem, ...]


def _panel(title: str, columns_meta: dict[str, list[str]], ratings: dict[str, int]) -> TraitPanel:
    cols = []
    for cat, traits in columns_meta.items():
        if cat == "all":
            continue
        stats = tuple(
            StatLine(label=_title(t), dots=DotRow(value=int(ratings.get(t, 0)))) for t in traits
        )
        cols.append(TraitColumn(title=_title(cat), stats=stats))
    return TraitPanel(title=title, columns=tuple(cols))


def build_sheet_model(result: GenerationResult) -> SpiSheetModel:
    char = result.character
    attrs_meta = load_json_cached(DATA_PKG, "attributes.json")
    skills_meta = load_json_cached(DATA_PKG, "skills.json")
    divisions = load_json_cached(DATA_PKG, "divisions.json")
    factions = load_json_cached(DATA_PKG, "factions.json")
    merits_payload = load_json_cached(DATA_PKG, "merits.json")
    merit_by_id = {m["id"]: m for m in merits_payload.get("merits", [])}
    merit_descriptions = load_json_cached(DATA_PKG, "merit_descriptions.json").get(
        "descriptions", {}
    )

    division = divisions.get(char.get("division", ""), {})
    faction = factions.get(char.get("faction", ""), {})
    arch_id = str(char.get("archetype", ""))
    sub_id = str(char.get("sub_archetype", ""))
    arch_label = _title(arch_id)
    sub_label = _title(sub_id)
    try:
        arch = get_archetype(arch_id) if arch_id else {}
        arch_label = str(arch.get("label", arch_label))
        for s in arch.get("sub_archetypes") or []:
            if s["id"] == sub_id:
                sub_label = str(s.get("label", sub_label))
                break
    except Exception:
        pass
    aff_summary = ", ".join(
        f"{_title(k)} {v}" for k, v in char.get("affinities", {}).items() if int(v) > 0
    ) or "—"

    header = SheetHeader(
        meta=(
            MetaItem("Division", str(division.get("label", char.get("division", "")))),
            MetaItem("Faction", str(faction.get("label", char.get("faction", "")))),
            MetaItem("Archetype", arch_label),
            MetaItem("Subtype", sub_label),
            MetaItem("Affinity", aff_summary),
            MetaItem("Virtue", str(char.get("virtue", ""))),
            MetaItem("Vice", str(char.get("vice", ""))),
            MetaItem("Status", str(char.get("division_status", 1))),
        )
    )

    general_stats = []
    affinity_stats = []
    for mid, dots in sorted(char.get("merits", {}).items()):
        m = merit_by_id.get(mid, {})
        label = str(m.get("label", _title(mid)))
        if m.get("category") == "affinity":
            aff_type = m.get("affinity_type")
            if aff_type:
                label = f"{label} ({_title(str(aff_type))})"
        blurb = merit_descriptions.get(mid) or m.get("description")
        blurb_s = str(blurb).strip() if blurb else None
        line = StatLine(
            label=label,
            dots=DotRow(value=int(dots), max_dots=int(m.get("dots_max", 5))),
            description=blurb_s or None,
        )
        if m.get("category") == "affinity":
            affinity_stats.append(line)
        else:
            general_stats.append(line)

    adv = char.get("advantages", {})
    advantages = tuple(
        MetaItem(_title(k), str(v))
        for k, v in (
            ("health", adv.get("health")),
            ("willpower", adv.get("willpower")),
            ("integrity", char.get("integrity")),
            ("max_integrity", adv.get("max_integrity")),
            ("speed", adv.get("speed")),
            ("initiative", adv.get("initiative")),
            ("perception", adv.get("perception")),
            ("defense", adv.get("defense")),
            ("clash_of_wills", adv.get("clash_of_wills")),
            ("downtimes", adv.get("downtimes")),
        )
        if v is not None
    )

    return SpiSheetModel(
        header=header,
        attributes=_panel(
            "Attributes",
            {k: attrs_meta[k] for k in ("mental", "physical", "social")},
            char.get("attributes", {}),
        ),
        skills=_panel(
            "Skills",
            {k: skills_meta[k] for k in ("mental", "physical", "social")},
            char.get("skills", {}),
        ),
        specialties=tuple(char.get("specialties", [])),
        affinities=RatedTraitsSection(
            title="Affinities",
            stats=tuple(
                StatLine(label=_title(k), dots=DotRow(value=int(v)))
                for k, v in char.get("affinities", {}).items()
            ),
        ),
        merits_general=RatedTraitsSection(title="General Merits", stats=tuple(general_stats)),
        merits_affinity=RatedTraitsSection(title="Affinity Merits", stats=tuple(affinity_stats)),
        advantages=advantages,
    )
