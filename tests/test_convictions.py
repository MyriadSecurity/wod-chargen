"""Convictions picker tests."""

from __future__ import annotations

from wod_chargen.core.share import SharePayload, decode_query, encode_payload
from wod_chargen.games.lotn_v5.convictions import load_convictions_catalog, pick_convictions


def test_convictions_catalog_has_enough_entries():
    catalog = load_convictions_catalog()
    assert len(catalog["convictions"]) >= 100
    assert catalog["pick_count"] == 3


def test_pick_convictions_is_reproducible_and_unique():
    first = pick_convictions(424242)
    second = pick_convictions(424242)
    assert first == second
    assert len(first) == 3
    assert len({c["id"] for c in first}) == 3


def test_pick_convictions_varies_by_seed():
    a = pick_convictions(1)
    b = pick_convictions(2)
    assert a != b


def test_share_url_round_trips_convictions_seed():
    payload = SharePayload(seed=123, convictions_seed=456789, options={"type": "vampire"})
    decoded = decode_query(encode_payload(payload))
    assert decoded.convictions_seed == 456789
