#!/usr/bin/env python3
"""Merge archetype_themes.json into primary and sub archetype JSON files."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "wod_chargen/games/lotn_v5/data"
THEMES_PATH = DATA / "archetype_themes.json"
ARCH = DATA / "archetypes"
DOCS = ROOT / "docs/archetype-weights"

PRIMARY_BIAS_KEYS = (
    "attribute_biases",
    "skill_biases",
    "discipline_biases",
    "merit_biases",
    "flaw_biases",
    "background_biases",
    "sphere_biases",
    "modifier_biases",
    "discipline_power_biases",
    "tag_affinities",
)


def _merge_dict(base: dict[str, float], patch: dict[str, float]) -> dict[str, float]:
    out = dict(base)
    for k, v in patch.items():
        out[k] = float(v)
    return out


def apply_primary(arch_id: str, theme: dict[str, Any]) -> None:
    path = ARCH / f"{arch_id}.json"
    data = json.loads(path.read_text())
    for key in PRIMARY_BIAS_KEYS:
        if key in theme:
            data[key] = _merge_dict(data.get(key, {}), theme[key])
    if "discipline_expressions" in theme:
        data["discipline_expressions"] = theme["discipline_expressions"]
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def apply_sub(arch_id: str, sub_id: str, theme: dict[str, Any]) -> None:
    path = ARCH / arch_id / f"{sub_id}.json"
    data = json.loads(path.read_text())
    mods = data.setdefault("modifiers", {})
    for key in PRIMARY_BIAS_KEYS:
        if key in theme:
            mods[key] = _merge_dict(mods.get(key, {}), theme[key])
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def write_doc(arch_id: str, theme: dict[str, Any], label: str) -> None:
    DOCS.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# {label} — thematic weights",
        "",
        theme.get("notes", f"Thematic bias profile for **{label}**."),
        "",
        "## Tag affinities",
        "",
    ]
    tags = theme.get("tag_affinities", {})
    if tags:
        for tag, val in sorted(tags.items(), key=lambda x: -x[1]):
            lines.append(f"- `{tag}`: {val}")
    else:
        lines.append("_None defined._")
    lines.extend(["", "## Top boosts", ""])
    for section, title in (
        ("skill_biases", "Skills"),
        ("discipline_biases", "Disciplines"),
        ("background_biases", "Backgrounds"),
        ("sphere_biases", "Spheres"),
        ("merit_biases", "Merits"),
    ):
        block = theme.get(section, {})
        if block:
            lines.append(f"### {title}")
            for k, v in sorted(block.items(), key=lambda x: -x[1])[:8]:
                lines.append(f"- `{k}`: {v}")
            lines.append("")
    lines.extend(["", "## Suppressions", ""])
    for section in PRIMARY_BIAS_KEYS:
        block = theme.get(section, {})
        low = {k: v for k, v in block.items() if v < 0.8}
        if low:
            for k, v in sorted(low.items(), key=lambda x: x[1]):
                lines.append(f"- `{section}` `{k}`: {v}")
    (DOCS / f"{arch_id}.md").write_text("\n".join(lines) + "\n")


def main() -> None:
    themes = json.loads(THEMES_PATH.read_text())
    manifest = json.loads((ARCH / "_manifest.json").read_text())
    for arch_id in manifest["primaries"]:
        block = themes["primaries"][arch_id]
        apply_primary(arch_id, block)
        write_doc(arch_id, block, block.get("label", arch_id))
        for sub_id in manifest["subtypes"].get(arch_id, []):
            sub_theme = block.get("subs", {}).get(sub_id, {})
            if sub_theme:
                apply_sub(arch_id, sub_id, sub_theme)
    print(f"Applied themes for {len(manifest['primaries'])} primaries")


if __name__ == "__main__":
    main()
