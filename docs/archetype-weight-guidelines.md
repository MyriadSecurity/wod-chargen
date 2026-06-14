# Archetype weight guidelines

Bias values steer procedural generation toward archetype themes. Eligibility rules apply first; bias only weights among eligible options.

**Data locations:**

- `wod_chargen/games/lotn_v5/data/archetype_themes.json` — central theme source
- `wod_chargen/games/lotn_v5/data/archetypes/<id>.json` — merged primary profiles
- `wod_chargen/games/lotn_v5/data/archetypes/<id>/<sub>.json` — sub modifiers

## Value ranges

| Role | Range | Notes |
|------|-------|-------|
| Primary on-theme affinity | 1.4–2.0 | `tag_affinities` or explicit trait bias |
| Sub sharpen (delta) | +0.2–0.5 | Additive on parent via sub `modifiers` |
| Soft opposed / off-theme | 0.4–0.7 | Tag clash or low affinity |
| Hard antithesis | 0.05–0.15 | Explicit trait id or `hard_opposed:*` tag |
| Global clamp | 0.05–3.0 | Enforced in `trait_biases.resolve_trait_bias` |

## Resolution order

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
| `loresheet_biases` | loresheet id | XP loresheet pick (one per character) |
| `weights.loresheets` | spend group | XP weight within merits/flaws bucket |
| `discipline_power_biases` | power id | power pick in disciplines |
| `tag_affinities` | tag slug → multiplier | all tagged traits |

Subs use additive deltas under `modifiers`. Do not add `discipline_expressions` on subs.

## Tags

Shared tags: `wod_chargen/games/lotn_v5/data/trait_tags.json`. Regenerate after catalog changes:

```bash
uv run python scripts/generate_trait_tags.py
```

## Opposition policy

- **Soft clash** — off-theme flavor: `opposed:tag` (~0.55) or tag affinity 0.4–0.7.
- **Hard antithesis** — direct contradiction: explicit 0.05–0.15 on trait id or `hard_opposed:tag`.

## Content workflow

1. Edit `data/archetype_themes.json`.
2. Run `uv run python scripts/apply_archetype_themes.py`.
3. Validate: `uv run python scripts/validate_archetype_biases.py`.
4. Spot-check: `uv run python scripts/archetype_weight_report.py --seeds 30`.

## Pitfalls

- **Over-tuning** — prefer soft tag affinities; floor is 0.05.
- **Amalgam/prereq** — power bias never bypasses eligibility.
- **Orphan keys** — validation fails on unknown ids.
- **Single-discipline tunnel vision** — name 3–5 signature `discipline_power_biases`, not every power.
- **Sub power deltas** — use +0.2–0.5 on subs, not target totals.
- **Secondary in-clan** — clan pool forces 3 disciplines; only one may match archetype core.

## Discipline power layers

```
effective_power_bias = clamp(archetype_bias × utility_bias)
```

| Layer | Source | Purpose |
|-------|--------|---------|
| Archetype theme | `discipline_power_biases`, `tag_affinities` | On-concept flavor |
| Neutral utility | `discipline_power_utility.json` | Broad usefulness when discipline is taken anyway |

Review: `uv run python scripts/discipline_power_coverage_report.py --matrix --clan <clan> [--arch <id>]`. See `docs/discipline-clan-matrix.md`.

## Clan discipline expressions

When signature disciplines are off-clan, define `discipline_expressions` on the **primary** in `archetype_themes.json`:

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
- `alternates` — merged only for in-clan disciplines when a signature is missing.
- Alternate `discipline_bias` values are targets (max with current); `power_biases` are overrides.
- Runtime floors via `clan_discipline_adapt.py`; off-clan signatures use XP `clan_factor` 0.6.
