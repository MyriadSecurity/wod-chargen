"""MES spreadsheet import smoke tests."""

from __future__ import annotations

import json
from pathlib import Path

from scripts.import_mes_tables import main

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "wod_chargen" / "games" / "lotn_v5" / "data"


def test_import_mes_tables_dry_run_parses_workbook():
    assert main(["--dry-run"]) == 0


def test_mes_import_artifacts_on_disk():
    manifest = DATA / "import_manifest.json"
    assert manifest.exists(), "Run scripts/import_mes_tables.py once to populate MES catalogs"

    summary = json.loads(manifest.read_text(encoding="utf-8"))
    files = summary["files"]
    assert files["merits_flaws.json"]["merits"] == 28
    assert files["merits_flaws.json"]["flaws"] >= 38
    assert files["loresheets.json"]["loresheets"] == 24
    assert files["discipline_powers.json"]["powers"] >= 270
    assert files["predator_catalog.json"]["predators"] == 13

    merits = json.loads((DATA / "merits_flaws.json").read_text(encoding="utf-8"))
    assert any(m["id"] == "iron_gullet" for m in merits["merits"])
    assert any(f["id"] == "enemy" for f in merits["flaws"])

    legacy = json.loads((DATA / "merits.json").read_text(encoding="utf-8"))
    assert "iron_gullet" in legacy["merits"]
    assert "acute_senses" not in legacy["merits"]

    formulas = json.loads((DATA / "thin_blood_formulas.json").read_text(encoding="utf-8"))
    assert len(formulas["formulas"]) == 6
