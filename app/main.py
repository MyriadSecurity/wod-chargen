"""PyScript UI entry point."""

from __future__ import annotations

from pyscript import document, window
from pyscript.ffi import create_proxy

_weight_app = None
_strategy_app = None
_hash_handler = None


def _hide_loading() -> None:
    overlay = document.getElementById("loading-overlay")
    if overlay:
        overlay.classList.add("hidden")


def _show_error(msg: str) -> None:
    _hide_loading()
    err = document.getElementById("py-error")
    if err:
        err.classList.remove("hidden")
        err.innerText = msg


def _current_page() -> str:
    raw = (window.location.hash or "").lstrip("#")
    if raw.startswith("weights"):
        return "weights"
    if raw.startswith("strategy"):
        return "strategy"
    return "generator"


def _mount_app() -> None:
    global _weight_app, _strategy_app
    root = document.getElementById("app-root")
    if not root:
        return
    page = _current_page()
    if page == "weights":
        from app.weight_map import WeightMapApp

        _strategy_app = None
        if _weight_app is None:
            _weight_app = WeightMapApp(root)
            _weight_app.mount()
        else:
            _weight_app.root = root
            _weight_app._parse_hash()
            _weight_app._render()
    elif page == "strategy":
        from app.strategy_page import StrategyPageApp

        _weight_app = None
        if _strategy_app is None:
            _strategy_app = StrategyPageApp(root)
            _strategy_app.mount()
        else:
            _strategy_app.root = root
            _strategy_app._parse_hash()
            _strategy_app._render()
    else:
        _weight_app = None
        _strategy_app = None
        from app.wizard import WizardApp

        WizardApp(root).mount()


def main() -> None:
    global _hash_handler
    try:

        def on_hash_change(_=None):
            _mount_app()

        _hash_handler = create_proxy(on_hash_change)
        window.addEventListener("hashchange", _hash_handler)
        _mount_app()
        _hide_loading()
    except Exception as exc:
        import traceback

        _show_error(f"Failed to start app:\n\n{exc}\n\n{traceback.format_exc()}")


main()
