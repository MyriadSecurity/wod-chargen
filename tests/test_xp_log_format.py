"""XP log formatting tests."""

from __future__ import annotations

from wod_chargen.core.models import XpLogEntry
from wod_chargen.core.xp_log_format import format_xp_log
from wod_chargen.games.lotn_v5.generator import generate_character


def _entry(**kwargs) -> XpLogEntry:
    defaults = {
        "item": "persuasion",
        "category": "skill",
        "spend_group": "skills",
        "new_level": 2,
        "cost": 2,
        "group_weight": 1.5,
        "item_bias": 1.2,
        "clan_factor": 1.0,
        "efficiency_bias": 1.0,
        "roll": 0.42,
        "score": 0.50,
        "source": "archetype",
    }
    defaults.update(kwargs)
    return XpLogEntry(**defaults)


def test_format_xp_log_groups_by_category_and_shows_level():
    text = format_xp_log(
        [
            _entry(item="persuasion", category="skill", new_level=2, cost=2),
            _entry(item="strength", category="attribute", spend_group="physical_attrs", new_level=3, cost=4),
            _entry(item="persuasion", category="skill", new_level=3, cost=6),
        ]
    )
    assert "Purchases" in text
    assert "── Skills" in text
    assert "  persuasion → 2 (2 XP)" in text
    assert "  persuasion → 3 (6 XP)" in text
    assert "── Attributes" in text
    assert "  strength → 3 (4 XP)" in text
    assert text.index("── Attributes") < text.index("── Skills")
    assert "group_w=" not in text
    assert "Debug (internal weights)" not in text


def test_xp_log_entries_include_new_level():
    from wod_chargen.core.data_loader import load_json_cached

    venue = load_json_cached("wod_chargen.venues", "mes_end_to_dawn.json")
    opts = {
        "type": "vampire",
        "clan": "brujah",
        "arch": "diplomat",
        "sub": "silver_tongue",
        "approval": "2026-06",
    }
    result = generate_character(424242, opts, venue)
    assert result.xp_log
    for entry in result.xp_log:
        assert entry.new_level >= 1
        assert entry.spend_group
