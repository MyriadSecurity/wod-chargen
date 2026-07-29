# SPI Venue Structure

Design bible for **Society of Paranormal Investigators** as a second Venue.
Sheet generator for oneshots and NPCs — not MES chronicle intake.

**Status:** Venue package + generator + wizard + Build guide / Weight Map shipped.
**Sources:** MES SPI docs + official character sheet under `reference/spi/` (gitignored).

### Maintainer quick links

| Need | Go to |
|------|--------|
| Which file to edit | [`where-to-edit.md`](where-to-edit.md) |
| Bias ranges / SPI workflow | [`archetype-weight-guidelines.md`](archetype-weight-guidelines.md) |
| Data folder map | [`wod_chargen/games/spi/data/README.md`](../wod_chargen/games/spi/data/README.md) |
| Contribute / validate commands | [`CONTRIBUTING.md`](../CONTRIBUTING.md) |

---

## 1. Product scope

### In

- Procedural **sheets**: Attributes, Skills, specialties, Affinity, Division, Faction, Archetype-driven spends, Merits (general + Affinity), Virtue/Vice, derived advantages, XP spend log.
- Flat CoD-style XP via **starting XP profiles**: MES datetime preset, fixed **35**, **custom**.

### Out

- Approvals workflow, VIP, CCD, Dark Places, MC-as-required path
- Touchstones, Aspirations (on generated sheets)
- Conditions / live character tracking
- Status as a picker (see §2.1)
- Full Affinity power prose (ids, costs, prereqs, tags for weighting only)
- VSS authoring, Ikons catalog, Research Tree, Sworn Knights, item crafting

---

## 2. Locked product decisions

| Topic | Decision |
|-------|----------|
| XP profiles | MES datetime floor (see §2.4), fixed **35**, **custom** |
| Wizard order | `xp_profile → division → faction → archetype → sub_archetype → affinity → generate` |
| Division | Explicit pick (except full random) |
| Faction | Wizard step + bias; seed list in §2.5 |
| Archetypes | Pared starter set (§2.6); Affinity usually from biases; staff can add packs later |
| Affinity step | Always shown; default **Any (from archetype)**; optional lock to one Affinity |
| Multi-Affinity | Generator **toggle** (off = stay on one Affinity track; on = allow secondary via XP/bundle) |
| Merit blurbs | Ship **flavor** blurbs on sheet via `merit_descriptions.json` (no Codex mechanics) |
| Virtue / Vice | Include on sheet |
| Touchstones / Aspirations | Omit |
| Conditions | Ignore (no live tracking) |
| Status | No picker; always emit **Division Status 1** (see §2.1) |
| Prereqs | **Bundle** missing prereqs into purchase cost (see §2.2) |

### 2.1 Division Status

Rules allow starting at Division Status **1 or 2**. For oneshot/NPC sheets we always record **Status 1** (the default floor). STs can bump in play. Local Status omitted.

### 2.2 Prerequisite bundling

When a desired trait’s prereqs are unmet, the generator may still select it: candidate **cost** = XP for the trait **plus** XP to buy missing prereq dots (attributes, skills, merits, Affinity), recursively. Efficiency weighting scores the whole bundle against remaining budget.

**Parsing approach (prep):**

1. Prefer structured fields extracted from the sheet tables (dot ranges, Affinity type, category).
2. Parse clean prereq strings where regular (`Resolve 3`, `Fae Affinity 1`, `Brawl 2`).
3. Fighting-style / messy chains: soft-skip or human-tagged until parsers are solid — do not block scaffolding.

### 2.3 Wizard steps (detail)

```text
xp_profile → division → faction → archetype → sub_archetype → affinity → generate
```

- Full random: may roll Division / Faction / Archetype; Affinity stays **Any** unless locked.
- Affinity picker options: **Any (from archetype)** (default) | Ghost | Spirit | Mage | Fae | Vampire.
- Multi-Affinity toggle lives on the generate / options strip (with XP), not as its own wizard step.

### 2.4 MES Game XP floor

From SPI Character Creation Guide (`reference/spi/character_creation.txt`):

