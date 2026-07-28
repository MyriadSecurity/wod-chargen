# Changelog

All notable changes to **wod-chargen** are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/). Versions use [Semantic Versioning](https://semver.org/).

## [0.3.0] - 2026-07-28

### Added

- **SPI Venue** (`spi`): Society of Paranormal Investigators oneshot/NPC sheet generator
  - Wizard: XP profile → Division → Faction → Archetype → Subtype → Affinity → generate
  - CoD 2e traits (Presence, Weaponry), Affinity tracks, Integrity cap, derived advantages
  - Eight primaries × subtypes with bias packs; Division / Faction soft leans
  - Flat XP costs (incl. Supernatural Resistance 2/dot); prereq bundling; multi-Affinity toggle
  - Sanctioned merit allowlist; merit theme tags (`trait_tags.json`)
  - Venue-scoped Build guide and Weight Map
- Maintainer docs: `docs/where-to-edit.md`, SPI/LotN data package READMEs, expanded weight guidelines

### Changed

- Venue dispatch for guide / weight-map / sheet rendering (fail-closed for unknown games)
- SPI Weight Map: navigable overview nodes, safe id defaults, Affinity lean profiles
- CONTRIBUTING / README / AGENTS point at the where-to-edit index

### Fixed

- SPI merit XP: Supernatural Resistance at 2 XP/dot; fixed-rating packages no longer crushed by jump efficiency
- Extra Touchstone omitted from oneshot generation (Touchstones out of sheet scope)
- Weight Map subtype dropdown ignored when LotN `sub` leftover overwrote SPI `arch:sub` ids

## [0.2.0] - 2026-06-13

### Added

- Loresheets: procedural selection and XP spend for LoTN V5 loresheet benefits
- Predator types with background and discipline weighting
- Archetype weight map explorer for tuning and debugging procedural bias
- Thin-blood merits, alchemical disciplines, and formula handling
- Clan symbols in the wizard and character sheet
- Custom XP venue (`custom_xp`) for non-MES tables
- Benefit packages and conviction support in generation
- Sheet view model with improved on-screen layout and print styles
- Clan-feature integration into archetype weight mapping
- Discipline expressions and clan discipline adaptation rules
- Archetype weight guidelines documentation (`docs/archetype-weight-guidelines.md`)
- Expanded pytest coverage across engine modules, share URLs, and browser smoke tests
- Favicon, logo, and footer version display

### Changed

- Share URLs omit optional `schema` param by default; missing `schema` decodes as `0.1`
- Removed one-time migration scripts and unused MES import artifact JSON; import now writes only canonical runtime data
- Generator split into focused modules (`merits_flaws`, `xp_purchases`, `predators`, `loresheets`, `trait_biases`, `sheet_model`, and others)
- Wizard navigation, archetype labels, and subtype presentation polish
- Ghoul power mechanics and discipline handling
- XP strategy, backgrounds, and MES End-to-Dawn chart data
- Catalog tagline updated for Laws of the Night V5 (2023)

### Fixed

- Infinite loading on HTTP custom domain (GitHub Pages)
- Thin-blood discipline caps and XP calculation edge cases
- Missing Thin Blood clan symbol asset
- Generic XP pool assignment moved to base book XP

## [0.1.0] - 2026-06-13

### Added

- Browser-only PyScript UI for Laws of the Night V5 (`lotn_v5`) character generation
- 12 primary archetypes with 44 subtypes; vampire, ghoul, and thin-blood creation paths
- Procedural XP spend with archetype-weighted two-stage purchase (attributes, skills, backgrounds, disciplines, merits)
- Share URLs (schema 0.1), character sheet renderer, JSON export, print styles
- MES End-to-Dawn venue XP chart; pytest suite (engine, manifest, browser smoke)
- GitHub Actions: CI tests and GitHub Pages deploy
- `scripts/dev_server.py` for local no-cache static serving

### Fixed

- Creation pool rules: one assignment per trait; highest-to-lowest pick ordering
- Rating caps (5 dots default; thin-blood discipline/formula limits)
- PyScript boot issues (`js.null`, manifest sync, cache busting)

[0.3.0]: https://github.com/gscott/wod-chargen/releases/tag/v0.3.0
[0.2.0]: https://github.com/gscott/wod-chargen/releases/tag/v0.2.0
[0.1.0]: https://github.com/gscott/wod-chargen/releases/tag/v0.1.0
