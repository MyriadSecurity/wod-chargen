# Changelog

All notable changes to **wod-chargen** are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/). Versions use [Semantic Versioning](https://semver.org/).

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

[0.1.0]: https://github.com/gscott/wod-chargen/releases/tag/v0.1.0
