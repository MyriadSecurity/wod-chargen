#!/usr/bin/env python3
"""Validate SPI archetype subtypes and bias packs."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from wod_chargen.games.spi.archetypes import (  # noqa: E402
    BIAS_KEYS,
    clear_archetype_caches,
    effective_profile,
    load_manifest,
)
from wod_chargen.games.spi.trait_biases import BIAS_MAX, BIAS_MIN, load_trait_tags  # noqa: E402

DATA = ROOT / "wod_chargen/games/spi/data"
WARN_LOW = 0.15
WARN_HIGH = 2.5


def _merit_ids() -> set[str]:
    payload = json.loads((DATA / "merits.json").read_text(encoding="utf-8"))
    return {m["id"] for m in payload.get("merits", [])}


def _check_bias_block(
    block: dict[str, float],
    *,
    path: str,
    label: str,
    registry: set[str] | None,
    errors: list[str],
    warnings: list[str],
    allow_negative: bool = False,
) -> None:
    for key, val in (block or {}).items():
        if registry is not None and key not in registry:
            errors.append(f"{path}: unknown {label} key {key!r}")
        try:
            fval = float(val)
        except (TypeError, ValueError):
            errors.append(f"{path}: {label}[{key}] non-numeric {val!r}")
            continue
        if allow_negative:
            # deltas: soft range check
            if fval < -1.0 or fval > 1.5:
                warnings.append(f"{path}: {label}[{key}]={fval} unusual delta")
        else:
            if fval < BIAS_MIN or fval > BIAS_MAX:
                warnings.append(f"{path}: {label}[{key}]={fval} outside [{BIAS_MIN}, {BIAS_MAX}]")
            elif fval <= WARN_LOW or fval >= WARN_HIGH:
                warnings.append(f"{path}: {label}[{key}]={fval} extreme")


def main() -> int:
    clear_archetype_caches()
    errors: list[str] = []
    warnings: list[str] = []
    manifest = load_manifest()
    primaries = list(manifest.get("primaries") or [])
    subtypes = dict(manifest.get("subtypes") or {})
    merit_ids = _merit_ids()
    theme_tags = set((load_trait_tags().get("tags") or {}).keys())
    skills = set(json.loads((DATA / "skills.json").read_text())["all"])
    attrs = set(json.loads((DATA / "attributes.json").read_text())["all"])
    aff_types = set(json.loads((DATA / "affinity_types.json").read_text()).keys())

    registries = {
        "attribute_biases": attrs,
        "skill_biases": skills,
        "affinity_biases": aff_types,
        "merit_biases": merit_ids,
        "tag_affinities": theme_tags,
    }

    for aid in primaries:
        path = DATA / "archetypes" / f"{aid}.json"
        if not path.exists():
            errors.append(f"missing primary file {path}")
            continue
        primary = json.loads(path.read_text(encoding="utf-8"))
        for key in BIAS_KEYS:
            _check_bias_block(
                primary.get(key) or {},
                path=f"archetypes/{aid}.json",
                label=key,
                registry=registries[key],
                errors=errors,
                warnings=warnings,
            )

        subs = list(subtypes.get(aid) or [])
        if len(subs) < 2:
            errors.append(f"{aid}: need ≥2 subtypes in manifest, found {len(subs)}")
        for sid in subs:
            spath = DATA / "archetypes" / aid / f"{sid}.json"
            if not spath.exists():
                errors.append(f"missing subtype file {spath.relative_to(DATA)}")
                continue
            raw = json.loads(spath.read_text(encoding="utf-8"))
            if raw.get("id") != sid:
                errors.append(f"{spath.relative_to(DATA)}: id {raw.get('id')!r} != {sid!r}")
            if not raw.get("label"):
                errors.append(f"{spath.relative_to(DATA)}: missing label")
            mods = raw.get("modifiers") or {}
            if not mods:
                errors.append(f"{spath.relative_to(DATA)}: empty modifiers")
            for key in BIAS_KEYS:
                _check_bias_block(
                    mods.get(key) or {},
                    path=str(spath.relative_to(DATA)),
                    label=f"modifiers.{key}",
                    registry=registries[key],
                    errors=errors,
                    warnings=warnings,
                    allow_negative=True,
                )
            # merge smoke
            try:
                effective_profile(aid, sid)
            except Exception as exc:
                errors.append(f"{aid}/{sid}: effective_profile failed: {exc}")

    for aid, subs in subtypes.items():
        if aid not in primaries:
            errors.append(f"manifest subtypes key {aid!r} not in primaries")

    for w in warnings:
        print(f"WARN: {w}")
    for e in errors:
        print(f"ERROR: {e}")
    print(
        f"SPI archetype subtype validation: {len(errors)} error(s), {len(warnings)} warning(s); "
        f"{len(primaries)} primaries"
    )
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
