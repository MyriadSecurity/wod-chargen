#!/usr/bin/env python3
"""Local dev server with no-cache headers for PyScript modules."""

from __future__ import annotations

import argparse
import functools
import http.server
import socket


class NoCacheHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self) -> None:
        if self.path.split("?", 1)[0].endswith((".py", ".json", ".toml", ".html", ".css")):
            self.send_header("Cache-Control", "no-store")
        super().end_headers()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--bind", default="127.0.0.1")
    args = parser.parse_args()

    handler = functools.partial(NoCacheHTTPRequestHandler, directory=".")
    with http.server.ThreadingHTTPServer((args.bind, args.port), handler) as httpd:
        host = args.bind
        if host == "0.0.0.0":
            host = socket.gethostname()
        print(f"Serving with no-cache headers at http://{host}:{args.port}/")
        httpd.serve_forever()


if __name__ == "__main__":
    main()
