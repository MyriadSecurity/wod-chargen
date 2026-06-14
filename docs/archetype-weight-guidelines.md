# Archetype weight guidelines

Bias values steer procedural character generation toward archetype themes without hard-locking picks. Eligibility rules always apply first; bias only weights among eligible options.

## Value ranges

| Role | Range | Notes |
|------|-------|-------|
| Primary on-theme affinity | 1.4–2.0 | `tag_affinities` or explicit trait bias |
| Sub sharpen (delta) | +0.2–0.5 | Additive on parent via sub `modifiers` |
| Soft opposed / off-theme | 0.4–0.7 | Tag clash or low affinity |
| Hard antithesis | 0.05–0.15 | Explicit trait id or `hard_opposed:*` tag |
| Global clamp | 0.05–3.0 | Enforced in `trait_biases.resolve_trait_bias` |

## Resolution order

For any trait id (skill, merit, power, `contacts`, sphere `underworld`, etc.):

```
effective_bias = explicit_bias.get(trait_id)
              OR product(tag_affinity[t] for t in trait_tags[trait_id])
              OR 1.0
```

Explicit keys on the merged profile (primary + sub deltas) take precedence over tag products.

## Profile fields

| Field | Keys | Used by |
|-------|------|---------|
| `attribute_biases` | attribute id | creation + XP attributes |
| `skill_biases` | skill id | creation + XP skills |
| `discipline_biases` | discipline id | creation + XP disciplines |
| `merit_biases` | merit id | Step 8 + XP merits |
| `flaw_biases` | flaw id | Step 8 flaws |
| `background_biases` | allies, contacts, … | creation + XP backgrounds |
| `sphere_biases` | church, underworld, … | sphere pick on new entries |
| `modifier_biases` | flaky, reliable, … | adv/disadv modifier picks |
| `discipline_power_biases` | power id | power pick in disciplines |
| `tag_affinities` | tag slug → multiplier | all tagged traits |

Subs use additive deltas under `modifiers` for every field except where a sub JSON documents explicit signature overrides (e.g. `discipline_power_biases` on subs are merged additively like other bias keys).

## Tags

Shared tags live in `wod_chargen/games/lotn_v5/data/trait_tags.json`. Powers inherit discipline tags plus per-power overrides. Regenerate power tags after catalog changes:

```bash
uv run python scripts/generate_trait_tags.py
```

## Opposition policy (mixed)

- **Soft clash** — off-theme flavor: multiply opposing tag affinity by ~0.55 (`opposed:tag`) or set tag affinity 0.4–0.7.
- **Hard antithesis** — direct contradiction (Spy vs Fame, Brawler vs Etiquette-adjacent merits): explicit `0.05–0.15` on trait id or `hard_opposed:tag` on the flaw/trait tag list.

## Content workflow

1. Edit `data/archetype_themes.json` (central theme source).
2. Run `uv run python scripts/apply_archetype_themes.py`.
3. Validate: `uv run python scripts/validate_archetype_biases.py`.
4. Spot-check: `uv run python scripts/archetype_weight_report.py --seeds 30`.
5. Document per-archetype notes in `docs/archetype-weights/<id>.md` (auto-generated header; extend by hand if needed).

## Pitfalls

- **Over-tuning** — prefer soft tag affinities; floor is 0.05 so nothing is truly zero.
- **Amalgam/prereq** — power bias never bypasses eligibility.
- **Orphan keys** — validation script fails on unknown ids; run after JSON edits.
- **Single-discipline tunnel vision** — explicit `discipline_power_biases` should name 3–5 signature picks, not every power in one discipline. Tag affinities already boost whole tag families (e.g. all `presence`-tagged powers).
- **Sub power deltas** — subs add to primary via `effective_profile`; use **+0.2–0.5** deltas on subs, not target totals like `2.05`.
- **Secondary in-clan** — clan pool forces 3 disciplines at creation; only one may match the archetype core. Review picks for the other two.

## Discipline power layers

Effective pick weight is the product of two layers:

| Layer | Source | Purpose |
|-------|--------|---------|
| Archetype theme | `discipline_power_biases`, `tag_affinities` | On-concept flavor |
| Neutral utility | `discipline_power_utility.json` | Broad LARP usefulness when a discipline is taken anyway |

```
effective_power_bias = clamp(archetype_bias × utility_bias)
```

- **Utility defaults** — level 1–2 powers slightly favored (more table time per dot); level 5 slightly deprioritized unless overridden.
- **Utility overrides** — ~40 staple powers (Fleetness, Conceal, Sense the Unseen, etc.) get explicit scores.
- **Review workflow** — for each primary, run `scripts/discipline_power_coverage_report.py --clan <typical>` and confirm in-clan disciplines without signature picks still produce sensible staples via utility.

Do **not** rely on tag affinities alone for off-theme in-clan disciplines — broad tags like `combat` suppress entire Celerity/Potence pools for social archetypes.

## Clan discipline expressions

When an archetype’s **signature** disciplines (Potence/Fortitude for Enforcer, Blood Sorcery for Occultist, etc.) are off-clan, define `discipline_expressions` on the **primary** in `archetype_themes.json`:

```json
"discipline_expressions": {
  "signature": ["potence", "fortitude"],
  "alternates": {
    "celerity": {
      "discipline_bias": 1.12,
      "power_biases": { "fleetness": 1.25, "rapid_reflexes": 1.2 }
    }
  }
}
```

- `signature` — explicit list, or inferred from `discipline_biases` ≥ 1.05.
- `alternates` — merged **only** for disciplines in the character’s in-clan pool when any signature is missing from that pool.
- Alternate `discipline_bias` values are **targets** (max with current); `power_biases` are **explicit overrides**, not deltas.
- Runtime also applies in-clan soft floors (discipline ≥ 0.85, non-explicit powers ≥ 0.75) via `clan_discipline_adapt.py`.
- Off-clan signature disciplines use XP `clan_factor` **0.6** instead of 0.3.
- Do **not** add expression maps on subs; subs keep +0.2–0.5 deltas only.

Review matrix: `uv run python scripts/discipline_power_coverage_report.py --matrix --clan <clan> [--arch <id>]`. See `docs/discipline-clan-matrix.md` for batch notes.
