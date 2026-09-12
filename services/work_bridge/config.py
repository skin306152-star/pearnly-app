"""One collaboration service for every COWORK account, with no tenant allowlist."""

from __future__ import annotations

import os
from dataclasses import dataclass
from urllib.parse import urlsplit
from uuid import UUID

from fastapi import HTTPException


@dataclass(frozen=True)
class Service:
    url: str
    secret: str


def service() -> Service:
    url = os.environ.get("WORK_BRIDGE_URL", "").rstrip("/")
    secret = os.environ.get("WORK_BRIDGE_SECRET", "")
    if not url or not secret:
        raise HTTPException(503, "work.unavailable")
    parsed = urlsplit(url)
    local = os.environ.get("PEARNLY_ENV") == "development"
    if (
        parsed.scheme not in ({"https", "http"} if local else {"https"})
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.path
        or parsed.query
        or parsed.fragment
        or len(secret) < 32
    ):
        raise RuntimeError("Invalid work collaboration service configuration")
    return Service(url, secret)


def remote_username(user_id: str) -> str:
    return "pearnly-" + str(UUID(user_id))
