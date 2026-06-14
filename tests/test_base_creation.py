"""Base creation phase tests."""

from wod_chargen.core.data_loader import load_json_cached
from wod_chargen.core.models import LogEntry
from wod_chargen.core.rng import SeededRng
from wod_chargen.games.lotn_v5.archetypes import effective_profile
from wod_chargen.games.lotn_v5.backgrounds import empty_backgrounds
from wod_chargen.games.lotn_v5.base_creation import apply_base_creation
from wod_chargen.games.lotn_v5.generator import generate_character
from wod_chargen.games.lotn_v5.paths import DATA_PKG as DATA
from tests.support.fixtures import ghoul_opts, load_venue, opts as vampire_opts


def test_apply_base_creation_assigns_vampire_dots():
    creation = load_json_cached(DATA, "creation.json")
    profile = effective_profile("diplomat", "silver_tongue", "vampire")
    char = {
        "character_type": "vampire",
        "clan": "brujah",
        "attributes": {},
        "skills": {},
        "disciplines": {},
        "backgrounds": empty_backgrounds(),
    }
    log: list[LogEntry] = []
    caps = {
        "attribute": 5,
        "skill": 5,
        "discipline": 5,
        "background": 3,
    }
    apply_base_creation(SeededRng(1), char, profile, creation, log, caps)
    assert sum(char["attributes"].values()) > 0
    assert sum(char["skills"].values()) > 0


def test_ghoul_creation_only_no_xp_spend():
    result = generate_character(42, {**ghoul_opts(), "xp": "0"}, load_venue("custom_xp"))
    assert result.character["character_type"] == "ghoul"
    assert result.xp_spent == 0


def test_vampire_creation_only_no_xp_spend():
    result = generate_character(42, {**vampire_opts(), "xp": "0"}, load_venue("custom_xp"))
    assert result.character["character_type"] == "vampire"
    assert result.xp_spent == 0
