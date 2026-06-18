"""XP purchase candidate enumeration for LoTN V5."""

from __future__ import annotations

from typing import Any

from wod_chargen.core.costs import lookup_cost
from wod_chargen.core.data_loader import load_json_cached
from wod_chargen.core.models import LogEntry
from wod_chargen.core.rng import SeededRng
from wod_chargen.core.spender import PurchaseCandidate
from wod_chargen.games.lotn_v5.backgrounds import (
    can_add_dot,
    apply_background_purchase,
    apply_modifier_purchase,
    background_defs,
    enumerate_xp_background_types,
    enumerate_xp_modifier_purchases,
    entries_for_type,
    modifier_item_key,
    modifier_xp_item_bias,
    record_xp_modifier_purchase,
)
from wod_chargen.games.lotn_v5.clan_discipline_adapt import (
    off_clan_signature_factor,
    resolve_discipline_bias,
)
from wod_chargen.games.lotn_v5.disciplines import (
    assign_power_at_level,
    caitiff_owned_disciplines,
    discipline_pool_for_char,
    enumerate_ceremony_candidates,
    enumerate_ghoul_power_candidates,
    enumerate_ritual_candidates,
    owned_power_ids,
    record_ceremony,
    record_formula_selection,
    record_ghoul_power,
    record_ritual,
)
from wod_chargen.games.lotn_v5.loresheets import (
    enumerate_loresheet_purchases,
    resolve_loresheet_bias,
)
from wod_chargen.games.lotn_v5.merits_flaws import enumerate_xp_merit_purchases
from wod_chargen.games.lotn_v5.paths import DATA_PKG as DATA
from wod_chargen.games.lotn_v5.signature_skills import signature_skill_candidates
from wod_chargen.games.lotn_v5.thin_blood_merits import (
    has_discipline_affinity,
    has_thin_blood_alchemist,
)
from wod_chargen.games.lotn_v5.trait_biases import resolve_trait_bias


