"""Browser smoke test — PyScript must boot the wizard on the main page."""

from __future__ import annotations

import time

import pytest

try:
    from playwright.sync_api import sync_playwright

    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False

BOOT_TIMEOUT_MS = 120_000
POLL_MS = 500


def _wait_for_app(page, timeout_ms: int = BOOT_TIMEOUT_MS) -> None:
    deadline = time.monotonic() + timeout_ms / 1000
    while time.monotonic() < deadline:
        boot_error = page.evaluate(
            """() => {
                const el = document.getElementById('py-error');
                if (!el || el.classList.contains('hidden')) return null;
                return el.innerText || 'Unknown PyScript error';
            }"""
        )
        if boot_error:
            raise AssertionError(f"Main page failed to boot:\n{boot_error}")

        ready = page.evaluate(
            """() => {
                const root = document.getElementById('app-root');
                const overlay = document.getElementById('loading-overlay');
                if (!root || !overlay) return false;
                const booted = root.children.length > 0 && overlay.classList.contains('hidden');
                if (!booted) return false;
                const title = root.querySelector('h1');
                return Boolean(title && title.textContent && title.textContent.length > 0);
            }"""
        )
        if ready:
            return
        page.wait_for_timeout(POLL_MS)
    raise TimeoutError(f"App did not boot within {timeout_ms}ms")


@pytest.mark.skipif(not HAS_PLAYWRIGHT, reason="playwright not installed")
def test_main_page_loads_wizard(site_base_url: str):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--disable-http-cache"])
        context = browser.new_context()
        page = context.new_page()
        page.goto(site_base_url, wait_until="domcontentloaded", timeout=60_000)
        _wait_for_app(page)
        title = page.locator("#app-root h1").first.inner_text()
        assert "Character Generator" in title
        context.close()
        browser.close()


@pytest.mark.skipif(not HAS_PLAYWRIGHT, reason="playwright not installed")
def test_weight_map_page_renders(site_base_url: str):
    """Weight map must boot and render SVG or a visible error — bounded wait."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--disable-http-cache"])
        context = browser.new_context()
        page = context.new_page()
        page.goto(f"{site_base_url}/#weights", wait_until="domcontentloaded", timeout=60_000)

        deadline = time.monotonic() + 90
        last_state = ""
        while time.monotonic() < deadline:
            boot_error = page.evaluate(
                """() => {
                    const el = document.getElementById('py-error');
                    if (!el || el.classList.contains('hidden')) return null;
                    return el.innerText || 'Unknown PyScript error';
                }"""
            )
            if boot_error:
                raise AssertionError(f"Weight map failed to boot:\n{boot_error}")

            state = page.evaluate(
                """() => {
                    const root = document.getElementById('app-root');
                    const overlay = document.getElementById('loading-overlay');
                    if (!root || !overlay || !overlay.classList.contains('hidden')) return 'loading';
                    const title = root.querySelector('h1');
                    if (!title || !title.textContent.toLowerCase().includes('weight map')) return 'no-title';
                    const canvas = document.getElementById('weight-map-canvas');
                    if (!canvas) return 'no-canvas';
                    if (canvas.querySelector('svg')) return 'svg';
                    const err = canvas.querySelector('.weight-map-error');
                    if (err) return 'canvas-error:' + err.textContent;
                    return 'waiting';
                }"""
            )
            last_state = state
            if state == "svg":
                break
            if state.startswith("canvas-error:"):
                raise AssertionError(f"Weight map canvas error: {state.split(':', 1)[1]}")
            page.wait_for_timeout(500)
        else:
            raise TimeoutError(
                f"Weight map did not render within 90s (last state: {last_state!r})"
            )

        assert page.locator("#weight-map-canvas svg").count() >= 1
        context.close()
        browser.close()


@pytest.mark.skipif(not HAS_PLAYWRIGHT, reason="playwright not installed")
def test_share_url_loads_results_sheet(site_base_url: str):
    share_path = (
        "/?schema=0.1&seed=424242&game=lotn_v5&venue=mes_end_to_dawn"
        "&type=vampire&clan=brujah&arch=diplomat&sub=silver_tongue&approval=2026-06"
    )
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--disable-http-cache"])
        context = browser.new_context()
        page = context.new_page()
        page.goto(f"{site_base_url}{share_path}", wait_until="domcontentloaded", timeout=60_000)
        _wait_for_app(page)
        has_sheet = page.evaluate(
            """() => {
                const root = document.getElementById('app-root');
                if (!root) return false;
                return Boolean(
                    root.querySelector('.character-sheet')
                    || root.textContent.includes('Attributes')
                );
            }"""
        )
        assert has_sheet, "Share URL should render a character sheet, not an empty or error state"
        context.close()
        browser.close()
