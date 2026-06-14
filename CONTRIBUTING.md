# Contributing

## Archetype weights

Weights live in:

- `wod_chargen/games/lotn_v5/data/archetype_themes.json` — central theme source
- `wod_chargen/games/lotn_v5/data/archetypes/` — merged primary + sub JSON (see `_schema.json`)

Workflow: `docs/archetype-weight-guidelines.md`, `docs/creation-weighting-strategy.md`

```bash
source .venv/bin/activate
uv run python scripts/apply_archetype_themes.py
uv run python scripts/validate_archetype_biases.py
pytest tests/test_archetypes.py tests/test_generator.py
```

## UI and picker config

Edit standalone JSON — not inline Python or wizard strings:

| File | Purpose |
|------|---------|
| `wod_chargen/games/catalog.json` | Game picker cards |
| `wod_chargen/games/lotn_v5/data/wizard_ui.json` | Wizard steps, type picker ids |
| `wod_chargen/games/lotn_v5/data/faction_picker.json` | Faction grid order/titles per role |
| `wod_chargen/games/lotn_v5/data/clans.json` | Clan + thin-blood lineage cards |
| `wod_chargen/venues/picker.json` | Venue ids per game |
| `wod_chargen/venues/<id>.json` | Venue labels and XP rules |

Regenerate PyScript file manifest after adding Python or JSON under `app/` or `wod_chargen/`:

```bash
python scripts/generate_pyscript_config.py
pytest tests/test_pyscript_manifest.py
```

## Local dev server

PyScript caches `.py` files aggressively. Use the no-cache dev server:

```bash
python scripts/dev_server.py
# open http://localhost:8080/
```

After changing packaged files:

```bash
python scripts/generate_pyscript_config.py
pytest
```