def enumerate_purchases(

    char: dict[str, Any],
    profile: Any,
    costs: dict[str, Any],
    ctype: str,
    source: str,
    caps: dict[str, int],
    rng: SeededRng,
    *,
    predator_bg_biases: dict[str, float] | None = None,
    discipline_logs: list[LogEntry] | None = None,
) -> list[PurchaseCandidate]:
    candidates: list[PurchaseCandidate] = []
    dlogs = discipline_logs if discipline_logs is not None else []
    clan_pool = set(discipline_pool_for_char(char, ctype))

    def add_attr(attr: str, cat_weight: float, spend_group: str) -> None:
        cur = char["attributes"].get(attr, 0)
        if cur >= caps["attribute"]:
            return
        new_level = cur + 1
        cost = lookup_cost(costs, "attribute", new_level=new_level)

        def apply() -> None:
            char["attributes"][attr] = new_level

        candidates.append(
            PurchaseCandidate(
                item_id=attr,
                category="attribute",
                spend_group=spend_group,
                new_level=new_level,
                cost=cost,
                weight=cat_weight,
                item_bias=profile.attribute_biases.get(attr, 1.0),
                clan_factor=1.0,
                source=source,
                apply=apply,
            )
        )

    attrs = load_json_cached(DATA, "attributes.json")
    for group, wkey in [("physical", "physical_attrs"), ("social", "social_attrs"), ("mental", "mental_attrs")]:
        cw = profile.weights.get(wkey, 1.0)
        for attr in attrs[group]:
            add_attr(attr, cw, wkey)

    skills_data = load_json_cached(DATA, "skills.json")
    sw = profile.weights.get("skills", 1.0)
    signature_ids = frozenset(signature_skill_candidates(profile, skills_data["all"]))
    for skill in skills_data["all"]:
        cur = char["skills"].get(skill, 0)
        if cur >= caps["skill"]:
            continue
        new_level = cur + 1
        cost = lookup_cost(costs, "skill", new_level=new_level)

        def apply_skill(s=skill, nl=new_level) -> None:
            char["skills"][s] = nl

        candidates.append(
            PurchaseCandidate(
                item_id=skill,
                category="skill",
                spend_group="skills",
                new_level=new_level,
                cost=cost,
                weight=sw,
                item_bias=resolve_trait_bias(profile, skill, "skills"),
                clan_factor=1.0,
                source=source,
                apply=apply_skill,
                is_signature=skill in signature_ids,
            )
        )

    dw = profile.weights.get("in_clan_disciplines", 1.0)
    tb_dw = profile.weights.get("thin_blood_disciplines", dw)
    affinity_dw = profile.weights.get("affinity_discipline", tb_dw)
    is_caitiff = char.get("clan") == "caitiff"
    if ctype != "ghoul":
        if is_caitiff:
            disc_iter = caitiff_owned_disciplines(char)
        else:
            disc_iter = sorted(set(char["disciplines"]) | clan_pool)
        for disc in disc_iter:
            cur = char["disciplines"].get(disc, 0)
            if cur >= caps["discipline"]:
                continue
            new_level = cur + 1
            in_clan = disc in clan_pool
            if ctype == "thin_blood" and disc == "thin_blood_alchemy" and not has_thin_blood_alchemist(char):
                continue
            if ctype == "thin_blood" and not in_clan:
                meta = char.get("discipline_meta") or {}
                affinity = meta.get("affinity_discipline")
                resonance = meta.get("resonance_discipline")
                if disc != affinity or disc == resonance:
                    continue
                cost_key = "discipline_out_of_clan"
                clan_factor = off_clan_signature_factor(profile, disc, clan_pool)
            elif is_caitiff:
                cost_key = "discipline_caitiff"
                clan_factor = 1.0
            else:
                cost_key = "discipline_in_clan" if in_clan else "discipline_out_of_clan"
                clan_factor = 1.0 if in_clan else off_clan_signature_factor(profile, disc, clan_pool)
            cost = lookup_cost(costs, cost_key, new_level=new_level)

            if ctype == "thin_blood" and not in_clan:
                disc_weight = affinity_dw
                spend_group = "affinity_discipline"
            elif ctype == "thin_blood":
                disc_weight = tb_dw
                spend_group = "thin_blood_disciplines"
            else:
                disc_weight = dw
                spend_group = "in_clan_disciplines"

            if ctype == "thin_blood" and cur >= 3:
                affinity_id = (char.get("discipline_meta") or {}).get("affinity_discipline")
                merit_gated = (disc == "thin_blood_alchemy" and has_thin_blood_alchemist(char)) or (
                    has_discipline_affinity(char) and disc == affinity_id
                )
                if merit_gated:
                    disc_weight *= 0.35

            def apply_disc(d=disc, nl=new_level) -> None:
                char["disciplines"][d] = nl
                assign_power_at_level(
                    rng, char, d, nl, profile, dlogs, phase="xp", source=source
                )

            item_bias = resolve_discipline_bias(profile, disc, clan_pool)

            candidates.append(
                PurchaseCandidate(
                    item_id=disc,
                    category="discipline",
                    spend_group=spend_group,
                    new_level=new_level,
                    cost=cost,
                    weight=disc_weight,
                    item_bias=item_bias,
                    clan_factor=clan_factor,
                    source=source,
                    apply=apply_disc,
                )
            )

    bw = profile.weights.get("backgrounds", 1.0)
    conn_w = bw * 0.55
    mod_w = bw * 0.3

    def _connection_item_bias(bg_type: str, entry: dict[str, Any] | None) -> float:
        spec = background_defs()[bg_type]
        bias = float(spec.get("creation_bias", 1.0))
        if predator_bg_biases:
            bias *= predator_bg_biases.get(bg_type, 1.0)
        if entry and entry.get("from_predator"):
            bias *= 1.5
        return bias

    for bg_type in enumerate_xp_background_types(char, caps["background"]):
        spec = background_defs()[bg_type]
        max_dots = min(int(spec.get("max_dots", 3)), caps["background"])
        typed = entries_for_type(char["backgrounds"], bg_type)

        def add_candidate(entry: dict[str, Any] | None, *, create_new: bool) -> None:
            if create_new:
                cur = 0
                entry_ref: dict[str, Any] | None = None
            else:
                assert entry is not None
                cur = entry["dots"]
                entry_ref = entry
            new_level = cur + 1
            if new_level > max_dots:
                return
            cost = lookup_cost(costs, "background", new_level=new_level)

            def apply_bg(
                t=bg_type,
                e=entry_ref,
                create=create_new,
            ) -> None:
                if create:
                    apply_background_purchase(
                        char["backgrounds"], t, rng, profile, mark_xp=True
                    )
                else:
                    assert e is not None
                    e["dots"] += 1
                    e["xp_purchased"] = True

            item_key = (
                f"{bg_type}/{entry_ref['name']}"
                if entry_ref
                else f"{bg_type}/new"
            )
            candidates.append(
                PurchaseCandidate(
                    item_id=item_key,
                    category="background",
                    spend_group="background_connections",
                    new_level=new_level,
                    cost=cost,
                    weight=conn_w,
                    item_bias=_connection_item_bias(bg_type, entry_ref),
                    clan_factor=1.0,
                    source=source,
                    apply=apply_bg,
                )
            )

        if spec.get("purchase_mode") == "single_rating":
            entry = typed[0] if typed else None
            if entry is None or entry["dots"] < max_dots:
                add_candidate(entry, create_new=entry is None)
        else:
            for entry in typed:
                if entry["dots"] < max_dots:
                    add_candidate(entry, create_new=False)
            if can_add_dot(char["backgrounds"], bg_type, spec, char):
                add_candidate(None, create_new=True)

    for entry, mod_def, kind, new_level in enumerate_xp_modifier_purchases(
        char, kinds=("advantage",), only_xp_purchased=True
    ):
        mod_id = mod_def["id"]
        cost = lookup_cost(costs, "background", new_level=new_level)

        def apply_mod(
            e=entry,
            mid=mod_id,
        ) -> None:
            apply_modifier_purchase(e, mid, "advantage")
            record_xp_modifier_purchase(char.setdefault("background_meta", {}))

        candidates.append(
            PurchaseCandidate(
                item_id=modifier_item_key(entry, mod_id, kind),
                category="background_modifier",
                spend_group="background_modifiers",
                new_level=new_level,
                cost=cost,
                weight=mod_w,
                item_bias=modifier_xp_item_bias(entry, kind)
                * resolve_trait_bias(profile, mod_id, "modifiers"),
                clan_factor=1.0,
                source=source,
                apply=apply_mod,
            )
        )

    candidates.extend(
        enumerate_xp_merit_purchases(char, profile, costs, ctype, source)
    )

    if ctype == "ghoul":
        for power in enumerate_ghoul_power_candidates(char):
            pid = power["id"]
            if pid in owned_power_ids(char):
                continue
            cost = lookup_cost(costs, "ghoul_power")
            disc_id = power.get("discipline_id", "")

            def apply_power(p=pid, d=disc_id) -> None:
                record_ghoul_power(char, p, d)

            power_bias = float(profile.discipline_power_biases.get(pid, 1.0))
            disc_bias = float(profile.discipline_biases.get(disc_id, 1.0))

            candidates.append(
                PurchaseCandidate(
                    item_id=pid,
                    category="ghoul_power",
                    spend_group="ghoul_powers",
                    new_level=1,
                    cost=cost,
                    weight=profile.weights.get("in_clan_disciplines", 1.0),
                    item_bias=disc_bias * power_bias,
                    clan_factor=1.0,
                    source=source,
                    apply=apply_power,
                )
            )

    if ctype == "thin_blood" and has_thin_blood_alchemist(char):
        fw = profile.weights.get("thin_blood_formulas", 1.5)
        tba = char["disciplines"].get("thin_blood_alchemy", 0)
        for formula in load_json_cached(DATA, "thin_blood_formulas.json")["formulas"]:
            fid = formula["id"]
            if char["thin_blood_formulas"].get(fid, 0) >= 1:
                continue
            if fid in owned_power_ids(char):
                continue
            req_level = int(formula.get("level", 1))
            if tba < req_level:
                continue
            new_level = 1
            cost = lookup_cost(costs, "thin_blood_formula", new_level=new_level)

            def apply_formula(f=fid) -> None:
                record_formula_selection(char, f)

            candidates.append(
                PurchaseCandidate(
                    item_id=fid,
                    category="thin_blood_formula",
                    spend_group="thin_blood_formulas",
                    new_level=new_level,
                    cost=cost,
                    weight=fw,
                    item_bias=1.0,
                    clan_factor=1.0,
                    source=source,
                    apply=apply_formula,
                )
            )

    if ctype == "vampire":
        rw = profile.weights.get("in_clan_disciplines", 0.5)
        for power in enumerate_ritual_candidates(char):
            pid = power["id"]
            level = int(power["level"])
            cost = lookup_cost(costs, "ritual", new_level=level)

            def apply_ritual(p=pid) -> None:
                record_ritual(char, p, dlogs, phase="xp", source=source)

            candidates.append(
                PurchaseCandidate(
                    item_id=pid,
                    category="ritual",
                    spend_group="in_clan_disciplines",
                    new_level=level,
                    cost=cost,
                    weight=rw,
                    item_bias=1.0,
                    clan_factor=1.0,
                    source=source,
                    apply=apply_ritual,
                )
            )

        for power in enumerate_ceremony_candidates(char):
            pid = power["id"]
            level = int(power["level"])
            cost = lookup_cost(costs, "ceremony", new_level=level)

            def apply_ceremony(p=pid) -> None:
                record_ceremony(char, p, dlogs, phase="xp", source=source)

            candidates.append(
                PurchaseCandidate(
                    item_id=pid,
                    category="ceremony",
                    spend_group="in_clan_disciplines",
                    new_level=level,
                    cost=cost,
                    weight=rw,
                    item_bias=1.0,
                    clan_factor=1.0,
                    source=source,
                    apply=apply_ceremony,
                )
            )

    if ctype in ("vampire", "thin_blood"):
        sect = char.get("sect")
        ls_w = profile.weights.get(
            "loresheets",
            max(profile.weights.get("merits", 0.5) * 2.0, 1.4),
        )
        for ls_id, new_level in enumerate_loresheet_purchases(char, profile, sect=sect):
            cost = lookup_cost(costs, "loresheet", new_level=new_level)

            def apply_ls(l=ls_id, nl=new_level) -> None:
                char["loresheets"][l] = nl

            candidates.append(
                PurchaseCandidate(
                    item_id=ls_id,
                    category="loresheet",
                    spend_group="loresheets",
                    new_level=new_level,
                    cost=cost,
                    weight=ls_w,
                    item_bias=resolve_loresheet_bias(ls_id, profile, char, sect=sect),
                    clan_factor=1.0,
                    source=source,
                    apply=apply_ls,
                )
            )

    if ctype == "vampire" and char.get("blood_potency", 0) < caps["blood_potency"]:
        cur = char["blood_potency"]
        new_level = cur + 1
        cost = lookup_cost(costs, "blood_potency", new_level=new_level)

        def apply_bp() -> None:
            char["blood_potency"] = new_level

        candidates.append(
            PurchaseCandidate(
                item_id="blood_potency",
                category="blood_potency",
                spend_group="blood_potency",
                new_level=new_level,
                cost=cost,
                weight=0.4,
                item_bias=1.0,
                clan_factor=1.0,
                source=source,
                apply=apply_bp,
            )
        )

    return candidates

