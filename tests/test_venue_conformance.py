"""Parameterized Venue conformance matrix (LotN + SPI)."""

from __future__ import annotations

import pytest

from app.strategy_content import UnknownVenueError, resolve_guide
from app.venue_dispatch import IMPLEMENTED_UI_GAMES, weight_data_for
from wod_chargen.core.xp_log_format import format_xp_log
from wod_chargen.games.registry import get_game, load_game_catalog, registered_game_ids
from wod_chargen.venues import load_venue, resolve_xp_budget


@pytest.mark.parametrize("game_id", sorted(IMPLEMENTED_UI_GAMES))
def test_registered_and_catalog_implemented(game_id: str):
    catalog = load_game_catalog()
    assert game_id in catalog
    assert catalog[game_id]["implemented"] is True
    assert game_id in registered_game_ids()
    system = get_game(game_id)
    assert system.id == game_id
    assert system.label
    assert system.get_wizard_steps()
    assert system.get_xp_profile_picker()


@pytest.mark.parametrize(
    "game_id,venue_id,options,expected_xp",
    [
        ("lotn_v5", "fixed_100", {}, 20),
        ("spi", "fixed_35", {}, 35),
        ("spi", "mes_spi", {"approval": "2026-01"}, 35),
    ],
)
def test_xp_profile_resolve(game_id: str, venue_id: str, options: dict, expected_xp: int):
    system = get_game(game_id)
    ids = {v["id"] for v in system.get_xp_profile_picker()}
    assert venue_id in ids
    xp, _ = resolve_xp_budget(venue_id, options)
    assert xp == expected_xp


@pytest.mark.parametrize(
    "game_id,venue_id,options",
    [
        (
            "lotn_v5",
            "fixed_100",
            {
                "type": "vampire",
                "clan": "brujah",
                "arch": "diplomat",
                "sub": "silver_tongue",
            },
        ),
        (
            "spi",
            "fixed_35",
            {
                "division": "adventure",
                "faction": "higher_ground",
                "archetype": "investigator",
                "affinity": "mage",
                "multi_affinity": False,
            },
        ),
    ],
)
def test_generate_and_sheet(game_id: str, venue_id: str, options: dict):
    system = get_game(game_id)
    venue = load_venue(venue_id)
    result = system.generate(11, options, venue)
    assert result.game_id == game_id
    assert result.xp_remaining >= 0
    sheet = system.build_sheet_model(result)
    assert sheet is not None
    # XP log formatting should not raise for either Venue
    text = format_xp_log(result.xp_log)
    assert "Purchases" in text or text == "No XP purchases."


@pytest.mark.parametrize(
    "game_id,title_fragment",
    [
        ("lotn_v5", "How Characters Are Built"),
        ("spi", "SPI"),
    ],
)
def test_strategy_guide_titles(game_id: str, title_fragment: str):
    guide = resolve_guide(game_id)
    assert title_fragment in guide["title"]
    assert guide["sections"]


@pytest.mark.parametrize("game_id", sorted(IMPLEMENTED_UI_GAMES))
def test_weight_map_overview_tree(game_id: str):
    data = weight_data_for(game_id)
    tree = data.build_tree("archetype", "overview")
    assert tree.get("children") or tree.get("name")


def test_unknown_guide_fails_closed():
    with pytest.raises(UnknownVenueError):
        resolve_guide("werewolf_apocalypse")


def test_unknown_weight_data_fails_closed():
    with pytest.raises(UnknownVenueError):
        weight_data_for("werewolf_apocalypse")
