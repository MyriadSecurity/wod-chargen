# Discipline × clan matrix

Review notes for unconventional archetype + clan combos. Generated with:

```bash
uv run python scripts/discipline_power_coverage_report.py --matrix --clan <clan> [--arch <id>]
```

Profiles use `adapt_profile_for_clan()` (expression alternates + in-clan floors). `flagged=1` means theme-only suppression with no explicit picks — runtime still applies the 0.75 in-clan power floor.

## Implementation

- `wod_chargen/games/lotn_v5/clan_discipline_adapt.py` — adaptation + floors + off-clan signature XP factor
- `wod_chargen/games/lotn_v5/data/archetype_themes.json` — `discipline_expressions` on primaries

## Toreador batch (first review)

| Archetype | Sub | In-clan disc | Status |
|-----------|-----|--------------|--------|
| enforcer | tank | Celerity, Presence | Expression maps added |
| enforcer | tank | Auspex | Viable (in-clan floor) |
| occultist | thaumaturge | Auspex | Expression added |
| occultist | thaumaturge | Celerity, Presence | Soft gap (floor mitigates) |
| artist | virtuoso | Presence, Auspex | Viable |
| artist | virtuoso | Celerity | Soft gap |
| shadow | spy | Auspex | Viable |
| shadow | spy | Celerity, Presence | Soft gap |

Follow-ups: expression maps for artist/shadow on non-combat clans; expand matrix to remaining primaries × clans.
