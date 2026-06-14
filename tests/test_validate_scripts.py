"""Smoke tests for offline validation scripts."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_validate_archetype_biases_script():
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts/validate_archetype_biases.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
