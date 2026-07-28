#!/usr/bin/env python3
"""Monte Carlo frequency reports for every SPI archetype × subtype.

Locks archetype + subtype; leaves division / faction / affinity unlocked.
Writes one markdown file per pair plus an index under -o.
"""

from __future__ import annotations

import argparse
import sys
import time
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from wod_chargen.games.spi.archetypes import get_archetype, load_manifest  # noqa: E402
from wod_chargen.games.spi.generator import generate_character  # noqa: E402
from wod_chargen.venues import load_venue  # noqa: E402


def _pct(n: int, total: int) -> float:
    return 100.0 * n / total if total else 0.0


def _fmt_pct(n: int, total: int) -> str:
    return f"{_pct(n, total):5.1f}%"


def _primary_affinity(affinities: dict[str, int]) -> str:
    best = max(affinities.items(), key=lambda kv: (kv[1], kv[0]))
    return best[0] if best[1] > 0 else "(none)"


@dataclass
class PairStats:
    archetype: str
    sub: str
    arch_label: str
    sub_label: str
    runs: int = 0
    attr_ratings: dict[str, Counter[int]] = field(default_factory=lambda: defaultdict(Counter))
    skill_ratings: dict[str, Counter[int]] = field(default_factory=lambda: defaultdict(Counter))
    merit_presence: Counter[str] = field(default_factory=Counter)
    merit_dots_sum: Counter[str] = field(default_factory=Counter)
    merit_dot_hist: dict[str, Counter[int]] = field(default_factory=lambda: defaultdict(Counter))
    primary_affinity: Counter[str] = field(default_factory=Counter)
    affinity_ratings: dict[str, Counter[int]] = field(default_factory=lambda: defaultdict(Counter))
    specialty_skills: Counter[str] = field(default_factory=Counter)
    divisions: Counter[str] = field(default_factory=Counter)
    factions: Counter[str] = field(default_factory=Counter)
    virtues: Counter[str] = field(default_factory=Counter)
    vices: Counter[str] = field(default_factory=Counter)

    def observe(self, char: dict[str, Any]) -> None:
        self.runs += 1
        for trait, rating in char["attributes"].items():
            self.attr_ratings[trait][int(rating)] += 1
        for trait, rating in char["skills"].items():
            self.skill_ratings[trait][int(rating)] += 1
        for mid, dots in char["merits"].items():
            d = int(dots)
            if d <= 0:
                continue
            self.merit_presence[mid] += 1
            self.merit_dots_sum[mid] += d
            self.merit_dot_hist[mid][d] += 1
        affinities = {k: int(v) for k, v in char["affinities"].items()}
        self.primary_affinity[_primary_affinity(affinities)] += 1
        for aid, rating in affinities.items():
            self.affinity_ratings[aid][rating] += 1
        for spec in char.get("specialties") or []:
            skill = str(spec).split(":", 1)[0]
            self.specialty_skills[skill] += 1
        self.divisions[str(char.get("division") or "")] += 1
        self.factions[str(char.get("faction") or "")] += 1
        self.virtues[str(char.get("virtue") or "")] += 1
        self.vices[str(char.get("vice") or "")] += 1

    def top_at_least(self, bucket: dict[str, Counter[int]], threshold: int, n: int = 3) -> list[tuple[str, float]]:
        scored: list[tuple[str, float]] = []
        for trait, counts in bucket.items():
            hits = sum(c for r, c in counts.items() if r >= threshold)
            scored.append((trait, _pct(hits, self.runs)))
        scored.sort(key=lambda x: (-x[1], x[0]))
        return scored[:n]

    def top_merits(self, n: int = 5) -> list[tuple[str, float]]:
        scored = [(mid, _pct(self.merit_presence[mid], self.runs)) for mid in self.merit_presence]
        scored.sort(key=lambda x: (-x[1], x[0]))
        return scored[:n]

    def top_primary_affinity(self) -> tuple[str, float]:
        if not self.primary_affinity:
            return ("(none)", 0.0)
        aid, hits = self.primary_affinity.most_common(1)[0]
        return aid, _pct(hits, self.runs)


