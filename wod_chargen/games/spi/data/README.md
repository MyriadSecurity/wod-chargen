# SPI data package

Authoritative oneshot/NPC data for Society of Paranormal Investigators.

**Maintainer index:** [`docs/where-to-edit.md`](../../../../docs/where-to-edit.md)  
**Schema notes:** [`archetypes/_schema.json`](archetypes/_schema.json)  
**Weight rules:** [`docs/archetype-weight-guidelines.md`](../../../../docs/archetype-weight-guidelines.md)

## Layout

| Path | Role |
|------|------|
| `archetypes/<id>.json` | Primary absolute bias maps |
| `archetypes/<id>/<sub>.json` | Subtype `modifiers` (additive deltas) |
| `archetypes/_manifest.json` | Primary list + subtype registration |
| `divisions.json` / `factions.json` | Soft bias layers |
| `trait_tags.json` | Judgment theme tags for merit weighting |
| `merits.json` | Catalog (ids, dots, prereqs); extract tags are metadata only |
| `merit_descriptions.json` | Flavor-only blurbs for sheet display (survives re-seed) |
| `costs.json` / `creation.json` | XP rates and free-creation pools |
| `wizard_ui.json` | Wizard step ids and copy keys |
| `attributes.json` / `skills.json` | CoD trait lists (Presence, Weaponry) |
| `specialties.json` | Example specialty labels per skill (generator picks from these) |

## Edit checklist

1. Change the JSON above (hand-edit; no themes apply script for SPI).
2. Validate: `scripts/validate_spi_archetypes.py`, `scripts/validate_spi_merit_biases.py`.
3. Regenerate PyScript manifest if you added files: `scripts/generate_pyscript_config.py`.
4. Spot-check Weight Map (`#weights?game=spi`) and a few generator seeds.
