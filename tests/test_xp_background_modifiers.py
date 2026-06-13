"""XP spending on background advantages and disadvantages."""

from __future__ import annotations

from collections import Counter

from wod_chargen.games.lotn_v5.generator import generate_character

from tests.test_generator import _opts, _venue


def test_xp_buys_background_modifiers_over_many_seeds():
    mod_purchases = 0
    dis_purchases = 0
    for seed in range(80):
        result = generate_character(seed, _opts(predator="alleycat"), _venue())
        for xp in result.xp_log:
            if xp.category == "background_modifier":
                mod_purchases += 1
            if xp.category == "background_disadvantage":
                dis_purchases += 1
    assert mod_purchases > 20, f"expected modifier XP buys, got {mod_purchases}"
    assert dis_purchases > 0, f"expected some disadvantage XP buys, got {dis_purchases}"


def test_xp_disadvantage_trade_grants_free_advantages():
    traded = 0
    for seed in range(40):
        result = generate_character(seed, _opts(predator="siren"), _venue())
        meta = result.character.get("background_meta", {})
        traded += int(meta.get("xp_adv_from_disadv_trade", 0))
    assert traded > 0


def test_xp_modifiers_only_on_xp_purchased_backgrounds():
    for seed in range(60):
        result = generate_character(seed, _opts(predator="alleycat"), _venue())
        xp_bg_keys = {
            xp.item.split("/", 1)[0] + "/" + xp.item.split("/", 2)[1]
            if xp.category == "background"
            else None
            for xp in result.xp_log
        }
        xp_bg_keys.discard(None)
        xp_purchased_names = {
            f"{e['type']}/{e.get('name', e['type'])}"
            for e in result.character["backgrounds"]
            if e.get("xp_purchased")
        }
        for xp in result.xp_log:
            if xp.category not in ("background_modifier", "background_disadvantage"):
                continue
            parts = xp.item.split("/")
            entry_key = f"{parts[0]}/{parts[1]}"
            assert entry_key in xp_purchased_names, (
                f"seed {seed}: modifier {xp.item} on non-XP background"
            )


def test_predator_backgrounds_get_xp_upgrades():
    upgrades = Counter()
    for seed in range(50):
        result = generate_character(seed, _opts(predator="bagger"), _venue())
        pred_types = {
            e["type"]
            for e in result.character["backgrounds"]
            if e.get("from_predator")
        }
        for xp in result.xp_log:
            if xp.category != "background":
                continue
            bg_type = xp.item.split("/", 1)[0]
            if bg_type in pred_types:
                upgrades[bg_type] += 1
    assert upgrades.get("contacts", 0) > 0
