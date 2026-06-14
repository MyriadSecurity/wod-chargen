# Share URL schema 0.1 (pre-alpha)

## Required query parameters

| Param | Description |
|-------|-------------|
| `seed` | Integer RNG seed |
| `game` | Game pack id (`lotn_v5`) |
| `venue` | Venue profile id (`mes_end_to_dawn`, `fixed_100`) |

## Optional query parameters

| Param | Description |
|-------|-------------|
| `schema` | Share URL format version; omitted by default, decodes as `0.1` |

## lotn_v5 options

| Param | Description |
|-------|-------------|
| `type` | `vampire`, `ghoul`, `thin_blood` |
| `clan` | Vampire clan id |
| `domitor_clan` | Ghoul domitor clan id |
| `arch` | Primary archetype id |
| `sub` | Sub-archetype id |
| `approval` | MES approval month `YYYY-MM` |

## Example

```
?seed=482910&game=lotn_v5&venue=mes_end_to_dawn&type=vampire&clan=brujah&arch=diplomat&sub=silver_tongue&approval=2026-06
```

Older links that include `schema=0.1` still decode normally.

## Errors

Unknown `schema` values produce a user-visible error — never silent fallback to a different format.