- Chronicle start **2026-01-01**: Game XP floor = **35**
- At the start of each subsequent calendar month: **+3** Game XP

Formula: `floor = 35 + 3 * months_since_2026_01` (inclusive of chron start month as 0).

Example: 2026-07 → `35 + 3*6 = 53`. MC / Event / Bonus XP are out of scope for oneshots (MES datetime profile = Game XP floor only).

### 2.5 Factions (from Division Guide)

Starter list for `factions.json` (bias hooks TBD at scaffold):

| id | label | Bias sketch |
|----|-------|-------------|
| `higher_ground` | The Higher Ground | Secrecy, status quo, Social / Subterfuge soft bias |
| `humanity_first` | Humanity First | Hunter lean: Firearms/Brawl, Defense-adjacent, anti-supernatural |
| `order_of_the_everlight` | The Order of the Everlight | Integrity/Resolve, Affinity control themes, Melee/Weaponry |
| `diplomats` | The Diplomats | Social Maneuvering, Empathy/Persuasion, alliance lean |
| `veritas` | Veritas | Investigation/Academics/Occult, information sharing |

Faction membership is optional in play; generator always picks one for sheet flavor + bias (full random included).

### 2.6 Starter archetypes (extensible)

Primaries plus **subtypes** (LotN-style additive deltas). Layout:

`archetypes/{id}.json` (absolute baselines) and `archetypes/{id}/{sub}.json`
(`modifiers` deltas). Register in `_manifest.json` `subtypes` map.

| id | label | Role sketch | Default Affinity lean | Starter subtypes |
|----|-------|-------------|------------------------|------------------|
| `investigator` | Investigator | Clues, interviews, forensics | Mage / Ghost | detective, forensic, interviewer |
| `occultist` | Occultist | Rituals, lore, Affinity powers | any (strong Affinity spend) | ritualist, exorcist, medium |
| `scholar` | Scholar | Research, Academics/Science, R&D | Mage / Spirit | scientist, archivist, theorist |
| `guardian` | Guardian | Protect people; Defense lean | Vampire / Spirit | bodyguard, tactical, warden |
| `field_agent` | Field Agent | Adventure, athletics, travel | Spirit / Fae | scout, courier, pathfinder |
| `shadow` | Shadow | Spy / infiltrate | Ghost / Fae | infiltrator, watcher, fixer |
| `diplomat` | Diplomat | Talk first; Social | Fae / Mage | negotiator, liaison, handler |
| `caregiver` | Caregiver | Medicine, Integrity support, H&W | Ghost / Spirit | medic, counselor, chaplain |

Bias packs: soft Affinity / attribute / skill / merit maps plus merit **theme**
`tag_affinities` (LotN-style resolver). Subtypes sharpen via additive deltas
(+0.2–0.5 typical). Staff handoff = drop new JSON under `data/archetypes/` and
register in manifest.

---

## 3. Terminology

| Term | Meaning | Examples |
|------|---------|----------|
| **Venue** | Game line | LotN V5, SPI, Werewolf Apocalypse |
| **VSS** | Local Venue Style Sheet | Deferred |
| **Starting XP profile** | XP budget source | MES datetime, fixed 35, custom |

**Repo naming debt:** catalog/registry say `game`; `wod_chargen/venues/` holds **starting XP profiles** (not Venues); wizard state key `venue` means XP profile. Prefer `get_xp_profile_picker()` in new call sites (aliases `get_venue_picker()`). Product/UI copy uses **Venue** for the game line. On-disk `venues/` rename is deferred.

**SPI bias model:** multiplicative maps on archetype / Division / Faction
(`attribute_biases`, `skill_biases`, `affinity_biases`, `merit_biases`,
`tag_affinities`). Catalog `merits.json` extract tags remain metadata.
Judgment **theme** tags live in `data/trait_tags.json` and feed
`wod_chargen.games.spi.trait_biases.resolve_merit_bias` (explicit id wins over
tag product; clamp 0.05–3.0). See [archetype-weight-guidelines.md](archetype-weight-guidelines.md)
(SPI merit subsection).

