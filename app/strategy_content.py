"""Player-facing copy for the character building guide."""

from __future__ import annotations

from typing import Any

STRATEGY_TABS: tuple[tuple[str, str], ...] = (
    ("overview", "Overview"),
    ("creation", "Creation"),
    ("xp", "Experience"),
    ("reference", "Quick reference"),
)

STRATEGY_PAGE_TITLE = "How Characters Are Built"

STRATEGY_BLURB = (
    "Pick archetype, clan, and predator type; the tool fills in a sheet that matches "
    "that concept. Hard rules run first — generation caps, prerequisites, costs. "
    "When several choices are legal, weights pick among them. "
    "Formulas under each section spell out the numbers. "
    "See the Weight Map for per-trait bias."
)


def strategy_sections() -> dict[str, list[dict[str, Any]]]:
    """Return section blocks keyed by tab id."""
    return {
        "overview": _overview_sections(),
        "creation": _creation_sections(),
        "xp": _xp_sections(),
        "reference": _reference_sections(),
    }


def _overview_sections() -> list[dict[str, Any]]:
    return [
        {
            "title": "Overview",
            "paragraphs": [
                "Build order matches LoTN: concept, free creation dots, optional Step 8, "
                "then XP. Nothing violates book limits; illegal options never enter the pool.",
                "Archetype and subtype set the baseline. Clan and predator adjust it before "
                "dots are assigned.",
            ],
        },
        {
            "title": "Build order",
            "steps": [
                "Archetype + subtype",
                "Clan (in-clan disciplines, alternates for off-clan signatures)",
                "Predator type",
                "Creation: attributes, skills, in-clan disciplines, backgrounds",
                "Predator package (specialties, extra dots, etc.)",
                "Step 8: flaws for merit credit (optional)",
                "Thin-blood merit/flaw pairs (thin blood only)",
                "XP: venue pool, then remaining buys",
                "Loresheet benefits (free; requires purchased loresheet dots)",
            ],
        },
        {
            "title": "Bias layers",
            "paragraphs": [
                "Preferences stack. Each layer modifies the last; none bypass rules.",
                "Each trait has a bias — a preference multiplier. Above 1.0 = on-theme; "
                "below 1.0 = off-theme. Clamped to 0.05–3.0 (never zero, rarely picked).",
            ],
            "formulas": [
                {
                    "caption": "Trait bias",
                    "body": (
                        "bias = explicit override on merged profile\n"
                        "    OR product of tag affinities for that trait\n"
                        "    OR 1.0 (neutral)\n"
                        "final bias = clamp(bias, 0.05 … 3.0)"
                    ),
                },
                {
                    "caption": "Merged profile",
                    "body": (
                        "merged profile = archetype + subtype deltas\n"
                        "              → clan adaptation (discipline floors, alternates)\n"
                        "              → predator multipliers (attributes, skills, disciplines)"
                    ),
                },
            ],
            "table": {
                "headers": ["Layer", "Source", "Effect"],
                "rows": [
                    [
                        "Archetype",
                        "Diplomat, Enforcer, …",
                        "Default bias on attributes, skills, disciplines, backgrounds, merits",
                    ],
                    [
                        "Subtype",
                        "Silver Tongue, Brawler, …",
                        "Adjusts the parent (additive deltas)",
                    ],
                    [
                        "Clan",
                        "Lineage or domitor clan (ghoul)",
                        "In-clan discipline bias ≥ 0.85; alternates if signature disciplines aren't in-clan",
                    ],
                    [
                        "Predator",
                        "Alleycat, Sandman, …",
                        "Multiplies pool and package biases",
                    ],
                ],
            },
        },
        {
            "title": "Weight Map",
            "paragraphs": [
                "Shows merged biases for your archetype, predator, and clan. "
                "Green = boosted; red = suppressed.",
            ],
            "link": {"label": "Open Weight Map", "page": "weights"},
        },
    ]


