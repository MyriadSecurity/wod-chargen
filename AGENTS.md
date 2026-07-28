# AGENTS.md

## Cursor Cloud specific instructions

### What this project is
`wod-chargen` is a **browser-only** World of Darkness / MET character generator. There is **no backend, no database, and no external API** at runtime. The UI runs entirely client-side via **PyScript** (Python in the browser via WebAssembly). The Python engine lives in `wod_chargen/` and the PyScript UI in `app/`. See `README.md` and `CONTRIBUTING.md` for the standard commands.

### Environment (keep it simple)
- Running the app needs **only system Python** — `scripts/dev_server.py` is stdlib-only.
- Cloud install is a no-op (`.cursor/environment.json`). A terminal auto-starts:
  `python3 scripts/dev_server.py --bind 0.0.0.0 --port 8080` → http://localhost:8080/
- Optional for tests/lint: `uv sync --extra dev --group dev` (or `python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"`).
- For browser smoke tests only: `.venv/bin/playwright install chromium`
- Runtime `dependencies` in `pyproject.toml` are empty — the browser loads PyScript/Tailwind/D3 from CDNs.

### Running the app (dev)
- `python3 scripts/dev_server.py` then open `http://localhost:8080/`
- The server only adds `Cache-Control: no-store`; PyScript caches aggressively and `file://` will not work.
- **Internet access is required on first browser load** (CDN assets). PyScript takes ~15s to boot before the wizard appears.

### Testing
- After installing the `dev` extra: `.venv/bin/pytest -q`
- Browser smoke tests (`tests/test_browser_smoke.py`) start their own HTTP server via `site_base_url` and need Playwright Chromium.
- CI runs `scripts/validate_archetypes.py`, `scripts/validate_archetype_biases.py`, then `pytest -q`. `WARN:` lines about extreme biases are expected (exit 0).

### Linting
- `ruff` is in the `dev` extra but not CI. Pre-existing findings exist; do not treat them as regressions.

### Editing packaged data/code
- After adding/changing `.py`/`.json` under `app/` or `wod_chargen/`, regenerate the manifest:
  `python3 scripts/generate_pyscript_config.py`