`VenueSystem` protocol: [`wod_chargen/games/protocol.py`](../wod_chargen/games/protocol.py). UI adapters fail closed via [`app/venue_dispatch.py`](../app/venue_dispatch.py).

```mermaid
flowchart LR
  landing[Landing pick Venue]
  catalog[catalog.json]
  registry[registry]
  system[VenueSystem contract]
  spiPkg[games/spi]
  lotnPkg[games/lotn_v5]
  xpProfiles[starting XP profiles]
  sheet[Sheet output]

  landing --> catalog
  catalog --> registry
  registry --> system
  system --> spiPkg
  system --> lotnPkg
  spiPkg --> xpProfiles
  lotnPkg --> xpProfiles
  spiPkg --> sheet
  lotnPkg --> sheet
```

---

## 4. Venue package tree

Shipped under `wod_chargen/games/spi/` (see also `data/README.md`):

```
wod_chargen/games/spi/
  __init__.py
  paths.py
  system.py
  generator.py                  # later
  sheet_model.py                # later
  data/
    wizard_ui.json
    character_types.json        # investigator
    creation.json
    costs.json
    attributes.json             # CoD: Presence not Charisma
    skills.json                 # CoD: Weaponry not Melee
    affinity_types.json
    affinity_levels.json        # L1–5 benefit keys (labels)
    divisions.json
    factions.json               # with bias hooks
    archetypes/                 # bias packs (Affinity downstream)
    merits.json                 # general + affinity; ids/costs/prereqs/tags
    advantages.json
```

**XP profiles** (later): `venues/picker.json` → `"spi": ["mes_spi", "fixed_35", "custom_xp"]` (names TBD).  
**Catalog:** `"spi"` with `implemented: false` until a UI spike.

**Extract source:** `reference/spi/character_sheet.xlsx` tabs `merit-table` / `affinity-table` (catalog only; no prose).

---

## 5. Sheet shapes

### 5.1 Official SPI sheet (source of truth)

From MES `character_sheet.xlsx` printable layout:

- **Header:** Name, Concept, Virtue, Vice, Faction, Division  
- **Attributes** (columns Mental | Physical | Social):
  - Mental: Intelligence, Wits, Resolve  
  - Physical: Strength, Dexterity, Stamina  
  - Social: **Presence**, Manipulation, Composure  
- **Skills** (CoD 2e; Mental −3 / Phys+Soc −1 unskilled):
  - Mental: Academics, Computer, Crafts, Investigation, Medicine, Occult, Politics, Science  
  - Physical: Athletics, Brawl, Drive, Firearms, Larceny, Stealth, Survival, **Weaponry**  
  - Social: Animal Ken, Empathy, Expression, Intimidation, Persuasion, Socialize, Streetwise, Subterfuge  
- **Other traits:** General Merits, Affinity Merits, Affinities (5 tracks), Health, Willpower, Integrity  
- **Derived:** Speed, Initiative, Perception, Defense, Clash of Wills (+ Downtime Actions / Max Integrity on working tabs)

**Not on sheet / not in our generator:** classic Flaws track (CoD 2e uses Conditions instead — we ignore Conditions). Touchstones exist in SPI rules (HtV-derived) but we **omit** them on generated sheets.

### 5.2 Shared envelope

`GenerationResult` stays shared (`game_id` = Venue id; `venue_id` = XP profile id — naming debt).

### 5.3 `SpiSheetModel` (target)

```text
SpiSheetModel {
  header: SheetHeader       # Division, Faction, Archetype, Affinity summary, Virtue, Vice, concept?
  attributes: TraitPanel    # Mental / Physical / Social (Presence)
  skills: TraitPanel        # CoD skills (Weaponry)
  specialties: string[]
  affinities: RatedTraitsSection
  merits_general: RatedTraitsSection
  merits_affinity: RatedTraitsSection   # or by AffinityType
  advantages: MetaItem[]    # Health, Speed, Willpower, Initiative, Perception,
                            # Defense, Clash of Wills, Downtimes, Integrity, Max Integrity
}
```

