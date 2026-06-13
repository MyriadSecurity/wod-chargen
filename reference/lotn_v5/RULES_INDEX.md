# Rules index — PDF, SRD, and JSON

## LoTN V5 pocket book (local only)

**Do not commit the PDF** to the public repository (Dark Pack / distribution policy).

```bash
cp "/path/to/laws_of_the_night_pocket.pdf" reference/lotn_v5/
```

## OWOD SRD (public web)

**Primary online reference:** [Laws of the Night SRD](https://www.oneworldofdarkness.com/laws-of-the-night/)

- URL map: `SRD_INDEX.md`
- Cursor setup: `CURSOR_DOCS.md`

## JSON ↔ rules mapping

| Rules source | SRD (preferred) | PDF (local) | Engine JSON |
|--------------|-----------------|-------------|-------------|
| Character creation | [dramatic-systems/character-creation](https://www.oneworldofdarkness.com/laws-of-the-night/dramatic-systems/character-creation) | Ch. 3 (pp. 51–81) | `creation.json`, `character_types.json` |
| XP costs / advancement | character-creation (XP section) | p. 79 | `costs.json` |
| Ghouls | [dramatic-systems/ghouls](https://www.oneworldofdarkness.com/laws-of-the-night/dramatic-systems/ghouls) | ghoul chapter | `ghoul_creation.json`, `ghoul_powers.json` |
| Thin-blood | [/thin-blood](https://www.oneworldofdarkness.com/laws-of-the-night/thin-blood) | thin-blood section | `thin_blood_creation.json`, `thin_blood_formulas.json`, `thin_blood_merits.json` |
| Clans | [/clans](https://www.oneworldofdarkness.com/laws-of-the-night/clans) | clan chapter | `clans.json` |
| Disciplines | [/disciplines](https://www.oneworldofdarkness.com/laws-of-the-night/disciplines) | disciplines chapter | `disciplines.json` |
| Backgrounds | [/backgrounds](https://www.oneworldofdarkness.com/laws-of-the-night/backgrounds) | backgrounds | `advantages.json` → `backgrounds` |
| Merits | [/merits-flaws](https://www.oneworldofdarkness.com/laws-of-the-night/merits-flaws) | merits | `advantages.json` → `merits` |
| Predator types | [/predator-types](https://www.oneworldofdarkness.com/laws-of-the-night/predator-types) | creation | `predator_types.json` |
| Loresheets | [/loresheets](https://www.oneworldofdarkness.com/laws-of-the-night/loresheets) | loresheets | (partial — generator stubs) |
| Attributes & skills | character-creation | Ch. 3 | `attributes.json`, `skills.json` |
| Archetype weights | — (house procedure) | — | `archetypes/*.json` |

When SRD and PDF differ, treat **SRD as canonical for MET LARP** unless implementing a deliberate house rule.
