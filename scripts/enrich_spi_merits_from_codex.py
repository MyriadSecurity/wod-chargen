#!/usr/bin/env python3
"""Enrich SPI merit extracts with Codex of Darkness short summaries.

Codex live site is often behind Anubis bot-protection. Prefer a local cache of
Wayback / previously fetched markdown tables under reference/spi/codex_cache/.

Usage:
    python3 scripts/enrich_spi_merits_from_codex.py
    python3 scripts/enrich_spi_merits_from_codex.py --cache reference/spi/codex_cache
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MERITS = ROOT / "reference" / "spi" / "extracted" / "merits.json"
DEFAULT_CACHE = ROOT / "reference" / "spi" / "codex_cache"

BOOK_RE = re.compile(
    r"^(CofD|HL|HtV|HTV|CTL|CtL|VtR|VTR|WtF|WTF|MtA|MTA|GtS|GTS|GtSE|BTP|DTR|MTC|GTTN)"
    r"(\s+2e)?\s+\d+",
    re.I,
)


def slug(text: str) -> str:
    text = text.replace("´", "'").replace("’", "'").lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_")


def split_md_row(line: str) -> list[str]:
    line = line.strip()
    if not line.startswith("|"):
        return []
    parts = [p.strip() for p in line.strip("|").split("|")]
    return parts


def is_separator(cells: list[str]) -> bool:
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", c.replace(" ", "")) for c in cells if c)


def normalize_row(cells: list[str]) -> dict[str, str] | None:
    """Handle Codex tables where empty Prerequisites shifts Description/Book left."""
    if len(cells) < 2:
        return None
    name = cells[0].strip()
    if not name or name.lower() == "merit" or name.startswith("---"):
        return None
    # Drop shared-merit marker columns (● / ○) when present as col 2
    if len(cells) >= 5 and cells[1] in {"●", "○", "•", ""}:
        cells = [cells[0], *cells[2:]]

    rating = cells[1].strip() if len(cells) > 1 else ""
    prereq = cells[2].strip() if len(cells) > 2 else ""
    desc = cells[3].strip() if len(cells) > 3 else ""
    book = cells[4].strip() if len(cells) > 4 else ""

    # Shifted: Description landed in Prerequisites, Book in Description
    if not book and desc and BOOK_RE.match(desc) and prereq and not BOOK_RE.match(prereq):
        book, desc, prereq = desc, prereq, ""
    elif not book and BOOK_RE.match(prereq) and not desc:
        book, prereq = prereq, ""
    elif not desc and prereq and not BOOK_RE.match(prereq) and len(prereq) > 40:
        # Prerequisites empty; description in prereq column; book may be missing
        desc, prereq = prereq, ""

    if not desc:
        return None
    return {
        "label": name,
        "id": slug(name),
        "rating": rating,
        "prerequisites": prereq,
        "summary": re.sub(r"\s+", " ", desc).strip(),
        "book": book,
    }


def parse_markdown_tables(text: str, source: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for line in text.splitlines():
        if "|" not in line:
            continue
        cells = split_md_row(line)
        if not cells or is_separator(cells):
            continue
        entry = normalize_row(cells)
        if entry:
            entry["source"] = source
            rows.append(entry)
    return rows


def _read_cache_file(path: Path) -> str:
    raw = path.read_bytes()
    if raw[:2] == b"\x1f\x8b":
        import gzip

        raw = gzip.decompress(raw)
    return raw.decode("utf-8", errors="replace")


def parse_html_tables(text: str, source: str) -> list[dict[str, str]]:
    """Pull rows from HTML <table> blocks (Wayback MediaWiki dumps)."""
    from html.parser import HTMLParser

    class _Parser(HTMLParser):
        def __init__(self) -> None:
            super().__init__()
            self.in_td = False
            self.cell: list[str] = []
            self.row: list[str] = []
            self.rows: list[list[str]] = []

        def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
            if tag == "tr":
                self.row = []
            elif tag in ("td", "th"):
                self.in_td = True
                self.cell = []

        def handle_endtag(self, tag: str) -> None:
            if tag in ("td", "th") and self.in_td:
                self.in_td = False
                self.row.append(re.sub(r"\s+", " ", "".join(self.cell)).strip())
            elif tag == "tr" and self.row:
                self.rows.append(self.row)

        def handle_data(self, data: str) -> None:
            if self.in_td:
                self.cell.append(data)

    parser = _Parser()
    parser.feed(text)
    out: list[dict[str, str]] = []
    for row in parser.rows:
        entry = normalize_row(row)
        if entry:
            entry["source"] = source
            out.append(entry)
    return out


def load_codex_index(cache_dir: Path) -> dict[str, dict[str, str]]:
    index: dict[str, dict[str, str]] = {}
    files = (
        sorted(cache_dir.glob("*.md"))
        + sorted(cache_dir.glob("*.txt"))
        + sorted(cache_dir.glob("*.html"))
    )
    for path in files:
        text = _read_cache_file(path)
        entries = parse_markdown_tables(text, path.name)
        if "<table" in text.lower() or "<tr" in text.lower():
            entries.extend(parse_html_tables(text, path.name))
        for entry in entries:
            existing = index.get(entry["id"])
            if existing is None or len(entry["summary"]) > len(existing["summary"]):
                index[entry["id"]] = entry
    return index


def enrich(merits_path: Path, cache_dir: Path) -> dict[str, Any]:
    data = json.loads(merits_path.read_text(encoding="utf-8"))
    index = load_codex_index(cache_dir)
    matched = 0
    for merit in data.get("merits", []):
        hit = index.get(merit["id"])
        if not hit and merit.get("label"):
            hit = index.get(slug(merit["label"]))
        if not hit:
            continue
        merit["summary"] = hit["summary"]
        if hit.get("book"):
            merit["book"] = hit["book"]
        merit["summary_source"] = f"codex:{hit['source']}"
        matched += 1
    data["codex_enrichment"] = {
        "cache_dir": str(cache_dir.relative_to(ROOT)) if cache_dir.is_relative_to(ROOT) else str(cache_dir),
        "codex_entries_loaded": len(index),
        "merits_matched": matched,
        "merits_total": len(data.get("merits", [])),
    }
    return data


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--merits", type=Path, default=DEFAULT_MERITS)
    parser.add_argument("--cache", type=Path, default=DEFAULT_CACHE)
    parser.add_argument(
        "-o",
        "--out",
        type=Path,
        default=None,
        help="Output path (default: overwrite --merits)",
    )
    args = parser.parse_args()
    if not args.merits.is_file():
        print(f"Missing merits file: {args.merits}")
        return 1
    if not args.cache.is_dir():
        print(f"Missing Codex cache dir: {args.cache}")
        print("Populate with Wayback markdown dumps of Codex Merits_*_2e pages.")
        return 1

    enriched = enrich(args.merits, args.cache)
    out = args.out or args.merits
    out.write_text(json.dumps(enriched, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    stats = enriched["codex_enrichment"]
    print(f"Wrote {out}")
    print(
        f"  Codex entries: {stats['codex_entries_loaded']}; "
        f"matched {stats['merits_matched']}/{stats['merits_total']}"
    )
    # Show a couple examples
    samples = [m for m in enriched["merits"] if m.get("summary")][:3]
    for m in samples:
        print(f"  - {m['label']}: {m['summary'][:90]}…")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
