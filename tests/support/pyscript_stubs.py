"""Minimal PyScript / js shims so app modules import under CPython."""

from __future__ import annotations

import sys
import types
from typing import Any


class _ClassList:
    def __init__(self) -> None:
        self._classes: set[str] = set()

    def add(self, name: str) -> None:
        self._classes.add(name)

    def remove(self, name: str) -> None:
        self._classes.discard(name)

    def contains(self, name: str) -> bool:
        return name in self._classes


class MockElement:
    def __init__(self, tag: str = "div", element_id: str = "") -> None:
        self.tagName = tag.upper()
        self.id = element_id
        self.className = ""
        self._innerHTML = ""
        self.innerText = ""
        self.textContent = ""
        self.classList = _ClassList()
        self.children: list[MockElement] = []
        self.style = types.SimpleNamespace()
        self.onclick: Any = None
        self.onchange: Any = None
        self.src = ""
        self.alt = ""
        self.href = ""
        self.rel = ""
        self._attrs: dict[str, str] = {}

    @property
    def innerHTML(self) -> str:
        return self._innerHTML

    @innerHTML.setter
    def innerHTML(self, value: str) -> None:
        self._innerHTML = value
        if value == "":
            self.children.clear()

    def appendChild(self, child: MockElement) -> MockElement:
        self.children.append(child)
        return child

    def setAttribute(self, name: str, value: str) -> None:
        self._attrs[name] = value

    def getAttribute(self, name: str) -> str | None:
        return self._attrs.get(name)


class MockClipboard:
    def __init__(self) -> None:
        self.written: list[str] = []

    def writeText(self, text: str) -> None:
        self.written.append(text)


class MockNavigator:
    def __init__(self) -> None:
        self.clipboard = MockClipboard()


class MockHistory:
    def __init__(self) -> None:
        self.replace_calls: list[tuple[Any, str, str]] = []

    def replaceState(self, state: Any, title: str, url: str) -> None:
        self.replace_calls.append((state, title, url))


class MockLocation:
    search = ""
    pathname = "/"
    href = "http://127.0.0.1/"
    _hash = ""

    @property
    def hash(self) -> str:
        return self._hash

    @hash.setter
    def hash(self, value: str) -> None:
        self._hash = value if value.startswith("#") or not value else f"#{value}"


class MockWindow:
    def __init__(self) -> None:
        self.location = MockLocation()
        self.history = MockHistory()
        self.navigator = MockNavigator()
        self._listeners: dict[str, list] = {}

    def addEventListener(self, event: str, handler) -> None:
        self._listeners.setdefault(event, []).append(handler)

    def setTimeout(self, handler, _ms: int = 0):
        if callable(handler):
            handler()
        return 0

    def print(self) -> None:
        pass


class MockDocument:
    def __init__(self) -> None:
        self.elements: dict[str, MockElement] = {
            "app-root": MockElement("div", "app-root"),
            "loading-overlay": MockElement("div", "loading-overlay"),
            "py-error": MockElement("div", "py-error"),
        }
        self.elements["py-error"].classList.add("hidden")
        self.head = MockElement("head")

    def getElementById(self, element_id: str) -> MockElement | None:
        return self.elements.get(element_id)

    def createElement(self, tag: str) -> MockElement:
        el = MockElement(tag)
        if tag == "link":
            el.rel = ""
            el.href = ""
        if tag == "script":
            el.src = ""
        return el


class PyScriptStubs:
    def __init__(self) -> None:
        self.document = MockDocument()
        self.window = MockWindow()

    @property
    def elements(self) -> dict[str, MockElement]:
        return self.document.elements


def install_pyscript_stubs() -> PyScriptStubs:
    """Register pyscript + js stubs; return handles for assertions."""
    existing = sys.modules.get("pyscript")
    if existing is not None and getattr(existing, "_WOD_STUB", False):
        return existing._WOD_HANDLE  # type: ignore[attr-defined]

    handle = PyScriptStubs()

    pyscript_mod = types.ModuleType("pyscript")
    pyscript_mod.document = handle.document
    pyscript_mod.window = handle.window
    pyscript_mod._WOD_STUB = True
    pyscript_mod._WOD_HANDLE = handle

    js_mod = types.ModuleType("js")
    js_mod.null = None

    sys.modules["pyscript"] = pyscript_mod
    sys.modules["js"] = js_mod

    ffi_mod = types.ModuleType("pyscript.ffi")

    def create_proxy(fn):  # noqa: ANN001
        return fn

    ffi_mod.create_proxy = create_proxy
    sys.modules["pyscript.ffi"] = ffi_mod

    return handle
