# AGENTS.md

## Cursor Cloud specific instructions

### What this project is
`wod-chargen` is a **browser-only** World of Darkness / MET character generator. There is **no backend, no database, and no external API** at runtime. The UI runs entirely client-side via **PyScript** (Python in the browser via WebAssembly). The Python engine lives in `wod_chargen/` and the PyScript UI in `app/`. See `README.md` and `CONTRIBUTING.md` for the standard commands.

### Environment
- Python is managed in a local virtualenv at `.venv` (gitignored). The startup update script creates it and installs `.[dev]` plus the Playwright Chromium browser. Prefix commands with `.venv/bin/` (e.g. `.venv/bin/pytest`) or activate with `source .venv/bin/activate`.
- Runtime `dependencies` in `pyproject.toml` are intentionally empty — everything the app needs at runtime is loaded in-browser from CDNs.

### Running the app (dev)
- Start the static no-cache dev server, then open `http://localhost:8080/`:
  `.venv/bin/python scripts/dev_server.py`
- The dev server exists only to serve static files with `Cache-Control: no-store`; PyScript caches `.py`/`.json` modules aggressively and `file://` will not work.
- **Internet access is required on first browser load**: the page pulls PyScript 2024.11.1, Tailwind, and D3 from CDNs (pinned in `pyscript.json` / `index.html`). PyScript takes ~15s to boot in the browser before the wizard appears.

### Testing
- Full suite: `.venv/bin/pytest -q` (pure-Python logic tests + Playwright browser smoke tests).
- Browser smoke tests (`tests/test_browser_smoke.py`) auto-start their own in-process HTTP server via the `site_base_url` fixture — no manual dev server needed — and require the Playwright Chromium browser to be installed.
- CI (`.github/workflows/test.yml`) runs `scripts/validate_archetypes.py`, `scripts/validate_archetype_biases.py`, then `pytest -q`. The validate scripts print many `WARN:` lines about "extreme" biases; these are expected and non-fatal (exit 0).

### Linting
- `ruff` is installed via the `dev` extra but is **not** run in CI, and the current tree has pre-existing ruff findings. Run `.venv/bin/ruff check .` if needed, but do not treat existing findings as regressions from your changes.

### Editing packaged data/code
- After adding or changing any `.py`/`.json` under `app/` or `wod_chargen/`, regenerate the PyScript file manifest or `tests/test_pyscript_manifest.py` will fail:
  `.venv/bin/python scripts/generate_pyscript_config.py`
