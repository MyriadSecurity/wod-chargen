#!/usr/bin/env python3
"""Validate archetype bias keys against registries and tag index."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from wod_chargen.core.data_loader import load_json_cached  # noqa: E402
from wod_chargen.games.lotn_v5.archetypes import (  # noqa: E402
    BIAS_MODIFIER_KEYS,
    _registry_ids,
    load_all_archetypes,
)
from wod_chargen.games.lotn_v5.trait_biases import load_trait_tags  # noqa: E402

DATA = ROOT / "wod_chargen/games/lotn_v5/data"

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


def _validate_discipline_expressions(
    expr: dict[str, Any],
    arch_path: str,
    disc_ids: set[str],
    power_ids: set[str],
    errors: list[str],
) -> None:
    if not expr:
        return
    for sig in expr.get("signature") or []:
        if sig not in disc_ids:
            errors.append(f"{arch_path}: discipline_expressions.signature unknown {sig!r}")
    alternates = expr.get("alternates") or {}
    for disc_id, spec in alternates.items():
        if disc_id not in disc_ids:
            errors.append(f"{arch_path}: discipline_expressions.alternates unknown disc {disc_id!r}")
        for pid in (spec.get("power_biases") or {}):
            if pid not in power_ids:
                errors.append(f"{arch_path}: discipline_expressions alternate unknown power {pid!r}")


def _validate_loresheet_bias_coverage(errors: list[str]) -> None:
    themes = json.loads((DATA / "loresheet_themes.json").read_text())
    theme_ids = set(themes["loresheets"])
    for arch_id in load_all_archetypes():
        raw = json.loads((DATA / "archetypes" / f"{arch_id}.json").read_text())
        bias_ids = set(raw.get("loresheet_biases", {}))
        if bias_ids != theme_ids:
            errors.append(f"{arch_id}: loresheet_biases keys mismatch theme catalog")

    clans = load_json_cached("wod_chargen.games.lotn_v5.data", "clans.json")
    for clan_id, clan in clans.items():
        if clan_id == "thin_blood":
            continue
        if "loresheet_biases" not in clan or not isinstance(clan["loresheet_biases"], dict):
            errors.append(f"clans.json[{clan_id}]: missing loresheet_biases")


def _validate_merits_flaws_descriptions(errors: list[str]) -> None:
    catalog = load_json_cached("wod_chargen.games.lotn_v5.data", "merits_flaws.json")
    for kind in ("merits", "flaws"):
        for entry in catalog[kind]:
            desc = entry.get("description") or ""
            if len(desc) < 20:
                errors.append(f"{kind} {entry['id']}: missing or short description")


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
        _validate_discipline_expressions(
            raw.get("discipline_expressions") or {},
            arch_id,
            registries.get("discipline_biases", set()),
            registries.get("discipline_power_biases", set()),
            errors,
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

    _validate_loresheet_bias_coverage(errors)
    _validate_merits_flaws_descriptions(errors)

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
