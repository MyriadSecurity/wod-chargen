# Disciplines review — LoTN V5 chargen

Context for procedural discipline power selection. Sources: MES `discipline_powers.json`, pocket book ch. disciplines (~p.79), creation files.

## Selection rules (confirmed for implementation)

1. **One power per dot level** — when a discipline gains a dot at level *N*, the character chooses exactly one power at level *N* from that discipline's list (mutually exclusive per level slot).
2. **Discipline rating** — `character["disciplines"][slug]` is the cap and source of truth; `discipline_powers[slug]["N"]` must exist for each level `1..rating`.
3. **Amalgams** — power requires another discipline at `amalgam_min_level` (19 powers in MES catalog).
4. **Prerequisites** — power requires owning specific other powers first (9 text prereqs; includes OR case `Conceal or Unseen Passage`).
5. **Creation** — free discipline dots are in-clan only (MES venue); each assigned dot triggers power picks at levels 1..dots.
6. **XP** — discipline dot purchases use existing in/out-of-clan costs; each +1 triggers a power pick at the new level.

## Track taxonomy

| Track kind | Catalog id | Parent discipline | XP cost key | Notes |
|------------|------------|-------------------|-------------|-------|
| discipline | animalism … protean, oblivion, blood_sorcery, thin_blood_alchemy | — | discipline_in/out_clan | In-clan lists from `clans.json` |
| ritual | blood_sorcery_rituals | blood_sorcery | ritual | Requires BS rating ≥ ritual level |
| ceremony | ceremonies | oblivion | ceremony | Requires Oblivion rating ≥ ceremony level |
| formula | thin_blood_alchemy (named) | — | thin_blood_formula | 6 named formulas only in v1; counterfeits deferred |

## Character schema

```json
{
  "disciplines": { "celerity": 3 },
  "discipline_powers": {
    "celerity": { "1": "fleetness", "2": "cats_grace", "3": "swiftness" }
  },
  "rituals": ["blood_walk"],
  "ceremonies": ["din_of_the_damned"],
  "thin_blood_formulas": { "far_reach": 2 },
  "formula_powers": { "far_reach": { "1": "far_reach", "2": "far_reach" } },
  "discipline_meta": {}
}
```

Legacy shares without `discipline_powers` display dots only.

## Prerequisite inventory (MES text → structured rules)

| Power | Prerequisite text | Resolution |
|-------|-------------------|------------|
| unburdening_the_bestial_soul | Panacea | requires_all: panacea |
| baal_s_caress | Scorpion's Touch | requires_all: scorpion_s_touch |
| blood_walk | A Taste For Blood | requires_all: a_taste_for_blood |
| conditioning | Submerged Directive | requires_all: submerged_directive |
| cache | Conceal | requires_all: conceal |
| vanish_from_the_mind_s_eye | Conceal or Unseen Passage | requires_any: conceal, unseen_passage |
| fleshcrafting | Vicissitude | requires_all: vicissitude |
| metamorphosis | Shapechange | requires_all: shapechange |
| horrid_form | Vicssitide | requires_all: vicissitude (import typo) |

## XP costs (v1 proposal)

| Key | Formula | Rationale |
|-----|---------|-----------|
| ritual | new_level × 5 | Match in-clan discipline |
| ceremony | new_level × 5 | Match in-clan discipline |

## Deferred (not v1)

- Counterfeit thin-blood formulas (~101)
- `discipline_affinity` merit
- `discipline_caitiff` pricing
- Predator package discipline grants
- Per-power ghoul picks (keep ghoul discipline dots + ghoul_power stub)

## Thin-blood fix

Thin-bloods use `thin_blood_alchemy` as sole creation discipline pool (no clan).
