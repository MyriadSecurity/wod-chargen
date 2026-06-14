"""Apply structured benefit packages (predator types, loresheet levels, etc.)."""

from __future__ import annotations

from typing import Any

from wod_chargen.core.rng import SeededRng
from wod_chargen.games.lotn_v5.archetypes import ArchetypeProfile
from wod_chargen.games.lotn_v5.backgrounds import (
    background_label,
    grant_background_rating,
)
from wod_chargen.games.lotn_v5.merits_flaws import (
    apply_enemy_flaw,
    apply_trait_dots,
    trait_display_label,
    trait_label,
    _dots_display,
)
from wod_chargen.games.lotn_v5.package_grants import (
    apply_flaw_grant,
    apply_flaw_spend,
    attach_advantage,
    grant_background_spec,
    latest_background_entry,
    split_dots,
)


def _apply_skill_grants(
    char: dict[str, Any],
    package: dict[str, Any],
    rng: SeededRng,
    *,
    log_prefix: str,
) -> list[str]:
    lines: list[str] = []
    skills = char.setdefault("skills", {})
    for spec in package.get("skills", []):
        skill_id = spec.get("id")
        if spec.get("choice"):
            skill_id = rng.choice(list(spec["choice"]))
        if not skill_id:
            continue
        target = int(spec["dots"])
        before = int(skills.get(skill_id, 0))
        skills[skill_id] = max(before, target)
        if skills[skill_id] > before:
            lines.append(
                f"{log_prefix}: Skill {skill_id.replace('_', ' ').title()} "
                f"+{skills[skill_id] - before} → {skills[skill_id]}"
            )
    return lines


def apply_benefit_package(
    package: dict[str, Any],
    char: dict[str, Any],
    rng: SeededRng,
    profile: ArchetypeProfile,
    *,
    caps: dict[str, int],
    log_prefix: str = "Predator",
) -> list[str]:
    """Grant backgrounds, merits, flaws, and skills from a package dict."""
    if not package:
        return []

    lines: list[str] = []
    entries = char["backgrounds"]

    for bg in package.get("backgrounds", []):
        for line in grant_background_spec(rng, entries, bg, profile, char=char):
            lines.append(line.replace("Predator:", f"{log_prefix}:", 1))

    for grant in package.get("background_grants", []):
        for line in grant_background_spec(rng, entries, grant, profile, char=char):
            lines.append(line.replace("Predator:", f"{log_prefix}:", 1))

    spend = package.get("background_spend")
    if spend:
        allocation = split_dots(rng, int(spend["dots"]), list(spend["options"]))
        for bg_type, grant in allocation.items():
            if grant <= 0:
                continue
            line = grant_background_rating(
                rng,
                entries,
                bg_type,
                grant,
                profile,
                from_predator=True,
                char=char,
                log_prefix=log_prefix,
            )
            if line:
                lines.append(line)

    adv_spend = package.get("advantage_spend")
    if adv_spend:
        bg_type = adv_spend["background"]
        entry = latest_background_entry(entries, bg_type)
        if entry is None:
            line = grant_background_rating(
                rng,
                entries,
                bg_type,
                1,
                profile,
                from_predator=True,
                char=char,
                log_prefix=log_prefix,
            )
            if line:
                lines.append(line)
            entry = latest_background_entry(entries, bg_type)
        if entry:
            options = adv_spend.get("options") or []
            total = int(adv_spend.get("dots", 1))
            if adv_spend.get("split"):
                allocation = split_dots(rng, total, list(options))
                for mod_id, mod_dots in allocation.items():
                    if mod_dots <= 0:
                        continue
                    adv_line = attach_advantage(
                        entry,
                        mod_id,
                        mod_dots,
                        char=char,
                        log_prefix=log_prefix,
                    )
                    if adv_line:
                        lines.append(adv_line.replace("Predator:", f"{log_prefix}:", 1))
            else:
                mod_id = rng.choice(list(options))
                adv_line = attach_advantage(
                    entry,
                    mod_id,
                    total,
                    char=char,
                    log_prefix=log_prefix,
                )
                if adv_line:
                    lines.append(adv_line.replace("Predator:", f"{log_prefix}:", 1))

    for merit in package.get("merits", []):
        merit_id = merit["id"]
        dots = int(merit.get("dots", 1))
        merits = char.setdefault("merits", {})
        before = int(merits.get(merit_id, 0))
        added = apply_trait_dots(merits, merit_id, "merit", dots, char, ignore_rules=True)
        if added:
            label = trait_label(merit_id, "merit")
            lines.append(
                f"{log_prefix}: Merit {label} +{merits[merit_id] - before} "
                f"→ {_dots_display(merits[merit_id])}"
            )

    lines.extend(_apply_skill_grants(char, package, rng, log_prefix=log_prefix))

    if "humanity" in package:
        delta = int(package["humanity"])
        before = int(char.get("humanity", 7))
        char["humanity"] = max(0, min(10, before + delta))
        sign = "+" if delta >= 0 else "−"
        lines.append(f"{log_prefix}: Humanity {sign}{abs(delta)} → {char['humanity']}")

    if "blood_potency" in package:
        delta = int(package["blood_potency"])
        before = int(char.get("blood_potency", 1))
        char["blood_potency"] = max(0, min(caps["blood_potency"], before + delta))
        lines.append(f"{log_prefix}: Blood Potency +{delta} → {char['blood_potency']}")

    for flaw_spec in package.get("flaws", []):
        for line in apply_flaw_grant(rng, char, entries, flaw_spec, profile):
            lines.append(line.replace("Predator:", f"{log_prefix}:", 1))

    flaw_pick = package.get("flaw_pick")
    if flaw_pick:
        for line in apply_flaw_grant(rng, char, entries, rng.choice(flaw_pick["options"]), profile):
            lines.append(line.replace("Predator:", f"{log_prefix}:", 1))

    flaw_choice = package.get("flaw_choice")
    if flaw_choice:
        branch = rng.choice(flaw_choice)
        if branch.get("flaws"):
            for flaw_spec in branch["flaws"]:
                for line in apply_flaw_grant(rng, char, entries, flaw_spec, profile):
                    lines.append(line.replace("Predator:", f"{log_prefix}:", 1))
        if branch.get("flaw_spend"):
            for line in apply_flaw_spend(rng, char, branch["flaw_spend"], profile):
                lines.append(line.replace("Predator:", f"{log_prefix}:", 1))

    flaw_spend = package.get("flaw_spend")
    if flaw_spend:
        for line in apply_flaw_spend(rng, char, flaw_spend, profile):
            lines.append(line.replace("Predator:", f"{log_prefix}:", 1))

    return lines
