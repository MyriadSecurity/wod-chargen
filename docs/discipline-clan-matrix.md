# Discipline × clan matrix — Toreador batch

First review batch for unconventional archetype + clan combos on **Toreador** (in-clan: Auspex, Celerity, Presence).

Generated with:

```bash
uv run python scripts/discipline_power_coverage_report.py --matrix --clan toreador --arch <id>
```

Profiles use `adapt_profile_for_clan()` (expression alternates + in-clan floors). Matrix `flagged=1` means theme-only suppression with no explicit power picks and no expression alternate — runtime may still pick viable staples via the **0.75 in-clan power floor**.

| Archetype | Sub (default) | In-clan disc | Status | Notes |
|-----------|---------------|--------------|--------|-------|
| **enforcer** | tank | Celerity | Expression added | Alternate map boosts fleetness/rapid_reflexes/cat's grace; 11 boosted powers post-adapt |
| **enforcer** | tank | Presence | Expression added | dread_gaze/awe overrides; some suppressions remain on non-signature picks |
| **enforcer** | tank | Auspex | Viable | Neutral theme distribution; in-clan floor applies at pick time |
| **occultist** | thaumaturge | Auspex | Expression added | scry_the_soul/sense_the_unseen/premonition staples when BS off-clan |
| **occultist** | thaumaturge | Celerity | Known gap (soft) | Flagged in matrix; **0.75 power floor** keeps creation/XP picks usable |
| **occultist** | thaumaturge | Presence | Viable | Neutral; not core to occultist theme |
| **artist** | virtuoso | Presence | Viable | Strong native boosts (11); core Toreador fit |
| **artist** | virtuoso | Auspex | Viable | Strong boosts from occult/social tags |
| **artist** | virtuoso | Celerity | Known gap (soft) | Combat-tag suppression; floor-only mitigation — consider expression map if artist+brawler clans matter |
| **shadow** | spy | Auspex | Viable | Strong occult/spy alignment |
| **shadow** | spy | Celerity | Known gap (soft) | Floor-only; shadow is obfuscate/celerity elsewhere — Toreador lacks obfuscate |
| **shadow** | spy | Presence | Known gap (soft) | Social archetype on social disc but spy suppresses presence powers — floor-only |

## Follow-ups (later batches)

- Add `discipline_expressions` for **artist** / **shadow** if Toreador (or other non-combat clans) are common play choices.
- Expand matrix to 12 primaries × ~5 off-clan clans per `scripts/discipline_power_coverage_report.py --matrix`.
- Optional: `scripts/archetype_weight_report.py` seed sweep (30 seeds per cell) for avg in-clan discipline dots.

## Implementation reference

- `wod_chargen/games/lotn_v5/clan_discipline_adapt.py` — adaptation + floors + off-clan signature XP factor
- `data/archetype_themes.json` — `discipline_expressions` on **enforcer** and **occultist** primaries
