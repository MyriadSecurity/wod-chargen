# Architecture Cleanup Implementation Plan

> **For agentic workers:** Use subagent-driven-development or executing-plans to implement task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reduce god files, eliminate drift between abstractions and usage, and prepare wod-chargen for a second game system — without changing generation behavior.

**Architecture:** Three independently shippable phases. Phase A is pure hygiene (constants, fixtures, dead code). Phase B splits the generator and wires the existing game registry end-to-end. Phase C is larger refactors (wizard decomposition, module boundary cleanup, sheet view-model).

**Tech Stack:** Python 3.12, pytest, PyScript/pyscript.web, packaged JSON via `importlib.resources`, static GitHub Pages deploy.

**Validation baseline (run before and after every phase):**

```bash
cd /home/gscott/Projects/wod-chargen
source .venv/bin/activate  # if present
pytest -q
python scripts/validate_archetypes.py
python scripts/generate_pyscript_config.py
pytest tests/test_pyscript_manifest.py tests/test_app_boot.py -q  # browser bundle parity
```

---

## Phase A — Foundation (no behavior change)

**Ship criteria:** All tests pass; wizard flow unchanged; smaller diff surface for later phases.

### Task A1: Centralize data paths and defaults

**Files:**
- Create: `wod_chargen/games/lotn_v5/paths.py`
- Create: `wod_chargen/defaults.py`
- Modify: all modules with `DATA_PKG = "wod_chargen.games.lotn_v5.data"` (15 files)
- Test: `tests/test_import_boundary.py` (should still pass)

- [ ] **Step 1:** Create `paths.py`:

```python
DATA_PKG = "wod_chargen.games.lotn_v5.data"
GAMES_PKG = "wod_chargen.games"
VENUE_PKG = "wod_chargen.venues"
```

- [ ] **Step 2:** Create `defaults.py`:

```python
DEFAULT_VENUE_ID = "mes_end_to_dawn"
DEFAULT_GAME_ID = "lotn_v5"
```

- [ ] **Step 3:** Replace local `DATA_PKG` / `DATA =` literals with `from wod_chargen.games.lotn_v5.paths import DATA_PKG` in engine modules and `app/components/sheet.py`, `app/weight_map_data.py`.
- [ ] **Step 4:** Update `LotnV5System` in `system.py` to import from `paths.py` instead of redefining constants.
- [ ] **Step 5:** Run `pytest -q`.

### Task A2: Shared test fixtures

**Files:**
- Modify: `tests/conftest.py`
- Modify: 12 test files that define local `_venue()` / `_opts()`

Affected test files:
`test_generator.py`, `test_ghoul.py`, `test_caitiff.py`, `test_thin_blood_merits.py`, `test_disciplines.py`, `test_xp_strategy.py`, `test_share.py`, `test_clan_discipline_adapt.py`, `test_archetype_weights.py`, `test_merits_flaws.py`, `test_backgrounds.py`, `test_generation.py`

- [ ] **Step 1:** Add to `conftest.py`:

```python
@pytest.fixture
def venue():
    return load_json_cached("wod_chargen.venues", "mes_end_to_dawn.json")

@pytest.fixture
def opts_factory():
    def _opts(**kwargs):
        base = {"type": "vampire", "clan": "brujah", "arch": "diplomat",
                "sub": "silver_tongue", "approval": "2026-06"}
        base.update(kwargs)
        return base
    return _opts
```

- [ ] **Step 2:** Migrate one test file (`test_generator.py`) to use fixtures; run `pytest tests/test_generator.py -q`.
- [ ] **Step 3:** Migrate remaining 11 files; delete local `_venue` / `_opts` helpers.
- [ ] **Step 4:** For tests that call `_opts()` many times without pytest injection, keep a module-level helper that delegates to a shared function in `tests/support/fixtures.py` if fixture injection is awkward — prefer one shared import over 12 copies.
- [ ] **Step 5:** Run full `pytest -q`.

### Task A3: Single wizard step source