def _creation_sections() -> list[dict[str, Any]]:
    return [
        {
            "title": "Attributes and disciplines",
            "paragraphs": [
                "One free pool assignment per attribute; no stacking +4 and +1 on "
                "the same trait from creation.",
                "Larger pool chunks go first (+4 before +1). On-theme attributes weigh "
                "higher; +4 chunks get ×2.0 so a •••• creation dot often pairs with a "
                "cheap fifth dot at XP.",
            ],
            "formulas": [
                {
                    "caption": "Creation pool pick (attributes)",
                    "body": (
                        "pick weight = trait bias × room to grow\n"
                        "room = max rating − current rating\n"
                        "\n"
                        "pool chunk multiplier:\n"
                        "  +4 dots → ×2.0\n"
                        "  +3 dots → ×1.3\n"
                        "  +1 or +2 → ×1.15"
                    ),
                },
            ],
            "bullets": [
                "Free discipline dots land on unused in-clan disciplines; powers assign with each dot.",
                "Power bias = archetype theme × general utility rating.",
                "Off-clan signature disciplines: legal at XP, ×0.6 pick weight vs in-clan.",
            ],
        },
        {
            "title": "Skills and signature reserve",
            "paragraphs": [
                "Skills use the book **Balanced** spread: 0×@4, 3×@3, 5×@2, 7×@1 "
                "(15 skills with dots). No skill gets a free +4 at creation.",
                "Before the rest of the skill pool is assigned, **one @3 slot is reserved** "
                "for a **signature skill** — a weighted pick among the top on-theme skills "
                "for your merged profile (archetype + subtype + clan + predator).",
            ],
            "formulas": [
                {
                    "caption": "Signature skill set",
                    "body": (
                        "merged bias = resolve_trait_bias(skill)\n"
                        "  explicit skill_biases OR tag-affinity product\n"
                        "\n"
                        "signature candidates = top 3 skills with bias ≥ 1.35\n"
                        "  (threshold in creation.json; else top 3 overall)\n"
                        "\n"
                        "@3 reserve = weighted pick among unused signature candidates\n"
                        "remaining skill pool = same merged bias, normal assignment"
                    ),
                },
            ],
            "bullets": [
                "Creation log marks the reserve: Skill … +3 → 3 (signature reserve).",
                "Other skills still spread broadly; single-stat skill maxing at creation is unlikely.",
                "Signature •4–•5 usually come from XP, not creation.",
            ],
        },
        {
            "title": "Backgrounds",
            "paragraphs": [
                "Creation background dots usually become Contacts, Allies, Resources, and similar.",
                "Which type gets the next dot: catalog default × archetype × predator.",
            ],
            "formulas": [
                {
                    "caption": "Background type (creation)",
                    "body": (
                        "weight = catalog creation_bias[type]\n"
                        "       × archetype background bias\n"
                        "       × predator background bias (if any)"
                    ),
                },
                {
                    "caption": "Modifier vs connection",
                    "body": (
                        "modifier chance: ~12% early, up to ~35% as connections grow\n"
                        "free disadvantages: ~70% chance, 1–3 picks\n"
                        "disadvantage → advantage: 1 for 1"
                    ),
                },
            ],
            "bullets": [
                "Most dots raise connection ratings.",
                "Some become modifier advantages (spheres, reliability, etc.).",
                "Predator type can weight Haven, Street, and other types.",
            ],
        },
        {
            "title": "Merits and flaws (Step 8)",
            "paragraphs": [
                "Step 8 is optional. If used: take flaws, spend up to ten free merit dots from the credit.",
            ],
            "formulas": [
                {
                    "caption": "Step 8 pick",
                    "body": (
                        "merit weight = merit group weight × merit bias\n"
                        "flaw weight = same group weight (coarse)"
                    ),
                },
            ],
            "bullets": [
                "Many sheets skip Step 8 entirely.",
                "Thin bloods use a separate merit/flaw pairing step.",
            ],
        },
    ]


