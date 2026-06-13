"""Share URL round-trip and regeneration tests."""

from urllib.parse import urlparse

import pytest

from wod_chargen.core.data_loader import load_json_cached
from wod_chargen.core.share import (
    SharePayload,
    browser_share_url,
    decode_query,
    encode_payload,
    wizard_share_options,
)
from wod_chargen.games.lotn_v5.generator import generate_character


def _venue():
    return load_json_cached("wod_chargen.venues", "mes_end_to_dawn.json")


def test_share_round_trip():
    payload = SharePayload(
        seed=482910,
        game="lotn_v5",
        venue="mes_end_to_dawn",
        options={
            "type": "vampire",
            "clan": "brujah",
            "arch": "diplomat",
            "sub": "silver_tongue",
            "approval": "2026-06",
        },
    )
    qs = encode_payload(payload)
    decoded = decode_query(qs)
    assert decoded.seed == payload.seed
    assert decoded.game == payload.game
    assert decoded.venue == payload.venue
    assert decoded.options["clan"] == "brujah"


def test_unsupported_schema():
    with pytest.raises(ValueError, match="schema"):
        decode_query("?schema=9.9&seed=1")


def test_wizard_share_options_vampire():
    opts = wizard_share_options(
        character_type="vampire",
        arch="artist",
        sub="virtuoso",
        clan="toreador",
        approval="2026-06",
        venue_requires_approval_month=True,
    )
    assert opts == {
        "type": "vampire",
        "arch": "artist",
        "sub": "virtuoso",
        "clan": "toreador",
        "approval": "2026-06",
    }


def test_wizard_share_options_ghoul():
    opts = wizard_share_options(
        character_type="ghoul",
        arch="shadow",
        sub="spy",
        domitor_clan="tremere",
        approval="2026-06",
        venue_requires_approval_month=True,
    )
    assert "clan" not in opts
    assert opts["domitor_clan"] == "tremere"


def test_wizard_share_options_omits_approval_when_not_required():
    opts = wizard_share_options(
        character_type="vampire",
        arch="diplomat",
        sub="silver_tongue",
        clan="brujah",
        approval="2026-06",
        venue_requires_approval_month=False,
    )
    assert "approval" not in opts


def test_browser_share_url_includes_schema_and_seed():
    payload = SharePayload(
        seed=123,
        options=wizard_share_options(
            character_type="vampire",
            arch="diplomat",
            sub="silver_tongue",
            clan="brujah",
            approval="2026-06",
            venue_requires_approval_month=True,
        ),
    )
    url = browser_share_url("/", payload)
    assert url.startswith("/?")
    parsed = urlparse(url)
    decoded = decode_query(parsed.query)
    assert decoded.seed == 123
    assert decoded.options["arch"] == "diplomat"


def test_share_url_regenerates_same_character():
    seed = 918273
    options = wizard_share_options(
        character_type="vampire",
        arch="diplomat",
        sub="silver_tongue",
        clan="brujah",
        approval="2026-06",
        venue_requires_approval_month=True,
    )
    venue = _venue()
    original = generate_character(seed, options, venue)

    payload = SharePayload(seed=seed, options=options)
    share_url = browser_share_url("/chargen/", payload)
    decoded = decode_query(urlparse(share_url).query)

    restored = generate_character(decoded.seed, decoded.options, _venue())
    assert restored.character == original.character
    assert restored.xp_spent == original.xp_spent
