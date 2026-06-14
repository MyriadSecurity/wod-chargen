"""XP log formatting tests."""

from __future__ import annotations

from wod_chargen.core.models import XpLogEntry
from wod_chargen.core.xp_log_format import format_xp_log


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


def test_format_xp_log_ghoul_power_uses_display_label():
    text = format_xp_log(
        [
            _entry(
                item="feral_whispers",
                category="ghoul_power",
                spend_group="disciplines",
                new_level=1,
                cost=10,
            ),
        ]
    )
    assert "── Discipline Powers" in text
    assert "feral_whispers" not in text
    assert "Feral Whispers" in text
    assert "(Animalism)" in text

