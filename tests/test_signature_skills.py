"""Signature skill reserve and XP push tests."""

from wod_chargen.core.data_loader import load_json_cached
from wod_chargen.core.models import LogEntry
from wod_chargen.core.rng import SeededRng
from wod_chargen.core.spender import PurchaseCandidate, spend_xp
from wod_chargen.core.xp_strategy import (
    efficiency_item_bias,
    signature_skill_efficiency_bias,
)
from wod_chargen.games.lotn_v5.archetypes import effective_profile
from wod_chargen.games.lotn_v5.backgrounds import empty_backgrounds
from wod_chargen.games.lotn_v5.base_creation import apply_base_creation
from wod_chargen.games.lotn_v5.generator import generate_character
from wod_chargen.games.lotn_v5.paths import DATA_PKG as DATA
from wod_chargen.games.lotn_v5.signature_skills import signature_skill_candidates
from tests.support.fixtures import load_venue, opts as vampire_opts

SKILLS = load_json_cached(DATA, "skills.json")["all"]


def _signatures(profile) -> list[str]:
    return signature_skill_candidates(profile, SKILLS)


def test_signature_skill_candidates_use_merged_bias():
    profile = effective_profile("diplomat", "silver_tongue", "vampire")
    candidates = _signatures(profile)
    assert candidates
    assert candidates[0] == "performance"
    assert all(
        profile.skill_biases.get(s) is not None or s in candidates for s in candidates[:1]
    )


def test_creation_reserves_one_signature_at_three_not_four():
    creation = load_json_cached(DATA, "creation.json")
    profile = effective_profile("diplomat", "silver_tongue", "vampire")
    signatures = set(_signatures(profile))
    caps = {"attribute": 5, "skill": 5, "discipline": 5, "background": 3}
    hits = 0
    for seed in range(40):
        char = {
            "character_type": "vampire",
            "clan": "brujah",
            "attributes": {},
            "skills": {},
            "disciplines": {},
            "backgrounds": empty_backgrounds(),
        }
        log: list[LogEntry] = []
        apply_base_creation(SeededRng(seed), char, profile, creation, log, caps)
        assert max(char["skills"].values(), default=0) <= 3
        reserved = [e for e in log if e.detail.get("signature_reserve")]
        assert len(reserved) == 1
        assert reserved[0].detail["rating"] == 3
        pick = reserved[0].message.split()[1]
        assert pick in signatures
        if char["skills"].get(pick, 0) == 3:
            hits += 1
    assert hits >= 36


def test_signature_skill_efficiency_boosts_three_to_five():
    assert signature_skill_efficiency_bias(2, 3) > efficiency_item_bias(2, 3)
    assert signature_skill_efficiency_bias(3, 4) > efficiency_item_bias(3, 4)
    assert signature_skill_efficiency_bias(4, 5) >= efficiency_item_bias(4, 5)


def test_xp_spends_push_signature_skills_toward_five():
    profile = effective_profile("enforcer", "tank", "vampire")
    sig = _signatures(profile)[0]
    char = {
        "attributes": {"strength": 2, "dexterity": 2, "stamina": 2},
        "skills": {sig: 3},
        "disciplines": {"potence": 2},
        "backgrounds": empty_backgrounds(),
        "character_type": "vampire",
        "clan": "brujah",
    }

    def enumerate_fn() -> list[PurchaseCandidate]:
        return [
            PurchaseCandidate(
                item_id=sig,
                category="skill",
                spend_group="skills",
                new_level=4,
                cost=12,
                weight=1.0,
                item_bias=2.0,
                clan_factor=1.0,
                source="test",
                apply=lambda: char["skills"].update({sig: 4}),
                is_signature=True,
            ),
        ]

    spend_xp(
        SeededRng(0),
        12,
        enumerate_fn,
        category_targets={
            "disciplines": 0.05,
            "attributes": 0.05,
            "skills": 0.8,
            "backgrounds": 0.05,
            "merits_flaws": 0.05,
        },
    )
    assert char["skills"][sig] == 4


def test_full_build_signature_reaches_four_or_five_with_xp():
    profile = effective_profile("diplomat", "silver_tongue", "vampire")
    signatures = set(_signatures(profile))
    hits = 0
    for seed in range(30):
        result = generate_character(seed, vampire_opts(), load_venue("mes_end_to_dawn"))
        if any(result.character["skills"].get(s, 0) >= 4 for s in signatures):
            hits += 1
    assert hits >= 20
