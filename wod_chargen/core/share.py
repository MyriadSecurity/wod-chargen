"""Share URL encode/decode — schema 0.1."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

SUPPORTED_SCHEMAS = {"0.1"}
from wod_chargen import __version__ as ENGINE_VERSION


@dataclass
class SharePayload:
    schema: str = "0.1"
    seed: int = 0
    game: str = "lotn_v5"
    venue: str = "mes_end_to_dawn"
    options: dict[str, Any] = field(default_factory=dict)

    def to_query_params(self) -> dict[str, str]:
        params: dict[str, str] = {
            "schema": self.schema,
            "seed": str(self.seed),
            "game": self.game,
            "venue": self.venue,
        }
        for key, value in sorted(self.options.items()):
            if value is None or value == "":
                continue
            params[key] = str(value)
        return params

    def to_url(self, base: str = "") -> str:
        qs = urlencode(self.to_query_params())
        if base:
            parsed = urlparse(base)
            return urlunparse(parsed._replace(query=qs))
        return f"?{qs}"


def decode_query(query: str) -> SharePayload:
    raw = parse_qs(query.lstrip("?"), keep_blank_values=False)
    flat = {k: v[0] for k, v in raw.items()}

    schema = flat.get("schema", "")
    if schema not in SUPPORTED_SCHEMAS:
        raise ValueError(f"Unsupported or missing schema: {schema!r}")

    reserved = {"schema", "seed", "game", "venue"}
    options = {k: v for k, v in flat.items() if k not in reserved}

    try:
        seed = int(flat.get("seed", "0"))
    except ValueError as exc:
        raise ValueError("Invalid seed") from exc

    return SharePayload(
        schema=schema,
        seed=seed,
        game=flat.get("game", "lotn_v5"),
        venue=flat.get("venue", "mes_end_to_dawn"),
        options=options,
    )


def encode_payload(payload: SharePayload) -> str:
    return payload.to_url()


def wizard_share_options(
    *,
    character_type: str,
    arch: str,
    sub: str,
    clan: str = "",
    domitor_clan: str = "",
    approval: str = "",
    venue_requires_approval_month: bool = False,
) -> dict[str, str]:
    """Build query options for schema 0.1 share URLs."""
    opts = {
        "type": character_type,
        "arch": arch,
        "sub": sub,
    }
    if character_type == "vampire":
        opts["clan"] = clan
    elif character_type == "ghoul":
        opts["domitor_clan"] = domitor_clan
    if venue_requires_approval_month and approval:
        opts["approval"] = approval
    return opts


def browser_share_url(pathname: str, payload: SharePayload) -> str:
    """Absolute path + query string suitable for clipboard/history."""
    path = pathname or "/"
    return f"{path}{payload.to_url()}"
