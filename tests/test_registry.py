"""Game registry tests."""

import pytest

from wod_chargen.games.registry import get_game


def test_get_game_returns_lotn_v5():
    game = get_game("lotn_v5")
    assert game.id == "lotn_v5"


def test_get_game_unknown_raises():
    with pytest.raises(ValueError, match="Unknown game"):
        get_game("werewolf_apocalypse")
