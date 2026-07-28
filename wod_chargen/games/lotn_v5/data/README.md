# LotN V5 data package

Authoritative BNS Laws of the Night V5 generation data.

**Maintainer index:** [`docs/where-to-edit.md`](../../../../docs/where-to-edit.md)  
**Weight rules:** [`docs/archetype-weight-guidelines.md`](../../../../docs/archetype-weight-guidelines.md)  
**Build pipeline:** [`docs/creation-weighting-strategy.md`](../../../../docs/creation-weighting-strategy.md)

## Layout (high traffic)

| Path | Role |
|------|------|
| `archetype_themes.json` | Central theme source → apply script |
| `archetypes/<id>.json` | Merged primary profiles |
| `archetypes/<id>/<sub>.json` | Subtype modifiers |
| `predator_types.json` | Feed types + packages |
| `clans.json` | Clan / lineage cards |
| `trait_tags.json` | Shared trait tags |
| `wizard_ui.json` / `faction_picker.json` | Wizard UI config |

## Edit checklist

1. Prefer editing `archetype_themes.json`, then `scripts/apply_archetype_themes.py`.
2. Validate: `scripts/validate_archetype_biases.py`.
3. Regenerate PyScript manifest if you added files: `scripts/generate_pyscript_config.py`.
