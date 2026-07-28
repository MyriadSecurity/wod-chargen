#!/usr/bin/env python3
"""Extract SPI character-sheet catalogs into seed JSON (no prose).

Reads merit-table / affinity-table from the MES SPI Google-Sheets export
(reference/spi/character_sheet.xlsx by default).

Usage:
    .venv/bin/python scripts/extract_spi_sheet_catalogs.py
    .venv/bin/python scripts/extract_spi_sheet_catalogs.py path/to/sheet.xlsx
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_XLSX = ROOT / "reference" / "spi" / "character_sheet.xlsx"
DEFAULT_OUT = ROOT / "reference" / "spi" / "extracted"

NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
REL_NS = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"

ATTR_RE = re.compile(
    r"\b(Intelligence|Wits|Resolve|Strength|Dexterity|Stamina|Presence|Manipulation|Composure)\s+(\d+)\b",
    re.I,
)
SKILL_RE = re.compile(
    r"\b(Academics|Computer|Crafts|Investigation|Medicine|Occult|Politics|Science|"
    r"Athletics|Brawl|Drive|Firearms|Larceny|Stealth|Survival|Weaponry|"
    r"Animal Ken|Empathy|Expression|Intimidation|Persuasion|Socialize|Streetwise|Subterfuge)\s+(\d+)\b",
    re.I,
)
AFFINITY_RE = re.compile(
    r"\b(Ghost|Spirit|Mage|Fae|Vampire|Changeling)\s+Affinity\s+(\d+)\b",
    re.I,
)
MERIT_DOT_RE = re.compile(r"^([A-Za-z][A-Za-z0-9'’\- ]+?)\s+(\d+)$")


def slug(text: str) -> str:
    text = text.replace("´", "'").replace("’", "'").lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_")


def _num(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _load_workbook(path: Path) -> tuple[dict[str, list[dict[str, str]]], list[str]]:
    """Return {sheet_name: [row_dicts keyed by column letter]} and shared strings."""
    with zipfile.ZipFile(path) as z:
        ss: list[str] = []
        if "xl/sharedStrings.xml" in z.namelist():
            root = ET.fromstring(z.read("xl/sharedStrings.xml"))
            for si in root.findall("m:si", NS):
                ss.append(
                    "".join(
                        t.text or ""
                        for t in si.iter("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t")
                    )
                )

        wb = ET.fromstring(z.read("xl/workbook.xml"))
        sheets_meta: list[tuple[str, str]] = []
        for sh in wb.findall("m:sheets/m:sheet", NS):
            sheets_meta.append((sh.attrib["name"], sh.attrib[f"{REL_NS}id"]))
        rels = {
            rel.attrib["Id"]: rel.attrib["Target"]
            for rel in ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
        }

        def cell_val(c: ET.Element) -> str:
            t = c.attrib.get("t")
            v = c.find("m:v", NS)
            if v is None:
                return ""
            if t == "s":
                return ss[int(v.text or "0")]
            return v.text or ""

        out: dict[str, list[dict[str, str]]] = {}
        for name, rid in sheets_meta:
            target = rels[rid]
            if not target.startswith("worksheets/"):
                target = "worksheets/" + target.split("/")[-1]
            sheet = ET.fromstring(z.read("xl/" + target))
            rows: list[dict[str, str]] = []
            for row in sheet.findall("m:sheetData/m:row", NS):
                vals: dict[str, str] = {}
                for c in row.findall("m:c", NS):
                    col = re.match(r"[A-Z]+", c.attrib["r"])
                    if not col:
                        continue
                    val = cell_val(c).strip()
                    if val != "":
                        vals[col.group()] = val
                if vals:
                    rows.append(vals)
            out[name] = rows
        return out, ss


def parse_prereqs(text: str) -> list[dict[str, Any]]:
    """Best-effort structured prereqs; leftovers kept as raw for later tagging."""
    if not text or not text.strip():
        return []
    raw = text.strip()
    found: list[dict[str, Any]] = []
    used_spans: list[tuple[int, int]] = []

    def add(kind: str, trait: str, dots: int, start: int, end: int) -> None:
        found.append({"kind": kind, "id": slug(trait), "label": trait, "dots": dots})
        used_spans.append((start, end))

    for rx, kind in ((ATTR_RE, "attribute"), (SKILL_RE, "skill"), (AFFINITY_RE, "affinity")):
        for m in rx.finditer(raw):
            label = m.group(1)
            if kind == "affinity" and label.lower() == "changeling":
                label = "Fae"
            add(kind, label, int(m.group(2)), m.start(), m.end())

    # Merit tokens: "Name N" or bare "Name", split on commas / and
    remainder = raw
    for start, end in sorted(used_spans, reverse=True):
        remainder = remainder[:start] + " " + remainder[end:]
    for part in re.split(r"[,;]|\band\b", remainder, flags=re.I):
        part = part.strip()
        if not part or part.lower() in {"or", "a", "an", "the"}:
            continue
        if ATTR_RE.search(part) or SKILL_RE.search(part) or AFFINITY_RE.search(part):
            continue
        m = MERIT_DOT_RE.match(part)
        if m:
            found.append(
                {
                    "kind": "merit",
                    "id": slug(m.group(1)),
                    "label": m.group(1).strip(),
                    "dots": int(m.group(2)),
                    "unresolved": True,
                }
            )
            continue
        # Bare merit / specialty phrase (e.g. "Lucid Dreamer", "specialty in brawl…")
        if re.match(r"^[A-Za-z]", part) and len(part) < 80:
            found.append(
                {
                    "kind": "merit",
                    "id": slug(part),
                    "label": part,
                    "dots": 1,
                    "unresolved": True,
                }
            )

    return found


def extract_merits(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    # Columns from sheet: C=name D=category E=min F=max G=prereq H=Style? I.. style steps
    # N..R = per-dot markers; S/T flags
    out: list[dict[str, Any]] = []
    seen: Counter[str] = Counter()
    for row in rows[1:]:
        name = row.get("C", "").strip()
        if not name:
            continue
        base_id = slug(name)
        seen[base_id] += 1
        merit_id = base_id if seen[base_id] == 1 else f"{base_id}_{seen[base_id]}"
        category = row.get("D", "General").strip()
        dots_min = _num(row.get("E"))
        dots_max = _num(row.get("F")) or dots_min
        prereq_text = row.get("G", "").strip()
        style_steps = []
        if row.get("H", "").strip().lower() == "style":
            for col in ("I", "J", "K", "L", "M"):
                step = row.get(col, "").strip()
                if step:
                    style_steps.append(step)
        tags = [slug(category)] if category else []
        if style_steps:
            tags.append("fighting_style" if slug(category) == "fighting" else "style")
        entry: dict[str, Any] = {
            "id": merit_id,
            "label": name,
            "category": "general",
            "sheet_category": category,
            "dots_min": dots_min or 1,
            "dots_max": dots_max or dots_min or 1,
            "prereq_text": prereq_text,
            "prereqs": parse_prereqs(prereq_text),
            "tags": tags,
        }
        if style_steps:
            entry["style_steps"] = style_steps
        out.append(entry)
    return out


def extract_affinity_powers(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    # A=name B=affinity C=cost_min_or_special D=cost_max E=...
    out: list[dict[str, Any]] = []
    seen: Counter[str] = Counter()
    for row in rows[1:]:
        name = row.get("A", "").strip()
        if not name:
            continue
        aff = row.get("B", "").strip()
        aff_id = slug(aff)
        base_id = slug(name)
        seen[base_id] += 1
        power_id = base_id if seen[base_id] == 1 else f"{base_id}_{seen[base_id]}"
        cost_raw = row.get("C", "").strip()
        special = cost_raw.lower() == "special"
        dots_min = None if special else _num(cost_raw)
        dots_max = None if special else (_num(row.get("D")) or dots_min)
        if special:
            # F/G sometimes hold special tier costs
            vals = [v for v in (_num(row.get("F")), _num(row.get("G")), _num(row.get("H")), _num(row.get("J"))) if v]
            if vals:
                dots_min, dots_max = min(vals), max(vals)
            else:
                dots_min, dots_max = 1, 1
        entry: dict[str, Any] = {
            "id": power_id,
            "label": name,
            "category": "affinity",
            "affinity_type": aff_id,
            "dots_min": dots_min or 1,
            "dots_max": dots_max or dots_min or 1,
            "cost_special": special,
            "prereq_text": "",
            "prereqs": [{"kind": "affinity", "id": aff_id, "label": aff, "dots": 1}],
            "tags": ["affinity_power", aff_id],
        }
        out.append(entry)
    return out


COD_ATTRIBUTES = {
    "mental": ["intelligence", "wits", "resolve"],
    "physical": ["strength", "dexterity", "stamina"],
    "social": ["presence", "manipulation", "composure"],
    "all": [
        "intelligence",
        "wits",
        "resolve",
        "strength",
        "dexterity",
        "stamina",
        "presence",
        "manipulation",
        "composure",
    ],
}

COD_SKILLS = {
    "mental": [
        "academics",
        "computer",
        "crafts",
        "investigation",
        "medicine",
        "occult",
        "politics",
        "science",
    ],
    "physical": [
        "athletics",
        "brawl",
        "drive",
        "firearms",
        "larceny",
        "stealth",
        "survival",
        "weaponry",
    ],
    "social": [
        "animal_ken",
        "empathy",
        "expression",
        "intimidation",
        "persuasion",
        "socialize",
        "streetwise",
        "subterfuge",
    ],
}

COD_SKILLS["all"] = COD_SKILLS["mental"] + COD_SKILLS["physical"] + COD_SKILLS["social"]

DIVISIONS = {
    "acquisitions": {
        "id": "acquisitions",
        "label": "Acquisitions",
        "summary": "Collecting things and information; leverage connections for goods and services.",
    },
    "adventure": {
        "id": "adventure",
        "label": "Adventure",
        "summary": "Going to interesting places and making it back alive.",
    },
    "defense": {
        "id": "defense",
        "label": "Defense",
        "summary": "Protecting people and fighting monsters.",
    },
    "health_and_welfare": {
        "id": "health_and_welfare",
        "label": "Health and Welfare",
        "summary": "Healing and helping people.",
    },
    "research_and_development": {
        "id": "research_and_development",
        "label": "Research and Development",
        "summary": "Using the supernatural for science and profit.",
    },
}

AFFINITY_TYPES = {
    "ghost": {
        "id": "ghost",
        "label": "Ghost",
        "fuel": "plasm",
        "place_merit": "cenote",
        "unseen_sense": "ghost",
        "sense_mode": "hear",
    },
    "spirit": {
        "id": "spirit",
        "label": "Spirit",
        "fuel": "essence",
        "place_merit": "locus",
        "unseen_sense": "werewolf",
        "sense_mode": "smell",
    },
    "mage": {
        "id": "mage",
        "label": "Mage",
        "fuel": "mana",
        "place_merit": "hallow",
        "unseen_sense": "mage",
        "sense_mode": "see",
    },
    "fae": {
        "id": "fae",
        "label": "Fae",
        "fuel": "glamour",
        "place_merit": "goblin_bounty",
        "unseen_sense": "changeling",
        "sense_mode": "feel",
    },
    "vampire": {
        "id": "vampire",
        "label": "Vampire",
        "fuel": "vitae_bonus",
        "place_merit": "feeding_grounds",
        "unseen_sense": "vampire",
        "sense_mode": "taste",
    },
}

CREATION = {
    "attributes": {"base_dots": 1, "primary": 5, "secondary": 4, "tertiary": 3},
    "skills": {"primary": 11, "secondary": 7, "tertiary": 4},
    "specialties": 3,
    "free_affinity_dots": 1,
    "merit_dots": 7,
    "max_affinity_merit_dots_at_creation": 3,
    "integrity_default": 7,
    "size_default": 5,
    "affinity_merit_dots_per_affinity_level": 3,
    "division_status_default": 1,
}

COSTS = {
    "affinity": {"kind": "flat_per_dot", "per_dot": 5},
    "attribute": {"kind": "flat_per_dot", "per_dot": 4},
    "skill": {"kind": "flat_per_dot", "per_dot": 2},
    "integrity": {"kind": "flat_per_dot", "per_dot": 2},
    "supernatural_resistance": {"kind": "flat_per_dot", "per_dot": 2},
    "specialty": {"kind": "flat", "amount": 1},
    "merit": {"kind": "flat_per_dot", "per_dot": 1},
    "willpower_dot_regain": {"kind": "flat", "amount": 1},
}

ADVANTAGES = {
    "health": "size + stamina",
    "speed": "5 + strength + dexterity",
    "willpower": "resolve + composure",
    "initiative": "dexterity + composure",
    "perception": "wits + composure",
    "defense": "min(wits, dexterity) + athletics",
    "clash_of_wills": "max_resistant_attribute + occult",
    "downtimes": "resolve + 1",
    "max_integrity": "11 - sum_top_two_affinities",
    "resistant_attributes": ["resolve", "stamina", "composure"],
}


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("xlsx", nargs="?", type=Path, default=DEFAULT_XLSX)
    parser.add_argument("-o", "--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    if not args.xlsx.is_file():
        print(f"Missing sheet: {args.xlsx}", file=sys.stderr)
        return 1

    sheets, _ = _load_workbook(args.xlsx)
    if "merit-table" not in sheets or "affinity-table" not in sheets:
        print("Workbook missing merit-table or affinity-table", file=sys.stderr)
        return 1

    general = extract_merits(sheets["merit-table"])
    affinity = extract_affinity_powers(sheets["affinity-table"])
    merits = {
        "source": str(args.xlsx.relative_to(ROOT)) if args.xlsx.is_relative_to(ROOT) else str(args.xlsx),
        "notes": "Extracted catalog only (ids, dots, prereq text). No power prose.",
        "merits": general + affinity,
    }

    args.out.mkdir(parents=True, exist_ok=True)
    write_json(args.out / "merits.json", merits)
    write_json(args.out / "attributes.json", COD_ATTRIBUTES)
    write_json(args.out / "skills.json", COD_SKILLS)
    write_json(args.out / "divisions.json", DIVISIONS)
    write_json(args.out / "affinity_types.json", AFFINITY_TYPES)
    write_json(args.out / "creation.json", CREATION)
    write_json(args.out / "costs.json", COSTS)
    write_json(args.out / "advantages.json", ADVANTAGES)

    by_cat = Counter(m["sheet_category"] for m in general)
    by_aff = Counter(m["affinity_type"] for m in affinity)
    parsed = sum(1 for m in general if m["prereqs"])
    print(f"Wrote extracts to {args.out}")
    print(f"  general merits: {len(general)} (prereqs parsed on {parsed})")
    print(f"  affinity powers: {len(affinity)}")
    print(f"  general by sheet_category: {dict(by_cat)}")
    print(f"  affinity by type: {dict(by_aff)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
