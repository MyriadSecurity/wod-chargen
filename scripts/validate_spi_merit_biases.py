#!/usr/bin/env python3
"""Validate SPI merit theme tags and bias packs against registries."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from wod_chargen.games.spi.archetypes import list_archetypes  # noqa: E402
from wod_chargen.games.spi.trait_biases import BIAS_MAX, BIAS_MIN, load_trait_tags  # noqa: E402

DATA = ROOT / "wod_chargen/games/spi/data"
WARN_LOW = 0.15
WARN_HIGH = 2.5


def _check_block(
    block: dict[str, float],
    registry: set[str],
    label: str,
    path: str,
    errors: list[str],
    warnings: list[str],
    *,
    allow_empty_registry: bool = False,
) -> None:
    for key, val in (block or {}).items():
        if registry and key not in registry:
            errors.append(f"{path}: unknown {label} key {key!r}")
        elif not registry and not allow_empty_registry:
            errors.append(f"{path}: {label} key {key!r} but registry empty")
        try:
            fval = float(val)
        except (TypeError, ValueError):
            errors.append(f"{path}: {label}[{key}] non-numeric {val!r}")
            continue
        if fval < BIAS_MIN or fval > BIAS_MAX:
            warnings.append(f"{path}: {label}[{key}]={fval} outside [{BIAS_MIN}, {BIAS_MAX}]")
        elif fval <= WARN_LOW or fval >= WARN_HIGH:
            warnings.append(f"{path}: {label}[{key}]={fval} extreme")


def _load_merit_ids() -> set[str]:
    payload = json.loads((DATA / "merits.json").read_text(encoding="utf-8"))
    return {m["id"] for m in payload.get("merits", [])}


def _validate_pack(
    pack: dict[str, Any],
    path: str,
    merit_ids: set[str],
    theme_tags: set[str],
    errors: list[str],
    warnings: list[str],
) -> None:
    _check_block(pack.get("merit_biases") or {}, merit_ids, "merit_biases", path, errors, warnings)
    _check_block(
        pack.get("tag_affinities") or {},
        theme_tags,
        "tag_affinities",
        path,
        errors,
        warnings,
    )


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []
    merit_ids = _load_merit_ids()
    tags_data = load_trait_tags()
    theme_tags = set((tags_data.get("tags") or {}).keys())
    merit_themes: dict[str, Any] = tags_data.get("merits") or {}

    # Theme index coverage
    for mid in sorted(merit_ids):
        themes = merit_themes.get(mid)
        if not themes:
            errors.append(f"trait_tags.json: merit {mid!r} missing theme tags")
            continue
        if isinstance(themes, str):
            themes = [themes]
        if not themes:
            errors.append(f"trait_tags.json: merit {mid!r} has empty theme list")
            continue
        for tag in themes:
            base = tag.split(":", 1)[1] if tag.startswith(("opposed:", "hard_opposed:")) else tag
            if tag.startswith(("opposed:", "hard_opposed:")):
                if base not in theme_tags:
                    errors.append(f"trait_tags.json: merit {mid!r} unknown opposed theme {base!r}")
            elif tag not in theme_tags:
                errors.append(f"trait_tags.json: merit {mid!r} unknown theme {tag!r}")

    for mid in sorted(merit_themes):
        if mid not in merit_ids:
            errors.append(f"trait_tags.json: orphan merit id {mid!r}")

    for arch in list_archetypes():
        path = f"archetypes/{arch['id']}.json"
        _validate_pack(arch, path, merit_ids, theme_tags, errors, warnings)

    for name in ("divisions.json", "factions.json"):
        payload = json.loads((DATA / name).read_text(encoding="utf-8"))
        for eid, entry in payload.items():
            _validate_pack(entry, f"{name}[{eid}]", merit_ids, theme_tags, errors, warnings)

    for w in warnings:
        print(f"WARN: {w}")
    for e in errors:
        print(f"ERROR: {e}")

    print(
        f"SPI merit bias validation: {len(errors)} error(s), {len(warnings)} warning(s); "
        f"{len(merit_ids)} merits, {len(theme_tags)} theme tags"
    )
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
