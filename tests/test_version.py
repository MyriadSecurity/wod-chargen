"""App version is consistent across packaging and runtime."""

from __future__ import annotations

import re
from pathlib import Path

import wod_chargen
from wod_chargen.core.share import ENGINE_VERSION

ROOT = Path(__file__).resolve().parent.parent


def test_engine_version_matches_package():
    assert ENGINE_VERSION == wod_chargen.__version__


def test_pyproject_reads_same_version():
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'path = "wod_chargen/__init__.py"' in text
    init = (ROOT / "wod_chargen" / "__init__.py").read_text(encoding="utf-8")
    match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', init)
    assert match
    assert match.group(1) == wod_chargen.__version__