### 5.4 Character dict sketch

```text
character {
  type: "investigator",
  concept?: string,
  virtue, vice,
  attributes: { intelligence, wits, resolve, strength, dexterity, stamina,
                presence, manipulation, composure },
  skills: { academics, computer, crafts, … weaponry, … },
  specialties: string[],
  affinities: { ghost, spirit, mage, fae, vampire },  # 0..5; sum ≥ 1
  division, faction,
  division_status: 1,          # always for generator output
  archetype,
  sub_archetype,
  options: { multi_affinity: bool, affinity_lock: "any"|AffinityType },
  merits: { "<id>": dots },
  integrity, size: 5,
  advantages: { health, speed, willpower, initiative, perception,
                defense, clash_of_wills, downtimes, max_integrity }
}
```

Hard rules:

- Free Affinity 1 at creation; Affinity merit dots per type ≤ `3 × AffinityRating[type]`
- If `multi_affinity` is **false**, all Affinity dots/powers stay on a single type
- If **true**, secondary Affinity allowed via XP / prereq bundles (Integrity still uses top two)
- `max_integrity = 11 − sum(top two Affinities)`; start `min(7, max_integrity)`
- No Greater/Lesser templates
- Prereq bundling when buying gated traits
- Flavor merit blurbs on sheet (`merit_descriptions.json`); no Codex mechanics dump

---

## 6. JSON field sketches

### 6.1 `affinity_types.json`

Five types: `ghost`, `spirit`, `mage`, `fae`, `vampire` — each with `fuel`, `place_merit`, `unseen_sense`, `sense_mode` (see Affinity Guide). Used for sheet labels and bias hooks, not Ikon simulation.

### 6.2 `affinity_levels.json`

L1–5 **keys** only (unlock powers, Unseen Sense, sense mode, fuel, place detect, bans, downtime penalty). Prose deferred.

### 6.3 `divisions.json` / `factions.json`

Division: Acquisitions, Adventure, Defense, Health and Welfare, R&D + bias refs.  
Faction: five starter factions in §2.5 + bias refs.

### 6.4 `creation.json`

```json
{
  "attributes": { "base_dots": 1, "primary": 5, "secondary": 4, "tertiary": 3 },
  "skills": { "primary": 11, "secondary": 7, "tertiary": 4 },
  "specialties": 3,
  "free_affinity_dots": 1,
  "merit_dots": 7,
  "max_affinity_merit_dots_at_creation": 3,
  "integrity_default": 7,
  "size_default": 5,
  "affinity_merit_dots_per_affinity_level": 3,
  "division_status_default": 1
}
```

### 6.5 `costs.json` (flat per dot)

Affinity 5 · Attribute 4 · Skill 2 · Integrity 2 · Supernatural Resistance **2** · Specialty 1 · Merit 1 · Willpower-dot regain 1.

**Flat vs graduated:** MES SPI is CoD 2e flat rate (same XP per new dot). Merits default to **1 XP/dot**; fixed-rating catalog entries (`dots_min == dots_max`) are bought as one package but still cost N×1 XP. **Extra Touchstone** is the sole graduated exception (level N costs N XP; 15 XP for •••••) — omitted from oneshot generation with Touchstones.

### 6.6 `merits.json`

Extract from sheet `merit-table` + `affinity-table`, then **filtered to Rules Addendum–sanctioned material** via `sanctioned_merit_ids.json` (rebuild: `scripts/build_spi_sanctioned_merit_ids.py`, then `scripts/seed_spi_data_from_extract.py`).

- **Affinity:** all sheet affinity-tab rows (MES Affinity Powers catalog).
- **General:** only Addendum-allowlisted names (plus typo aliases). Dropped from the sheet include unsanctioned Fighting Styles, Mystery Cult Initiation, Artifacts, and CoD supernatural rows that are Affinity-only or not listed as General.
- Same `id` may exist as Affinity after its General twin was dropped (e.g. `medium`, `telekinesis`).

