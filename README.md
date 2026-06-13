# wod-chargen

Browser-only **World of Darkness / MET** procedural character generator.

- **Stack:** PyScript + pyscript.web + Tailwind CSS
- **Engine:** Python (`wod_chargen/`) — tested with pytest
- **v1 game:** BNS Laws of the Night V5 (`lotn_v5`)
- **Deploy:** GitHub Pages (static)
- **Version:** see `CHANGELOG.md` and `wod_chargen/__init__.py` (`__version__`)

## Local development

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
python scripts/dev_server.py
# Open http://localhost:8080/
```

Versioning policy: `docs/VERSIONING.md`.

## PyScript version

Pinned in `pyscript.json`. Re-test after bumping the CDN version.

## Dark Pack

This project uses World of Darkness material under the [Dark Pack Agreement](https://www.paradoxinteractive.com/games/world-of-darkness/community/dark-pack-agreement). See `NOTICES.md`.

## Reference PDF

Copy `laws_of_the_night_pocket.pdf` to `reference/lotn_v5/` locally (gitignored). See `reference/README.md`.
