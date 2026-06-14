"""LotnV5System facade tests."""

from wod_chargen.core.data_loader import load_json_cached
from wod_chargen.games.lotn_v5.paths import DATA_PKG
from wod_chargen.games.lotn_v5.system import LotnV5System


def test_wizard_steps_match_ui_json():
    system = LotnV5System()
    ui = load_json_cached(DATA_PKG, "wizard_ui.json")
    assert system.get_wizard_steps() == ui["wizard_steps"]
