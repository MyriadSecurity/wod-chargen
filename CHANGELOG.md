# Changelog

All notable changes to **wod-chargen** are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/). Versions use [Semantic Versioning](https://semver.org/).

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

[0.2.0]: https://github.com/gscott/wod-chargen/releases/tag/v0.2.0
[0.1.0]: https://github.com/gscott/wod-chargen/releases/tag/v0.1.0
