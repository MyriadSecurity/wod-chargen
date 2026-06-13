"""Shared pytest fixtures."""

from __future__ import annotations

import functools
import http.server
import socket
import threading
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


class _NoCacheHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Avoid stale PyScript modules when running browser smoke tests."""

    def end_headers(self) -> None:
        if self.path.split("?", 1)[0].endswith((".py", ".json", ".toml", ".html", ".css")):
            self.send_header("Cache-Control", "no-store")
        super().end_headers()


@pytest.fixture(scope="session")
def site_base_url() -> str:
    """Serve the repo root over HTTP for static and browser smoke tests."""
    port = _free_port()
    handler = functools.partial(_NoCacheHTTPRequestHandler, directory=str(ROOT))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", port), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{port}"
    server.shutdown()
