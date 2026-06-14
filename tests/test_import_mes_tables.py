"""MES spreadsheet import smoke tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.import_mes_tables import FALLBACK_XLSX, main

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "wod_chargen" / "games" / "lotn_v5" / "data"


@pytest.fixture(scope="module")
def mes_workbook_available() -> None:
    pytest.importorskip("openpyxl")
    if not FALLBACK_XLSX.exists():
        pytest.skip(f"MES workbook not found at {FALLBACK_XLSX}")


def test_import_mes_tables_dry_run_parses_workbook(mes_workbook_available: None):
    assert main(["--dry-run"]) == 0


def test_mes_canonical_data_on_disk():
    merits = json.loads((DATA / "merits_flaws.json").read_text(encoding="utf-8"))
    assert len(merits["merits"]) == 28
    assert len(merits["flaws"]) >= 38
    assert any(m["id"] == "iron_gullet" for m in merits["merits"])
    assert any(f["id"] == "enemy" for f in merits["flaws"])

    loresheets = json.loads((DATA / "loresheets.json").read_text(encoding="utf-8"))
    assert len(loresheets["loresheets"]) == 24

    disciplines = json.loads((DATA / "discipline_powers.json").read_text(encoding="utf-8"))
    power_count = sum(d["power_count"] for d in disciplines["disciplines"])
    assert power_count >= 270

    predators = json.loads((DATA / "predator_types.json").read_text(encoding="utf-8"))
    assert len(predators["types"]) == 13

    formulas = json.loads((DATA / "thin_blood_formulas.json").read_text(encoding="utf-8"))
    assert len(formulas["formulas"]) == 6
