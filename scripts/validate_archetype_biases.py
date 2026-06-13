#!/usr/bin/env python3
"""Validate archetype bias keys against registries and tag index."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from wod_chargen.games.lotn_v5.archetypes import (  # noqa: E402
    BIAS_MODIFIER_KEYS,
    _registry_ids,
    load_all_archetypes,
)
from wod_chargen.games.lotn_v5.trait_biases import load_trait_tags  # noqa: E402

BIAS_MIN = 0.05
BIAS_MAX = 3.0
WARN_LOW = 0.15
WARN_HIGH = 2.5


def _check_block(
    block: dict[str, float],
    registry: set[str],
    label: str,
    arch_path: str,
    errors: list[str],
    warnings: list[str],
) -> None:
    for key, val in block.items():
        if registry and key not in registry:
            errors.append(f"{arch_path}: unknown {label} key {key!r}")
        if val < BIAS_MIN or val > BIAS_MAX:
            warnings.append(f"{arch_path}: {label}[{key}]={val} outside [{BIAS_MIN}, {BIAS_MAX}]")
        elif val <= WARN_LOW or val >= WARN_HIGH:
            warnings.append(f"{arch_path}: {label}[{key}]={val} extreme")


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []
    registries = _registry_ids()
    tags = set(load_trait_tags().get("tags", {}).keys())

    manifest_path = ROOT / "wod_chargen/games/lotn_v5/data/archetypes/_manifest.json"
    manifest = json.loads(manifest_path.read_text())
    primaries = set(manifest["primaries"])

    for arch_id in primaries:
        raw = json.loads(
            (ROOT / f"wod_chargen/games/lotn_v5/data/archetypes/{arch_id}.json").read_text()
        )
        for key in BIAS_MODIFIER_KEYS:
            if key == "weights":
                continue
            registry = registries.get(key, tags if key == "tag_affinities" else set())
            _check_block(
                {k: float(v) for k, v in raw.get(key, {}).items()},
                registry,
                key,
                arch_id,
                errors,
                warnings,
            )
        for sub_id in manifest["subtypes"].get(arch_id, []):
            sub_raw = json.loads(
                (ROOT / f"wod_chargen/games/lotn_v5/data/archetypes/{arch_id}/{sub_id}.json").read_text()
            )
            mods = sub_raw.get("modifiers", {})
            for key in BIAS_MODIFIER_KEYS:
                if key == "weights":
                    continue
                registry = registries.get(key, tags if key == "tag_affinities" else set())
                _check_block(
                    {k: float(v) for k, v in mods.get(key, {}).items()},
                    registry,
                    key,
                    f"{arch_id}/{sub_id}",
                    errors,
                    warnings,
                )

    try:
        profiles = load_all_archetypes()
        if len(profiles) != len(primaries):
            errors.append(f"Loaded {len(profiles)} profiles, expected {len(primaries)}")
    except Exception as exc:
        errors.append(f"load_all_archetypes failed: {exc}")

    for w in warnings:
        print(f"WARN: {w}")
    for e in errors:
        print(f"ERROR: {e}")

    if errors:
        return 1
    print(f"OK: {len(primaries)} primaries validated ({len(warnings)} warnings)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
