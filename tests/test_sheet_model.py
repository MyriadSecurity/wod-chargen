"""Sheet view-model builds from generation results."""

from wod_chargen.games.lotn_v5.generator import generate_character
from wod_chargen.games.lotn_v5.sheet_model import SheetModel, build_sheet_model
from wod_chargen.games.lotn_v5.system import LotnV5System
from tests.support.fixtures import CUSTOM_XP_VENUE, ghoul_opts, load_venue, opts, thin_blood_opts


def _venue():
    return load_venue()


def _custom_xp_venue():
    return load_venue(CUSTOM_XP_VENUE)


def test_build_sheet_model_vampire():
    result = generate_character(42, opts(), _venue())
    model = build_sheet_model(result)
    assert isinstance(model, SheetModel)
    assert model.header.meta
    type_labels = {item.label: item.value for item in model.header.meta}
    assert type_labels["Type"] == "Vampire"
    assert type_labels["Clan"] == "Brujah"
    assert type_labels["Archetype"]
    assert model.attributes is not None
    assert model.skills is not None
    assert len(model.attributes.columns) == 3
    assert len(model.skills.columns) == 3


def test_build_sheet_model_ghoul():
    result = generate_character(88, ghoul_opts(), _custom_xp_venue())
    model = LotnV5System().build_sheet_model(result)
    assert isinstance(model, SheetModel)
    meta = {item.label: item.value for item in model.header.meta}
    assert meta["Type"] == "Ghoul"
    assert meta["Domitor"]
    assert "Generation" not in meta
    if model.disciplines:
        assert model.disciplines.title == "Domitor Disciplines"
        for card in model.disciplines.cards:
            assert card.rating.max_dots == 1


def test_build_sheet_model_thin_blood():
    result = generate_character(7, thin_blood_opts(), _custom_xp_venue())
    model = build_sheet_model(result)
    assert isinstance(model, SheetModel)
    meta = {item.label: item.value for item in model.header.meta}
    assert meta["Type"] == "Thin-Blood"
    assert "Generation" in meta
    assert model.header.clan_symbol_src is None
