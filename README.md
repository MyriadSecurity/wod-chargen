# wod-chargen

Browser-only **World of Darkness / MET** procedural character generator.

- **Stack:** PyScript + pyscript.web + Tailwind CSS
- **Engine:** Python (`wod_chargen/`) — tested with pytest
- **Venues:** LotN V5 (`lotn_v5`), SPI (`spi`)
- **Deploy:** GitHub Pages (static)
- **Version:** see `CHANGELOG.md` and `wod_chargen/__init__.py` (`__version__`)
- **Source:** [github.com/MyriadSecurity/wod-chargen](https://github.com/MyriadSecurity/wod-chargen)
- **Contact:** [contact.gsco@gmail.com](mailto:contact.gsco@gmail.com)

## Local development

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
python scripts/dev_server.py
# Open http://localhost:8080/
```

## Docs

| Doc | Use when |
|-----|----------|
| [`docs/where-to-edit.md`](docs/where-to-edit.md) | Finding which file to change |
| [`CONTRIBUTING.md`](CONTRIBUTING.md) | Weights, UI JSON, validate commands |
| [`docs/archetype-weight-guidelines.md`](docs/archetype-weight-guidelines.md) | Bias ranges and resolution |
| [`docs/spi-structure.md`](docs/spi-structure.md) | SPI design / product decisions |
| [`docs/creation-weighting-strategy.md`](docs/creation-weighting-strategy.md) | LotN creation + XP pipeline |
| [`AGENTS.md`](AGENTS.md) | Agent / cloud environment notes |
| [`docs/VERSIONING.md`](docs/VERSIONING.md) | Versioning |

## PyScript version

Pinned in `pyscript.json`. Re-test after bumping the CDN version.

## Dark Pack

This project uses World of Darkness material under the [Dark Pack Agreement](https://www.paradoxinteractive.com/games/world-of-darkness/community/dark-pack-agreement). See `NOTICES.md`.
