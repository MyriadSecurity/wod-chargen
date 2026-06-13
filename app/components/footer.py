"""Reusable UI components."""

from __future__ import annotations

from pyscript import document


def dark_pack_footer() -> None:
    from wod_chargen import __version__

    footer = document.createElement("footer")
    footer.className = "no-print border-t border-stone-800 mt-auto py-6 px-4 text-sm text-stone-400"
    footer.innerHTML = f"""
    <div class="max-w-4xl mx-auto flex flex-col gap-3 items-center text-center">
      <img src="static/img/dark-pack-logo.svg" alt="Dark Pack" class="h-8" />
      <p>Portions of the materials are fictitious and claimed under the Dark Pack license.
      This is an <strong>unofficial</strong> fan project, not affiliated with Paradox Interactive.</p>
      <a class="text-blood hover:underline" href="https://www.paradoxinteractive.com/games/world-of-darkness/community/dark-pack-agreement" target="_blank" rel="noopener">Dark Pack Agreement</a>
      <p class="text-stone-500 text-xs">wod-chargen v{__version__}</p>
    </div>
    """
    document.getElementById("app-root").appendChild(footer)
