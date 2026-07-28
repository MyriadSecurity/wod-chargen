# Where to edit

Front door for maintainers. Pick a task → open the file. Deeper rules live in the linked docs.

**Naming:** Product **Venue** = game line (`lotn_v5`, `spi`). On-disk `wod_chargen/venues/` holds **starting XP profiles** (not Venues). Prefer `get_xp_profile_picker()` in new code.

After any new/changed `.py` / `.json` under `app/` or `wod_chargen/`:

```bash
.venv/bin/python scripts/generate_pyscript_config.py
```

---

## SPI (Society of Paranormal Investigators)

| I want to… | Edit |
|------------|------|
| Change an archetype’s feel | `wod_chargen/games/spi/data/archetypes/<id>.json` |
| Sharpen a subtype | `wod_chargen/games/spi/data/archetypes/<id>/<sub>.json` → `modifiers` |
| Add archetype / subtype | New JSON + register in `archetypes/_manifest.json` (see `_schema.json`) |
| Tilt a Division | `wod_chargen/games/spi/data/divisions.json` |
| Tilt a Faction | `wod_chargen/games/spi/data/factions.json` |
| Retag merits for theme weighting | `wod_chargen/games/spi/data/trait_tags.json` (not extract tags on `merits.json`) |
| Change XP / creation costs | `wod_chargen/games/spi/data/costs.json`, `creation.json` |
| Change XP spend mix targets | `wod_chargen/core/xp_strategy.py` → `SPI_CATEGORY_TARGETS` |
| Change wizard steps / labels | `wod_chargen/games/spi/data/wizard_ui.json` |
| Change Build guide copy | `app/strategy_content_spi.py` |
| Change Weight Map trees | `app/weight_map_data_spi.py` |
| Change sheet layout VM | `wod_chargen/games/spi/sheet_model.py` |
| Change generation rules | `wod_chargen/games/spi/generator.py` |
| Change starting XP profiles | `wod_chargen/venues/picker.json` + `wod_chargen/venues/<id>.json` |

**Validate**

```bash
.venv/bin/python scripts/validate_spi_archetypes.py
.venv/bin/python scripts/validate_spi_merit_biases.py
.venv/bin/pytest -q tests/test_spi_generator.py tests/test_spi_archetypes.py tests/test_spi_trait_biases.py
```

**Spot-check:** open `#weights?game=spi` and `#strategy?game=spi`, then generate a few seeds.

**Weights deep-dive:** [archetype-weight-guidelines.md](archetype-weight-guidelines.md) (SPI sections).  
**Design bible:** [spi-structure.md](spi-structure.md).  
**In-tree map:** `wod_chargen/games/spi/data/README.md`.

---

## LotN V5

| I want to… | Edit |
|------------|------|
| Bulk-retune archetype themes | `wod_chargen/games/lotn_v5/data/archetype_themes.json` then apply script |
| Hand-edit a primary / subtype | `wod_chargen/games/lotn_v5/data/archetypes/<id>.json` (+ `<id>/<sub>.json`) |
| Predator packages / biases | `wod_chargen/games/lotn_v5/data/predator_types.json` |
| Clan cards / in-clan list | `wod_chargen/games/lotn_v5/data/clans.json` |
| Trait tags | `wod_chargen/games/lotn_v5/data/trait_tags.json` |
| Build guide copy | `app/strategy_content_lotn.py` |
| Weight Map trees | `app/weight_map_data.py` |
| Wizard / faction picker UI | `wizard_ui.json`, `faction_picker.json` |

**Workflow**

```bash
.venv/bin/python scripts/apply_archetype_themes.py   # if you edited themes
.venv/bin/python scripts/validate_archetype_biases.py
.venv/bin/pytest -q tests/test_archetypes.py tests/test_generator.py
```

**Docs:** [archetype-weight-guidelines.md](archetype-weight-guidelines.md), [creation-weighting-strategy.md](creation-weighting-strategy.md), [xp-strategy.md](xp-strategy.md).

---

## Shared / app

| I want to… | Edit |
|------------|------|
| Game picker cards (landing) | `wod_chargen/games/catalog.json` |
| Register a VenueSystem | `wod_chargen/games/registry.py` |
| Route guide / weight map by Venue | `app/venue_dispatch.py` |
| Wizard shell / steps wiring | `app/wizard.py`, `app/wizard_state.py` |
| Weight Map UI chrome | `app/weight_map.py`, `static/weight_map.js` |
| Dev / agent environment notes | `AGENTS.md`, `CONTRIBUTING.md` |

---

## Quick “which layer?” for SPI biases

```
sheet lean ≈ archetype (± subtype deltas)
           × division maps
           × faction maps
           × tag_affinities → trait_tags → merits
```

Explicit `merit_biases` / skill ids on a pack beat tag products. Illegal options never enter the pool regardless of weight.