**Files:**
- Modify: `app/wizard.py`
- Modify: `wod_chargen/games/lotn_v5/data/wizard_ui.json` (if needed to match actual flow)
- Test: `tests/test_app_boot.py`, manual smoke in dev server

**Current drift:**
- `BUILD_STEPS` in wizard: `venue, type, faction, …` (no `game`, no `results`)
- `wizard_ui.json`: `game, venue, type, …, generate, results`

- [ ] **Step 1:** Document actual wizard flow by reading `WizardApp` navigation (`_step_index`, `_advance`, `_render_step`). Decide canonical step list — likely drop unused `game`/`results` from JSON *or* add them to wizard if intended.
- [ ] **Step 2:** Remove `BUILD_STEPS` constant; replace with `self._system.get_wizard_steps()` filtered to steps the wizard actually renders (exclude `results` if handled separately).
- [ ] **Step 3:** Align `wizard_ui.json` `wizard_steps` with canonical list.
- [ ] **Step 4:** Add test in `tests/test_lotn_system.py` (new file):

```python
def test_wizard_steps_match_ui_json():
    system = LotnV5System()
    ui = load_json_cached(DATA_PKG, "wizard_ui.json")
    assert system.get_wizard_steps() == ui["wizard_steps"]
```

- [ ] **Step 5:** Run tests + dev server smoke.

### Task A4: Wire or remove dead registry code

**Files:**
- Modify: `app/wizard.py`
- Modify or delete: `app/component_registry.py`
- Create: `tests/test_registry.py`
- Modify: `wod_chargen/games/registry.py` (optional typing)

- [ ] **Step 1:** Write failing test:

```python
def test_get_game_returns_lotn_v5():
    game = get_game("lotn_v5")
    assert game.id == "lotn_v5"

def test_get_game_unknown_raises():
    with pytest.raises(ValueError):
        get_game("werewolf_apocalypse")
```

- [ ] **Step 2:** In wizard, replace `LotnV5System()` with `get_game(self.state.get("game", DEFAULT_GAME_ID))`; store as `self._system`.
- [ ] **Step 3:** Either import `component_registry.REGISTRY` in wizard/sheet for renderer dispatch, **or** delete `component_registry.py` and remove from `pyscript.toml` via regen script.
- [ ] **Step 4:** Run `python scripts/generate_pyscript_config.py` and manifest tests.

### Task A5: Prune PyScript bundle (import-only JSON)

**Files:**
- Modify: `scripts/generate_pyscript_config.py`
- Move (optional): legacy JSON → `wod_chargen/games/lotn_v5/data/imported/`
- Test: `tests/test_pyscript_manifest.py`, `tests/test_site_static.py`

**Candidates to exclude from browser bundle** (verify with ripgrep first — no runtime `load_json_cached` references):
- `merits.json`
- `background_catalog.json`, `predator_catalog.json`, `clans_table.json`
- `dyscrasias.json`, `equipment_qualities.json`, `xp_matrix.json`
- `import_manifest.json`

- [ ] **Step 1:** Grep each candidate; confirm zero runtime loads from `wod_chargen/` and `app/`.
- [ ] **Step 2:** Add `EXCLUDE_GLOBS` or `EXCLUDE_NAMES` to `generate_pyscript_config.py`.
- [ ] **Step 3:** Regenerate `pyscript.toml`; run manifest + static tests.
- [ ] **Step 4:** Note moved/excluded files in `CONTRIBUTING.md` one-liner if layout changes.

### Task A6: Archive one-off scripts

**Files:**
- Create: `scripts/archive/README.md`
- Move: one-off migration scripts (confirm via git log / comments)

- [ ] **Step 1:** Identify scripts with no references in CI, CONTRIBUTING, or other scripts.
- [ ] **Step 2:** Move to `scripts/archive/` with README listing purpose and last-used date.
- [ ] **Step 3:** No test changes required.

**Phase A commit message:** `refactor: centralize paths, fixtures, and wizard step config`

