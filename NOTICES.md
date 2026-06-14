# Dark Pack compliance

This project uses World of Darkness intellectual property under the [Dark Pack Agreement](https://www.paradoxinteractive.com/games/world-of-darkness/community/dark-pack-agreement).

## Required elements

- [x] Dark Pack logo in footer (`static/img/dark-pack-logo.png`)
- [x] Required Paradox legal notice in footer
- [x] Unofficial fan project disclaimer
- [x] Link to Dark Pack Agreement

## Local-only assets

- LoTN pocket PDF under `reference/lotn_v5/` — **not** distributed in the public repository

## Clan symbols

Official V5 clan symbol PNGs in `static/img/clans/` were sourced from the
[VTM Wiki](https://vtm.paradoxwikis.com/Category:Clan_symbols) (Paradox Interactive).
Re-fetch with `uv run python scripts/fetch_clan_symbols_wiki.py` (requires Playwright).
Thin-blood uses a local SVG placeholder (`scripts/generate_clan_symbols.py`) — no wiki asset exists.

## Notice text (footer)

Part of the materials are fictitious and claimed under the Dark Pack license. This is an unofficial fan project. See the Dark Pack Agreement for terms.