def _xp_sections() -> list[dict[str, Any]]:
    return [
        {
            "title": "Starting XP",
            "paragraphs": [
                "Set by venue:",
            ],
            "table": {
                "headers": ["Venue", "XP source"],
                "rows": [
                    ["MES approval month", "Chart lookup for approval date"],
                    ["Fixed", "Same total for everyone (e.g. 100)"],
                    ["Custom", "You enter the amount"],
                ],
            },
        },
        {
            "title": "Blood Potency first",
            "paragraphs": [
                "XP buys mandatory Blood Potency for generation before anything else — "
                "required by rules, not concept. If the pool falls short, the shortfall is logged; "
                "leftover XP continues.",
            ],
        },
        {
            "title": "Choosing XP spends",
            "paragraphs": [
                "One legal purchase per loop (one dot, one merit step, one background dot, etc.) "
                "until XP runs out or nothing is affordable.",
                "Three passes: pick area (disciplines, attributes, …), pick group within it, "
                "pick trait. A random factor on the last pass adds variation between seeds.",
            ],
            "formulas": [
                {
                    "caption": "Three-pass pick",
                    "body": (
                        "1. Macro area (disciplines, attributes, skills, backgrounds, merits/loresheets)\n"
                        "   macro weight = target share × avg group weight × deficit boost\n"
                        "\n"
                        "2. Spend group (Physical attrs, in-clan disciplines, …)\n"
                        "   group weight = archetype weight for that group\n"
                        "\n"
                        "3. Trait\n"
                        "   score = trait bias × clan factor × efficiency × random(0…1)\n"
                        "   highest score wins"
                    ),
                },
                {
                    "caption": "Deficit boost",
                    "body": (
                        "expected spend in area = target share × XP spent so far\n"
                        "deficit = (expected − actual) / total XP budget\n"
                        "boost = clamp(1 + 4.5 × deficit, 0.25 … 4.0)"
                    ),
                },
            ],
        },
        {
            "title": "XP mix",
            "paragraphs": [
                "Target shares jitter ±18% per character, then normalize. "
                "Average spend skews supernatural but still buys attrs, skills, and contacts:",
            ],
            "formulas": [
                {
                    "caption": "Base targets (before jitter)",
                    "body": (
                        "disciplines  … 34%\n"
                        "attributes   … 20%\n"
                        "skills       … 20%\n"
                        "backgrounds  … 12%\n"
                        "merits, loresheets, extra Blood Potency … 14%"
                    ),
                },
            ],
            "table": {
                "headers": ["Area", "Rough share"],
                "rows": [
                    ["Disciplines (+ rituals, ceremonies, ghoul powers, alchemy)", "~⅓"],
                    ["Attributes", "~⅕"],
                    ["Skills", "~⅕"],
                    ["Backgrounds", "~⅛+"],
                    ["Merits, loresheets, BP above minimum", "rest"],
                ],
            },
        },
        {
            "title": "Dot-buy habits",
            "paragraphs": [
                "Efficiency multipliers favor cheap, typical buys (finish •••••, open skills at • or ••). "
                "Areas already over their target share get dampened so XP doesn't pile into one bucket.",
                "**Signature skills** (same top-3 on-theme set as creation) get higher efficiency "
                "when pushing to •3–•5, since creation rarely grants •4 skills.",
            ],
            "formulas": [
                {
                    "caption": "Efficiency multipliers",
                    "body": (
                        "•••• → •••••     ×5.0\n"
                        "none → •         ×2.5\n"
                        "none → ••        ×1.6\n"
                        "• → ••           ×1.4\n"
                        "•• → •••         ×0.35  (signature floor ×2.5)\n"
                        "••• → ••••       ×1.1   (signature floor ×3.5)\n"
                        "none → •••       ×0.1\n"
                        "\n"
                        "Loresheets:\n"
                        "  0→1 ×3.2, 1→2 ×3.6, 2→3 ×2.8"
                    ),
                },
                {
                    "caption": "Over/under target share",
                    "body": (
                        "if area spend > 110% of target:\n"
                        "  efficiency × max(0.15, 1 − (overshoot × 5))\n"
                        "if area spend < 90% of target:\n"
                        "  efficiency × min(2.0, 1 + (undershoot × 3))"
                    ),
                },
            ],
            "bullets": [
                "Skill item bias uses merged resolve_trait_bias (explicit + tags), not explicit keys alone.",
                "In-clan disciplines: normal XP cost and weight. Off-clan signatures: ×0.6 weight.",
                "Blood Potency above generation minimum: group weight 0.4 (uncommon).",
                "Loresheet benefits apply after dots are paid — the benefit itself costs no XP.",
            ],
        },
        {
            "title": "Typical sheet",
            "bullets": [
                "At least one signature skill at •3 from creation; often •4–•5 after XP.",
                "Attrs and other skills aligned with archetype and predator.",
                "Disciplines that fit clan costs and concept.",
                "Background entries with modifiers on key contacts.",
                "Some merits; often a loresheet at 2–3 dots.",
                "Rituals or ceremonies if Thaumaturgy or Oblivion is present.",
            ],
        },
    ]


def _reference_sections() -> list[dict[str, Any]]:
    return [
        {
            "title": "Same seed, same sheet",
            "paragraphs": [
                "Same seed and same wizard inputs (venue, type, clan, archetype, subtype, "
                "predator, approval month, …) → same output. Change any input — or the "
                "generator version — and the result shifts.",
            ],
            "formulas": [
                {
                    "caption": "Determinism",
                    "body": "seed + wizard options + generator version → sheet",
                },
            ],
        },
        {
            "title": "Rules vs weights",
            "table": {
                "headers": ["Fixed by rules", "Weighted by concept"],
                "rows": [
                    ["Generation and Blood Potency caps", "Which attrs and skills rise"],
                    ["Power and merit prerequisites", "Which disciplines and powers"],
                    ["Dot caps per category", "Backgrounds and spheres"],
                    ["Book skill spread (Balanced; no @4 skill)", "Signature @3 reserve + XP pushes"],
                    ["In-clan vs out-of-clan XP cost", "Merits, flaws, loresheets"],
                    ["Thin-blood and ghoul limits", "Overall XP allocation"],
                ],
            },
        },
        {
            "title": "Same archetype, different sheets",
            "bullets": [
                "Clan changes discipline costs and power eligibility.",
                "Predator changes skills, backgrounds, and package.",
                "Random roll on each weighted pick.",
                "Jittered XP target shares.",
                "Step 8 and free background disadvantages aren't guaranteed.",
            ],
        },
        {
            "title": "More detail",
            "paragraphs": [
                "Weight Map: visual bias for archetype + predator + clan before you generate.",
                "Maintainers: bias ranges and data paths in docs/archetype-weight-guidelines.md.",
            ],
            "link": {"label": "Open Weight Map", "page": "weights"},
        },
    ]
