"""PyScript UI entry point."""

from __future__ import annotations

from pyscript import document


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


def main() -> None:
    try:
        from app.wizard import WizardApp

        root = document.getElementById("app-root")
        wizard = WizardApp(root)
        wizard.mount()
        _hide_loading()
    except Exception as exc:
        import traceback

        _show_error(f"Failed to start app:\n\n{exc}\n\n{traceback.format_exc()}")


main()
