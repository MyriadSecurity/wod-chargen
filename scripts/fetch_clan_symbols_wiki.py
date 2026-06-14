#!/usr/bin/env python3
"""Download official V5 clan symbols from the Paradox VTM wiki."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "static" / "img" / "clans"
WIKI = "https://vtm.paradoxwikis.com"
CATEGORY = f"{WIKI}/Category:Clan_symbols"

# App clan id -> wiki File: page title
CLAN_WIKI_FILES: dict[str, str] = {
    "brujah": "Brujah symbol.png",
    "gangrel": "Gangrel symbol.png",
    "malkavian": "Malkavian symbol.png",
    "nosferatu": "Nosferatu symbol.png",
    "toreador": "Toreador symbol.png",
    "tremere": "Tremere symbol.png",
    "ventrue": "Ventrue symbol.png",
    "lasombra": "Lasombra symbol.png",
    "ministry": "Ministry symbol.png",
    "hecata": "Hecata symbol.png",
    "ravnos": "Ravnos symbol.png",
    "tzimisce": "Tzimisce symbol.png",
    "salubri": "Salubri symbol.png",
    "caitiff": "Caitiff symbol.png",
    "thin_blood": "Thinblood_symbol.png",
}


def _wiki_file_title(filename: str) -> str:
    return f"File:{filename}"


def _slug_from_url(url: str) -> str | None:
    name = unquote(Path(urlparse(url).path).name)
    m = re.match(r"(\d+px-)?(.+)\.png$", name, re.I)
    if not m:
        return None
    stem = m.group(2).replace("_", " ")
    m2 = re.match(r"(.+?) symbol$", stem, re.I)
    return m2.group(1).lower().replace(" ", "_").replace("-", "_") if m2 else None


def fetch_via_api(page) -> dict[str, str]:
    """Resolve download URLs through MediaWiki API using the browser session."""
    titles = "|".join(_wiki_file_title(v) for v in CLAN_WIKI_FILES.values())
    api_url = (
        f"{WIKI}/api.php?action=query&format=json&prop=imageinfo"
        f"&iiprop=url&iiurlwidth=512&titles={titles}"
    )
    data = page.evaluate(
        """async (url) => {
            const res = await fetch(url);
            return await res.json();
        }""",
        api_url,
    )
    file_to_clan = {v.lower(): k for k, v in CLAN_WIKI_FILES.items()}
    urls: dict[str, str] = {}
    for page_data in data.get("query", {}).get("pages", {}).values():
        title = page_data.get("title", "")
        m = re.match(r"File:(.+)\.png", title, re.I)
        if not m:
            continue
        wiki_file = f"{m.group(1)}.png".lower()
        clan_id = file_to_clan.get(wiki_file)
        if not clan_id:
            continue
        info = (page_data.get("imageinfo") or [{}])[0]
        url = info.get("thumburl") or info.get("url")
        if url:
            urls[clan_id] = url
    return urls


def fetch_via_category(page) -> dict[str, str]:
    page.goto(CATEGORY, wait_until="networkidle", timeout=120_000)
    links = page.eval_on_selector_all(
        'a[href*="/File:"]',
        "els => els.map(e => e.href)",
    )
    urls: dict[str, str] = {}
    for href in links:
        if " symbol" not in href and " Symbol" not in href:
            continue
        m = re.search(r"/File:(.+?)(?:%20| )symbol\.png", href, re.I)
        if not m:
            continue
        clan_slug = m.group(1).lower().replace("%20", "_").replace(" ", "_").replace("-", "_")
        file_page = href if href.startswith("http") else f"{WIKI}{href}"
        page.goto(file_page, wait_until="networkidle", timeout=120_000)
        img_url = page.eval_on_selector(
            "#file img, .fullMedia a, a.internal",
            """el => {
                if (!el) return null;
                if (el.tagName === 'IMG') return el.src;
                return el.href || null;
            }""",
        )
        if img_url and img_url.endswith(".png"):
            urls[clan_slug] = img_url
    return urls


def download_symbols(page, url_map: dict[str, str]) -> list[str]:
    OUT.mkdir(parents=True, exist_ok=True)
    manifest: dict[str, str] = {}
    written: list[str] = []

    for clan_id, url in sorted(url_map.items()):
        if clan_id not in CLAN_WIKI_FILES:
            print(f"skip unmapped clan id: {clan_id}", file=sys.stderr)
            continue

        resp = page.request.get(url)
        if not resp.ok:
            print(f"failed {clan_id}: HTTP {resp.status}", file=sys.stderr)
            continue
        body = resp.body()
        if not body.startswith(b"\x89PNG"):
            print(f"failed {clan_id}: not PNG ({body[:20]!r})", file=sys.stderr)
            continue

        out_path = OUT / f"{clan_id}.png"
        out_path.write_bytes(body)
        manifest[clan_id] = f"static/img/clans/{clan_id}.png"
        written.append(clan_id)
        print(f"wrote {out_path.name} ({len(body)} bytes)")

    manifest_path = OUT / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return written


def main() -> int:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Install dev deps: uv sync --extra dev && uv run playwright install chromium", file=sys.stderr)
        return 1

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(WIKI, wait_until="networkidle", timeout=120_000)

        url_map = fetch_via_api(page)
        if len(url_map) < len(CLAN_WIKI_FILES):
            print(f"API returned {len(url_map)} symbols; trying category scrape…", file=sys.stderr)
            cat_map = fetch_via_category(page)
            url_map = {**cat_map, **url_map}

        if not url_map:
            print("No symbol URLs resolved.", file=sys.stderr)
            browser.close()
            return 1

        written = download_symbols(page, url_map)
        browser.close()

    if written:
        import subprocess

        invert_script = Path(__file__).resolve().parent / "invert_clan_symbols.py"
        subprocess.run([sys.executable, str(invert_script)], check=True)

    missing = set(CLAN_WIKI_FILES) - set(written)
    if missing:
        print(f"missing: {', '.join(sorted(missing))}", file=sys.stderr)
    print(f"Downloaded {len(written)}/{len(CLAN_WIKI_FILES)} clan symbols.")
    return 0 if len(written) == len(CLAN_WIKI_FILES) else 1


if __name__ == "__main__":
    raise SystemExit(main())
