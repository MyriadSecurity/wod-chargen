# Contributing

**Start here for “what file do I edit?”:** [`docs/where-to-edit.md`](docs/where-to-edit.md)

## Archetype / bias weights

### LotN V5

| File | Role |
|------|------|
| `wod_chargen/games/lotn_v5/data/archetype_themes.json` | Central theme source |
| `wod_chargen/games/lotn_v5/data/archetypes/` | Merged primary + sub JSON |

```bash
source .venv/bin/activate
uv run python scripts/apply_archetype_themes.py
uv run python scripts/validate_archetype_biases.py
pytest tests/test_archetypes.py tests/test_generator.py
```

### SPI

Hand-edit JSON (no themes apply script). Primaries are absolute maps; subtypes use additive `modifiers`.

| File | Role |
|------|------|
| `wod_chargen/games/spi/data/archetypes/<id>.json` | Primary biases |
| `wod_chargen/games/spi/data/archetypes/<id>/<sub>.json` | Subtype deltas |
| `wod_chargen/games/spi/data/divisions.json` | Division leans |
| `wod_chargen/games/spi/data/factions.json` | Faction leans |
| `wod_chargen/games/spi/data/trait_tags.json` | Merit theme tags |

```bash
uv run python scripts/validate_spi_archetypes.py
uv run python scripts/validate_spi_merit_biases.py
pytest tests/test_spi_generator.py tests/test_spi_archetypes.py tests/test_spi_trait_biases.py
```

**Rules / ranges:** [`docs/archetype-weight-guidelines.md`](docs/archetype-weight-guidelines.md)  
**LotN build math:** [`docs/creation-weighting-strategy.md`](docs/creation-weighting-strategy.md)  
**SPI design:** [`docs/spi-structure.md`](docs/spi-structure.md)

## UI and picker config

Edit standalone JSON — not inline Python or wizard strings:

| File | Purpose |
|------|---------|
| `wod_chargen/games/catalog.json` | Venue picker cards |
| `wod_chargen/games/lotn_v5/data/wizard_ui.json` | LotN wizard steps / type picker |
| `wod_chargen/games/lotn_v5/data/faction_picker.json` | Faction grid order/titles |
| `wod_chargen/games/lotn_v5/data/clans.json` | Clan + thin-blood lineage cards |
| `wod_chargen/games/spi/data/wizard_ui.json` | SPI wizard steps / copy keys |
| `wod_chargen/venues/picker.json` | Starting XP profile ids per Venue |
| `wod_chargen/venues/<id>.json` | XP profile labels and rules |

Player-facing Build guide copy: `app/strategy_content_lotn.py`, `app/strategy_content_spi.py`.

Regenerate the PyScript file manifest after adding Python or JSON under `app/` or `wod_chargen/`:

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
