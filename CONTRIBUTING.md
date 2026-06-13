# Contributing

## Rules reference

- **SRD (web):** [One World of Darkness — Laws of the Night](https://www.oneworldofdarkness.com/laws-of-the-night/) — index at `reference/lotn_v5/SRD_INDEX.md`; add to Cursor via `reference/lotn_v5/CURSOR_DOCS.md`
- **Local PDF:** copy to `reference/lotn_v5/` (gitignored). See `reference/README.md`.

## Tuning archetype weights

**12 primaries** (11 for vampire/ghoul + Alchemist for thin-blood). Merges: Diplomat (was Face+Diplomat), Enforcer (was Bruiser+Enforcer), Predator (was Hunter+Beast), Criminal (absorbed Survivor).

Archetypes use **two JSON layers** (see `archetypes/_schema.json`):

1. **Base:** `archetypes/<id>.json` — core `weights`, `attribute_biases`, `skill_biases`, `discipline_biases`
2. **Sub-archetype modifiers:** `archetypes/<id>/<sub_id>.json` — additive `modifiers` applied on top of the base

```json
{
  "id": "silver_tongue",
  "label": "Silver Tongue",
  "modifiers": {
    "weights": { "skills": 0.3 },
    "skill_biases": { "persuasion": 0.5 },
    "discipline_biases": { "presence": 0.3 }
  }
}
```

Validate and test:

```bash
source .venv/bin/activate
python scripts/validate_archetypes.py
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

4. Reload the app in your browser to compare builds (use the same seed via share URL)

Regenerate PyScript file manifest after adding Python or JSON under `app/` or `wod_chargen/`:

```bash
python scripts/generate_pyscript_config.py
pytest tests/test_pyscript_manifest.py
```

`test_pyscript_manifest.py` fails if `pyscript.toml` is stale or missing files the browser must load (e.g. new `app/components/*.py`).

## Local dev server

PyScript aggressively caches `.py` files. After pulling changes, a stale `share.py` (or other module) can cause import errors even though disk sources are correct. Prefer the no-cache dev server:

```bash
python scripts/dev_server.py
# open http://localhost:8080/
```

If you use `python -m http.server` instead, hard-refresh (Ctrl+Shift+R) after updates, or restart the server and clear site data for localhost.

After changing packaged files, regenerate the manifest (updates `index.html` cache-bust query on `main.py` and `pyscript.toml`):

```bash
python scripts/generate_pyscript_config.py
pytest
```


1. Add `your_archetype.json` base file under `archetypes/`
2. Add **2–4** subtype files under `archetypes/<id>/` — each must be a clearly distinct theme (no filler to hit a count)
2. Validate skill/discipline keys against `skills.json` / `disciplines.json`
3. Optional: `"allowed_types": ["thin_blood"]` to restrict by character type
4. Run full test suite before opening a PR