def collect_pair(
    archetype: str,
    sub: str,
    runs: int,
    venue: dict[str, Any],
) -> PairStats:
    arch = get_archetype(archetype)
    sub_meta = next(s for s in arch["sub_archetypes"] if s["id"] == sub)
    stats = PairStats(
        archetype=archetype,
        sub=sub,
        arch_label=str(arch.get("label") or archetype),
        sub_label=str(sub_meta.get("label") or sub),
    )
    options = {
        "archetype": archetype,
        "sub": sub,
        "multi_affinity": False,
        "affinity": "any",
    }
    for seed in range(runs):
        result = generate_character(seed, options, venue)
        stats.observe(result.character)
    return stats


def _rating_table(
    title: str,
    ratings: dict[str, Counter[int]],
    runs: int,
    rating_range: range,
    thresholds: list[int],
) -> list[str]:
    lines = [f"## {title}", ""]
    header = ["trait", *[str(r) for r in rating_range], *[f">={t}" for t in thresholds]]
    lines.append("| " + " | ".join(header) + " |")
    lines.append("| " + " | ".join(["---"] * len(header)) + " |")

    rows: list[tuple[float, str, list[str]]] = []
    primary_threshold = thresholds[0] if thresholds else 0
    for trait in sorted(ratings):
        counts = ratings[trait]
        cells = [_fmt_pct(counts[r], runs).strip() for r in rating_range]
        thresh_vals: list[float] = []
        for t in thresholds:
            hits = sum(c for r, c in counts.items() if r >= t)
            thresh_vals.append(_pct(hits, runs))
            cells.append(f"{thresh_vals[-1]:.1f}%")
        sort_key = thresh_vals[0] if thresh_vals else 0.0
        rows.append((sort_key, trait, cells))
    rows.sort(key=lambda x: (-x[0], x[1]))
    for _, trait, cells in rows:
        lines.append("| " + " | ".join([trait, *cells]) + " |")
    lines.append("")
    _ = primary_threshold
    return lines


def _counter_table(title: str, counter: Counter[str], runs: int, *, min_pct: float = 0.0) -> list[str]:
    lines = [f"## {title}", ""]
    lines.append("| id | count | pct |")
    lines.append("| --- | ---: | ---: |")
    for key, hits in counter.most_common():
        pct = _pct(hits, runs)
        if pct < min_pct:
            continue
        lines.append(f"| {key} | {hits} | {pct:.1f}% |")
    lines.append("")
    return lines


def _merit_table(stats: PairStats) -> list[str]:
    lines = ["## Merits", ""]
    lines.append("| merit | presence | mean dots (all) | mean dots (owners) | dots histogram |")
    lines.append("| --- | ---: | ---: | ---: | --- |")
    rows: list[tuple[float, str, list[str]]] = []
    for mid, hits in stats.merit_presence.items():
        presence = _pct(hits, stats.runs)
        mean_all = stats.merit_dots_sum[mid] / stats.runs
        mean_own = stats.merit_dots_sum[mid] / hits
        hist = ", ".join(
            f"{d}:{stats.merit_dot_hist[mid][d]}"
            for d in sorted(stats.merit_dot_hist[mid])
        )
        rows.append(
            (
                presence,
                mid,
                [
                    f"{presence:.1f}%",
                    f"{mean_all:.2f}",
                    f"{mean_own:.2f}",
                    hist,
                ],
            )
        )
    rows.sort(key=lambda x: (-x[0], x[1]))
    for _, mid, cells in rows:
        lines.append("| " + " | ".join([mid, *cells]) + " |")
    lines.append("")
    return lines


def render_pair_markdown(stats: PairStats) -> str:
    lines = [
        f"# {stats.arch_label} / {stats.sub_label}",
        "",
        f"- Archetype: `{stats.archetype}`",
        f"- Subtype: `{stats.sub}`",
        f"- Runs: {stats.runs}",
        f"- Locks: archetype + sub; division/faction/affinity unlocked",
        "",
    ]
    lines.extend(
        _rating_table(
            "Attributes",
            dict(stats.attr_ratings),
            stats.runs,
            range(1, 6),
            [4, 5],
        )
    )
    lines.extend(
        _rating_table(
            "Skills",
            dict(stats.skill_ratings),
            stats.runs,
            range(0, 6),
            [3, 4, 5],
        )
    )
    lines.extend(_merit_table(stats))
    lines.extend(_counter_table("Primary Affinity", stats.primary_affinity, stats.runs))
    lines.extend(
        _rating_table(
            "Affinity Ratings",
            dict(stats.affinity_ratings),
            stats.runs,
            range(0, 6),
            [1, 3, 4],
        )
    )
    lines.extend(_counter_table("Specialty Skills", stats.specialty_skills, stats.runs))
    lines.extend(_counter_table("Divisions", stats.divisions, stats.runs))
    lines.extend(_counter_table("Factions", stats.factions, stats.runs))
    lines.extend(_counter_table("Virtues", stats.virtues, stats.runs))
    lines.extend(_counter_table("Vices", stats.vices, stats.runs))
    return "\n".join(lines) + "\n"