---

## Phase B — Generator split and registry completion

**Ship criteria:** `generate_character()` behavior identical; wizard calls `system.generate()`; generator.py under ~400 lines.

### Task B1: Extract XP purchase enumeration

**Files:**
- Create: `wod_chargen/games/lotn_v5/xp_purchases.py`
- Modify: `wod_chargen/games/lotn_v5/generator.py` (lines ~385–806)
- Create: `tests/test_xp_purchases.py`
- Test: full `pytest -q`

- [ ] **Step 1:** Copy `_enumerate_purchases` to `xp_purchases.py` as public `enumerate_purchases(...)`.
- [ ] **Step 2:** Write focused tests for 2–3 character types (vampire, ghoul, thin_blood) asserting candidate categories appear and respect caps — use fixed seed + mock char dict, no full generation.
- [ ] **Step 3:** Replace body in `generator.py` with import; run tests.
- [ ] **Step 4:** Verify `generator.py` line count dropped ~400 lines.

### Task B2: Extract base creation

**Files:**
- Create: `wod_chargen/games/lotn_v5/base_creation.py`
- Modify: `generator.py` (`_apply_base_creation`, dot assignment helpers)

- [ ] **Step 1:** Move `_apply_base_creation`, `_assign_dots*`, `_assign_one_dot_pick`, `_assign_one_discipline_pick` to `base_creation.py`.
- [ ] **Step 2:** Add `tests/test_base_creation.py` with one vampire + one ghoul smoke test (creation-only, xp=0).
- [ ] **Step 3:** `generator.py` retains `_empty_character`, `_resolve_caps`, `_apply_predator`, and `generate_character` orchestration.
- [ ] **Step 4:** Full pytest.

### Task B3: Wizard uses `system.generate()`

**Files:**
- Modify: `app/wizard.py` (replace direct `generate_character` import)

- [ ] **Step 1:** Change generation call site to `self._system.generate(seed, options, venue_config)`.
- [ ] **Step 2:** Remove direct `from ...generator import generate_character` from wizard if unused elsewhere in file.
- [ ] **Step 3:** Run `tests/test_app_boot.py` and share round-trip tests.

### Task B4: Shared trait catalog registry

**Files:**
- Create: `wod_chargen/games/lotn_v5/trait_catalog.py`
- Modify: `archetypes.py`, `predators.py`, `app/weight_map_data.py`

- [ ] **Step 1:** Extract common logic: load attributes, skills, disciplines, backgrounds IDs from JSON once.
- [ ] **Step 2:** Refactor `archetypes._registry_ids()` to use `trait_catalog.all_bias_keys()`.
- [ ] **Step 3:** Refactor predator validation and weight map ID listing.
- [ ] **Step 4:** Run `validate_archetypes.py` + archetype weight tests.

### Task B5: Promote private cross-imports

**Files:**
- Modify: `backgrounds.py` — export `can_add_dot` (drop leading underscore)
- Modify: `generator.py`, tests importing `_can_add_dot`
- Modify: `benefit_packages.py`, `predators.py` — extract public helpers to `wod_chargen/games/lotn_v5/package_grants.py`

- [ ] **Step 1:** Rename `_can_add_dot` → `can_add_dot`; update call sites.
- [ ] **Step 2:** Move predator grant helpers used by `benefit_packages` into `package_grants.py`.
- [ ] **Step 3:** Full pytest.

### Task B6: Targeted unit tests for core modules

**Files:**
- Create: `tests/test_spender.py`, `tests/test_costs.py`, `tests/test_benefit_packages.py`, `tests/test_lotn_system.py`

- [ ] **Step 1:** `test_costs.py` — table lookups for attribute/skill/discipline tiers.
- [ ] **Step 2:** `test_spender.py` — spend loop stops at budget, respects max iterations.
- [ ] **Step 3:** `test_benefit_packages.py` — one predator package + one loresheet package application.
- [ ] **Step 4:** `test_lotn_system.py` — picker methods return non-empty lists for vampire.