```json
{
  "id": "psychometry",
  "label": "Psychometry",
  "category": "affinity",
  "affinity_type": "ghost",
  "dots_min": 3,
  "dots_max": 3,
  "prereq_text": "",
  "prereqs": [],
  "tags": ["affinity_power"]
}
```

- `category: general | affinity`  
- Affinity merits count against `3 × Affinity` pool  
- General merits with Affinity floors do **not** burn that pool  
- No Flaws catalog

### 6.7 `advantages.json`

Same formulas as SPI sheet / chargen guide (Health, Speed, Willpower, Initiative, Perception, Defense, Clash = max resistant attr + Occult, Downtimes = Resolve+1, Max Integrity).

### 6.8 `attributes.json` / `skills.json`

Explicit CoD lists (§5.1). Do **not** reuse LotN `charisma` / `melee`.

### 6.9 `wizard_ui.json`

```json
{
  "wizard_steps": ["xp_profile", "division", "faction", "archetype", "sub_archetype", "affinity", "generate"],
  "affinity_default": "any",
  "copy": {
    "landing_blurb": "Build a Society investigator sheet for oneshots or NPCs.",
    "division_title": "Division",
    "faction_title": "Faction",
    "archetype_title": "Archetype",
    "affinity_title": "Affinity",
    "affinity_any_label": "Any (from archetype)",
    "multi_affinity_label": "Allow multiple Affinities",
    "xp_title": "Starting XP"
  }
}
```

---

## 7. VenueSystem contract

| Method / property | Role |
|-------------------|------|
| `id`, `label`, `tagline` | Venue identity |
| `get_wizard_steps()` / `get_wizard_copy()` | UI |
| Pickers | Division, Faction, Archetypes, Affinity (default Any); multi-affinity toggle on generate |
| `get_xp_profile_picker()` | Today: `get_venue_picker()` |
| `generate(...)` → `GenerationResult` | Engine |
| `build_sheet_model(...)` | Sheet VM |

Landing: pick **Venue** first, then that Venue’s wizard.

---

## 8. Pre-build coupling checklist

| Area | Issue |
|------|--------|
| [`registry.py`](../wod_chargen/games/registry.py) | `VenueSystem` protocol; LotN + SPI registered |
| [`app/venue_dispatch.py`](../app/venue_dispatch.py) | Fail-closed guide/weight adapters |
| [`app/wizard.py`](../app/wizard.py), sheet, views | Venue-branched via dispatch + `is_spi_game` |
| [`app/strategy_page.py`](../app/strategy_page.py) / weight map | Venue-scoped via `?game=`; unknown fails closed |
| [`core/share.py`](../wod_chargen/core/share.py) | LotN option keys; SPI options built in wizard_state |
| [`core/xp_log_format.py`](../wod_chargen/core/xp_log_format.py) | LotN discipline labels |
| [`venues/picker.json`](../wod_chargen/venues/picker.json) | No `spi` XP profiles yet |
| Naming | `game` vs Venue; `venue` vs XP profile |

---

## 9. Defer list

Approvals, VIP, CCD, Touchstones/Aspirations UI, Conditions, Status politics, Ikons, Research Tree, power prose, Sworn Knights, item crafting, VSS, MC membership progression, mass `games`/`venues` rename.

---

## 10. Next phases

1. ~~Extract catalogs~~ (done: `scripts/extract_spi_sheet_catalogs.py`)  
2. ~~Scaffold `games/spi/` + catalog stub + XP profiles~~ (done: seed via `scripts/seed_spi_data_from_extract.py`)  
3. ~~Seed factions §2.5 + starter archetypes §2.6~~  
4. ~~Generator MVP + SpiSheetModel~~  
5. ~~Wizard + Venue-scoped Build guide / Weight Map~~  

---

## 11. Success criteria

- [x] Sheet-only oneshot/NPC framing  
- [x] Venue vs XP profile terminology  
- [x] Official SPI/CoD sheet shape (Presence, Weaponry, no Flaws)  
- [x] Locked wizard order and product decisions  
- [x] Factions, starter archetypes, XP floor formula, multi-affinity toggle  
- [x] Prereq bundling + parsing approach  
- [x] JSON sketches + coupling checklist  