def _headline_cell(items: list[tuple[str, float]], digits: int = 0) -> str:
    if not items:
        return "—"
    fmt = f"{{:.{digits}f}}" if digits else "{:.0f}"
    return ", ".join(f"{name} ({fmt.format(pct)}%)" for name, pct in items)


def render_index(all_stats: list[PairStats]) -> str:
    lines = [
        "# SPI archetype frequency index",
        "",
        f"Runs per pair: **{all_stats[0].runs if all_stats else 0}**",
        "",
        "| Archetype | Subtype | Report | Top attrs ≥4 | Top skills ≥4 | Top merits | Primary affinity |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for s in all_stats:
        fname = f"{s.archetype}_{s.sub}.md"
        lines.append(
            "| "
            + " | ".join(
                [
                    s.arch_label,
                    s.sub_label,
                    f"[`{fname}`]({fname})",
                    _headline_cell(s.top_at_least(dict(s.attr_ratings), 4, 3)),
                    _headline_cell(s.top_at_least(dict(s.skill_ratings), 4, 3)),
                    _headline_cell(s.top_merits(3)),
                    _headline_cell([s.top_primary_affinity()]),
                ]
            )
            + " |"
        )
    lines.append("")
    return "\n".join(lines)


def iter_pairs(archetype: str | None, sub: str | None) -> list[tuple[str, str]]:
    manifest = load_manifest()
    subtypes = manifest.get("subtypes") or {}
    pairs: list[tuple[str, str]] = []
    for aid, subs in subtypes.items():
        if archetype and aid != archetype:
            continue
        for sid in subs:
            if sub and sid != sub:
                continue
            pairs.append((aid, sid))
    if archetype and sub and not pairs:
        raise SystemExit(f"Unknown pair: {archetype}/{sub}")
    if archetype and not pairs:
        raise SystemExit(f"Unknown archetype or no matching subtypes: {archetype}")
    return pairs


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", type=int, default=1000)
    parser.add_argument("--venue", default="fixed_35")
    parser.add_argument("-o", "--output", type=Path, default=Path("reports/spi_archetype_freq"))
    parser.add_argument("--archetype", default=None, help="Limit to one primary archetype id")
    parser.add_argument("--sub", default=None, help="Limit to one subtype id (use with --archetype)")
    args = parser.parse_args()

    if args.sub and not args.archetype:
        raise SystemExit("--sub requires --archetype")
    if args.runs < 1:
        raise SystemExit("--runs must be >= 1")

    pairs = iter_pairs(args.archetype, args.sub)
    venue = load_venue(args.venue)
    outdir: Path = args.output
    outdir.mkdir(parents=True, exist_ok=True)

    print(f"Venue={args.venue} runs={args.runs} pairs={len(pairs)} → {outdir}")
    all_stats: list[PairStats] = []
    t0 = time.perf_counter()
    for i, (aid, sid) in enumerate(pairs, start=1):
        pair_t0 = time.perf_counter()
        stats = collect_pair(aid, sid, args.runs, venue)
        elapsed = time.perf_counter() - pair_t0
        path = outdir / f"{aid}_{sid}.md"
        path.write_text(render_pair_markdown(stats), encoding="utf-8")
        all_stats.append(stats)
        top_a = _headline_cell(stats.top_at_least(dict(stats.attr_ratings), 4, 2))
        top_s = _headline_cell(stats.top_at_least(dict(stats.skill_ratings), 4, 2))
        print(f"[{i}/{len(pairs)}] {aid}/{sid}  {elapsed:.1f}s  attrs@4: {top_a}  skills@4: {top_s}")

    index_path = outdir / "_index.md"
    index_path.write_text(render_index(all_stats), encoding="utf-8")
    total = time.perf_counter() - t0
    print(f"Wrote {index_path} ({len(all_stats)} reports, {total:.1f}s)")


if __name__ == "__main__":
    main()
