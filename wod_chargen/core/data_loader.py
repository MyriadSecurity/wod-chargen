"""Load JSON data via importlib.resources (pytest + Pyodide compatible)."""

from __future__ import annotations

import json
from functools import lru_cache
from importlib import resources
from typing import Any


def load_json(package: str, resource: str) -> Any:
    """Load a JSON file from a package's data tree."""
    with resources.files(package).joinpath(resource).open("r", encoding="utf-8") as fh:
        return json.load(fh)


@lru_cache(maxsize=128)
def load_json_cached(package: str, resource: str) -> Any:
    return load_json(package, resource)


def clear_cache() -> None:
    load_json_cached.cache_clear()
