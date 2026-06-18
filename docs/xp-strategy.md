# XP strategy (LoTN V5)

How the procedural generator spends experience points after character creation. This document mirrors the in-app **XP Strategy** page and describes behavior in `wod_chargen/core/xp_strategy.py`, `wod_chargen/core/spender.py`, and `wod_chargen/games/lotn_v5/xp_purchases.py`.

## Goals

- Spend the full venue XP budget on purchases that fit the merged archetype profile (archetype + sub + predator + clan adaptation).
- Favor **efficient dot buys** (cheap fifth dots, shallow new traits) while keeping a believable **category mix** across disciplines, attributes, skills, backgrounds, and merits/loresheets.
- Respect LoTN eligibility: caps, in-clan vs out-of-clan discipline costs, thin-blood gates, sect loresheet rules, and mandatory generation Blood Potency.

## Pipeline

1. **Resolve budget** — venue config (`fixed`, `mes_approval_month`, or `custom`) sets starting XP.
2. **Mandatory Blood Potency** — if generation requires a minimum Blood Potency above the free creation value, spend XP on BP before any discretionary picks (logged as `source: mandatory`).
3. **Discretionary loop** — repeat until budget exhausted or no affordable candidates:
   - Roll per-character **category targets** (jittered macro budget shares).
   - **Stage 1:** pick a macro category (disciplines, attributes, skills, backgrounds, merits_flaws) weighted by target share × group strength × deficit boost.
   - **Stage 2:** pick a spend group within that macro (e.g. `physical_attrs`, `in_clan_disciplines`).
   - **Stage 3:** pick one purchase among eligible items in that group using `item_bias × clan_factor × efficiency × random roll`.
4. **Loresheet benefits** — after XP spend, apply any free loresheet benefit packages tied to purchased dots (not charged against remaining budget).

## Category budget (macro mix)

Each character rolls jittered targets from base shares (normalized to 100%):

| Macro | Base share | Typical spend groups |
|-------|------------|----------------------|
| Disciplines | 34% | `in_clan_disciplines`, `thin_blood_disciplines`, `affinity_discipline`, `ghoul_powers`, `thin_blood_formulas` |
| Attributes | 20% | `physical_attrs`, `social_attrs`, `mental_attrs` |
| Skills | 20% | `skills` |
| Backgrounds | 12% | `background_connections`, `background_modifiers`, `background_disadvantages` |
| Merits & flaws | 14% | `merits`, `loresheets`, `blood_potency` |

**Deficit boost** raises weight for macros behind their expected spend share (`DEFICIT_SCALE = 4.5`, clamped 0.25–4.0). **Budget efficiency scale** dampens efficient picks when a macro is already over target (and nudges under-target macros).

Jitter per character: each base share × uniform(0.82, 1.18), then renormalized.

## Profile weights (spend groups)

Archetype `weights.*` keys scale entire spend groups before item-level bias:

| Weight key | Role |
|------------|------|
| `physical_attrs`, `social_attrs`, `mental_attrs` | Attribute category pools |
| `skills` | All skills |
| `in_clan_disciplines` | Vampire/Caitiff disciplines, rituals, ceremonies |
| `thin_blood_disciplines` / `affinity_discipline` | Thin-blood in-clan vs resonance discipline |
| `thin_blood_formulas` | Alchemist formulas |
| `backgrounds` | Split: connections (~55%), modifiers (~30%), disadvantages (remainder) |
| `merits` | XP merit purchases |
| `loresheets` | Loresheet dot track (defaults high vs merits) |

Item-level **`item_bias`** comes from the merged profile. Skills use **`resolve_trait_bias`** (explicit keys + tag affinities), not raw `skill_biases` alone. Attributes and other categories use their respective bias maps. **`clan_factor`** applies to out-of-clan signature disciplines (typically 0.6) via `clan_discipline_adapt.py`.

## Efficiency biases (dot economics)

XP favors purchases that match LoTN cost curves:

| Transition | Bias | Signature skill (floor) |
|------------|------|-------------------------|
| 4 → 5 | 5.0 | 5.0 |
| 0 → 1 | 2.5 | — |
| 0 → 2 | 1.6 | — |
| 1 → 2 | 1.4 | — |
| 2 → 3 | 0.35 | **2.5** |
| 3 → 4 | 1.1 | **3.5** |
| 0 → 3+ | 0.1 | — |

**Signature skills** — top 3 skills by merged bias ≥ threshold (default 1.35), same set as creation — use `signature_skill_efficiency_bias` so XP can finish •3–•5 spikes after the creation @3 reserve.

**Loresheets** use a separate curve favoring taking a sheet and completing 2–3 dots (0→1: 3.2, 1→2: 3.6, 2→3: 2.8).

## Creation setup (pre-XP)

**Attributes** use `creation_pick_weight`: +4 pool chunks favored (×2.0) for cheap fifth-dot XP buys; +3 gets ×1.3; +1/+2 get ×1.15.

**Skills:** one @3 slot is reserved for a signature skill before the remaining pool is assigned; see `wod_chargen/games/lotn_v5/signature_skills.py` and `creation.json` (`signature_skill_bias_threshold`).

## Purchase catalog (by character type)

**All types:** attributes, skills, backgrounds (connections + XP-purchased modifiers), merits (where allowed).

**Vampire:** in-clan and eligible out-of-clan disciplines (with power assignment at each new level), rituals, ceremonies, loresheets, optional Blood Potency (low group weight 0.4 — mandatory minimum already applied).

**Thin blood:** thin-blood disciplines, affinity/resonance rules, formulas when Alchemist merit present; merit-gated disciplines above •3 get reduced weight (×0.35).

**Caitiff:** any owned or clan-pool discipline at Caitiff cost tier.

**Ghoul:** domitor-clan discipline powers as flat-cost purchases.

## Tuning and validation

- Category targets and efficiency: `tests/test_xp_strategy.py`
- Archetype bias keys: `docs/archetype-weight-guidelines.md` and the Weight Map explorer
- Spot-check spend mix: generate with varied seeds and inspect `xp_log` on the character sheet

## Related code

| Module | Responsibility |
|--------|----------------|
| `wod_chargen/core/xp_strategy.py` | Targets, efficiency, deficit/creation helpers |
| `wod_chargen/core/spender.py` | Three-stage weighted pick loop |
| `wod_chargen/games/lotn_v5/xp_purchases.py` | Enumerate legal candidates per character state |
| `wod_chargen/games/lotn_v5/signature_skills.py` | Signature skill set, creation @3 reserve |
| `wod_chargen/games/lotn_v5/generation.py` | Mandatory Blood Potency |
| `wod_chargen/venues/` | XP budget resolution |