**Phase B commit message:** `refactor: split generator XP/base creation and complete game registry wiring`

---

## Phase C — UI decomposition and module boundaries

**Ship criteria:** Wizard split into navigable modules; backgrounds/merits cycle removed; sheet no longer imports raw JSON catalogs.

### Task C1: Wizard state vs views

**Files:**
- Create: `app/wizard_state.py` — state dict, URL encode/decode, validation
- Create: `app/views/venue.py`, `type.py`, `faction.py`, `archetype.py`, `predator.py`, `generate.py`
- Modify: `app/wizard.py` — thin coordinator (~200 lines)

- [ ] **Step 1:** Extract `WizardApp` state initialization and share URL logic to `wizard_state.py`.
- [ ] **Step 2:** Move one step's `_render_*` method to `app/views/venue.py`; wire from wizard.
- [ ] **Step 3:** Repeat for remaining steps one at a time; run browser smoke after each.
- [ ] **Step 4:** Delete duplicated label formatting — small `app/formatting.py` with `titleize_id(s)`.

### Task C2: Break backgrounds ↔ merits_flaws cycle

**Files:**
- Create: `wod_chargen/games/lotn_v5/background_rules.py`
- Modify: `backgrounds.py`, `merits_flaws.py`

Shared rules to extract:
- Haven advantage blocking
- Poor rating / sphere pick logic
- Modifier accounting shared between creation and XP

- [ ] **Step 1:** Map all lazy cross-imports with grep.
- [ ] **Step 2:** Move shared functions to `background_rules.py` with no imports from either parent module.
- [ ] **Step 3:** Replace lazy imports with direct imports from `background_rules`.
- [ ] **Step 4:** Full pytest + merits/backgrounds tests.

### Task C3: Sheet view-model

**Files:**
- Create: `wod_chargen/games/lotn_v5/sheet_model.py`
- Modify: `LotnV5System` — add `build_sheet_model(result) -> SheetModel`
- Modify: `app/components/sheet.py` — render from dataclass/dict DTO only

- [ ] **Step 1:** Define `SheetModel` (labels resolved, dot rows pre-computed, clan symbol paths).
- [ ] **Step 2:** Move JSON label lookups from `sheet.py` into `sheet_model.py`.
- [ ] **Step 3:** `render_lotn_v5_sheet(model)` — no engine imports except types.
- [ ] **Step 4:** Add engine-level test asserting model builds for vampire/ghoul/thin_blood results.

### Task C4: Weight map uses trait catalog

**Files:**
- Modify: `app/weight_map_data.py`

- [ ] **Step 1:** Replace duplicate catalog traversal with `trait_catalog` from Phase B.
- [ ] **Step 2:** Manual smoke: weight map renders in dev server.

**Phase C commit message:** `refactor: split wizard views, decouple sheet rendering, break backgrounds cycle`

---

## Execution Order and PR Strategy

| PR | Phase | Est. sessions | Risk |
|----|-------|---------------|------|
| 1 | A (Tasks A1–A6) | 1–2 | Low |
| 2 | B (Tasks B1–B3) | 1–2 | Medium — generator split |
| 3 | B (Tasks B4–B6) | 1 | Low–medium |
| 4 | C1 | 2–3 | Medium — UI |
| 5 | C2–C4 | 2–3 | High — cycle break |

**Do not start Phase C until Phase B generator split is stable.** Phase A can ship immediately.

---

## Out of Scope (defer)

- Werewolf / second game implementation
- DOM unit tests for sheet renderer
- pytest coverage reporting in CI
- Rewriting `scripts/build_loresheet_data.py` (archive only)
- Changing generation algorithms or SRD rules

---

## Decision Log

When completing a phase, add a line to second-brain `notes/decisions.md` if hub continuity matters:

```
2026-06-13 — wod-chargen architecture cleanup Phase A: centralized paths/defaults, shared test fixtures, wizard steps from JSON.
```
