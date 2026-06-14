# Versioning

## Single source of truth

Application version lives in one place:

```python
# wod_chargen/__init__.py
__version__ = "0.1.0"
```

`pyproject.toml` reads it via Hatch (`[tool.hatch.version]`).  
`wod_chargen.core.share.ENGINE_VERSION` and generation results use the same value.

Share URL **schema** (`0.1`) is separate from app semver — bump schema only when share payload shape changes. Generated share links omit `schema` by default; decode treats a missing param as `0.1`.

## Release checklist

1. Update `wod_chargen/__init__.py` → `__version__`
2. Add a `CHANGELOG.md` section for the release
3. Run `python scripts/generate_pyscript_config.py` if packaged files changed
4. Run `pytest`
5. Commit, tag `vX.Y.Z`, push tag

```bash
git tag -a v0.1.0 -m "wod-chargen 0.1.0"
git push origin main --tags
```

## Semver guidance

- **MAJOR** — breaking share schema or incompatible saved URLs
- **MINOR** — new archetypes, games, venues, or user-visible features
- **PATCH** — bug fixes, data tuning, tests, docs
