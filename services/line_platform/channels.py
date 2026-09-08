# -*- coding: utf-8 -*-
"""LINE OA channel registry: public identity + credential resolution.

DMS runs on several official accounts (OA) that belong to one Pearnly provider. Business code
must address an OA by its **stable channel key** (``dms`` / ``dms_a`` / ``dms_b``), never by a
hardcoded Basic ID or friend link. This module is the single source of truth for:

* the public identity safe to hand to browsers (display name, Basic ID, add-friend URL, QR image);
* the environment variable names that hold the secret / access token for each key.

Secrets are only ever read from the process environment (Cloud Run mounts Secret Manager into
env). They are never logged, returned by an API or embedded in this registry.
"""

from __future__ import annotations

import json
import logging
import os
import urllib.parse
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Third-party QR renderer already used by the DMS bind-code dialog (CSP img-src allows it).
# The QR payload is always the channel's public add-friend URL, so QR / link / ID cannot diverge.
QR_IMAGE_ENDPOINT = "https://api.qrserver.com/v1/create-qr-code/"
_FRIEND_URL_PREFIX = "https://line.me/R/ti/p/"


@dataclass(frozen=True)
class LineChannel:
    """Public identity + credential env names for one OA. Never holds a secret value."""

    key: str
    product: str
    display_name: str
    basic_id: str
    secret_env: str
    token_env: str
    credentials_env: str = ""
    liff_env: str = ""

    @property
    def add_friend_url(self) -> str:
        return _FRIEND_URL_PREFIX + self.basic_id

    def public(self) -> dict:
        """Browser-safe payload: no env names, no secret material."""
        return {
            "channel_key": self.key,
            "channel_name": self.display_name,
            "basic_id": self.basic_id,
            "add_friend_url": self.add_friend_url,
            "qr_image_url": qr_image_url(self.add_friend_url),
        }


# Stable keys are API/DB values. Display names / Basic IDs are the only OA-specific facts here;
# secrets stay in the environment (individual vars or a JSON/dotenv blob mounted per key).
DMS_CHANNELS: Dict[str, LineChannel] = {
    "dms": LineChannel(
        key="dms",
        product="dms",
        display_name="ลั่วหยง DMS",
        basic_id="@264tuqln",
        secret_env="LINE_DMS_CHANNEL_SECRET",
        token_env="LINE_DMS_CHANNEL_ACCESS_TOKEN",
        credentials_env="LINE_DMS_CREDENTIALS",
        liff_env="LINE_DMS_LIFF_ID",
    ),
    "dms_a": LineChannel(
        key="dms_a",
        product="dms",
        display_name="A DMS",
        basic_id="@260oecde",
        secret_env="LINE_DMS_A_CHANNEL_SECRET",
        token_env="LINE_DMS_A_CHANNEL_ACCESS_TOKEN",
        credentials_env="LINE_DMS_A_CREDENTIALS",
        liff_env="LINE_DMS_A_LIFF_ID",
    ),
    "dms_b": LineChannel(
        key="dms_b",
        product="dms",
        display_name="B DMS",
        basic_id="@145xbbjo",
        secret_env="LINE_DMS_B_CHANNEL_SECRET",
        token_env="LINE_DMS_B_CHANNEL_ACCESS_TOKEN",
        credentials_env="LINE_DMS_B_CREDENTIALS",
        liff_env="LINE_DMS_B_LIFF_ID",
    ),
}

# Existing rows / old API callers that never sent a channel keep working on the legacy OA.
DEFAULT_DMS_CHANNEL = "dms"


def qr_image_url(add_friend_url: str) -> str:
    return (
        QR_IMAGE_ENDPOINT
        + "?size=240x240&margin=1&data="
        + urllib.parse.quote(add_friend_url, safe="")
    )


def get(channel_key: Optional[str]) -> Optional[LineChannel]:
    return DMS_CHANNELS.get((channel_key or "").strip())


def normalize(channel_key: Optional[str]) -> str:
    """Unknown / empty → legacy default. Callers that must fail closed use :func:`get`."""
    key = (channel_key or "").strip()
    return key if key in DMS_CHANNELS else DEFAULT_DMS_CHANNEL


def is_valid(channel_key: Optional[str]) -> bool:
    return (channel_key or "").strip() in DMS_CHANNELS


def public(channel_key: Optional[str]) -> dict:
    """Public payload for a key; unknown key falls back to the legacy OA (never leaks secrets)."""
    return DMS_CHANNELS[normalize(channel_key)].public()


def list_public() -> List[dict]:
    return [DMS_CHANNELS[key].public() for key in DMS_CHANNELS]


def liff_id(channel_key: Optional[str]) -> str:
    """LIFF app id for an OA. Non-legacy OAs never fall back to the legacy LIFF id.

    Falling back would open a link owned by another OA and silently log the user into the wrong
    channel, so an unset A/B LIFF id simply disables the LIFF-backed entry (honest degradation).
    """
    key = normalize(channel_key)
    cfg = DMS_CHANNELS[key]
    value = (os.environ.get(cfg.liff_env) or "").strip() if cfg.liff_env else ""
    if not value and key == DEFAULT_DMS_CHANNEL:
        value = (os.environ.get("LINE_LIFF_ID") or "").strip()
    return value


def menu_name(base: str, channel_key: Optional[str]) -> str:
    """Rich-menu name for an OA; the legacy OA keeps the historical unsuffixed name."""
    key = normalize(channel_key)
    return base if key == DEFAULT_DMS_CHANNEL else f"{base}-{key}"


# ── credential resolution ─────────────────────────────────────────────────


def _parse_blob(raw: str) -> Dict[str, str]:
    """Accept a JSON object or dotenv-style text mounted from Secret Manager."""
    text = (raw or "").strip()
    if not text:
        return {}
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            return {str(k): str(v) for k, v in data.items()}
    except Exception:
        pass  # not JSON → try dotenv below
    out: Dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        out[name.strip()] = value.strip().strip('"').strip("'")
    return out


def _pick(blob: Dict[str, str], names: Tuple[str, ...]) -> str:
    for name in names:
        value = (blob.get(name) or "").strip()
        if value:
            return value
    return ""


def resolve_credentials(
    secret_env: str, token_env: str, credentials_env: str = ""
) -> Tuple[str, str]:
    """Return ``(channel_secret, channel_access_token)`` for one channel profile.

    Individual env vars win; a single blob (JSON or dotenv) is the fallback used when a
    per-OA Secret Manager secret is mounted as one variable. Missing material → empty strings.
    """
    secret = (os.environ.get(secret_env) or "").strip() if secret_env else ""
    token = (os.environ.get(token_env) or "").strip() if token_env else ""
    if secret and token:
        return secret, token
    if not credentials_env:
        return secret, token
    blob = _parse_blob(os.environ.get(credentials_env) or "")
    if not blob:
        return secret, token
    secret = secret or _pick(
        blob,
        ("channel_secret", "channelSecret", "secret", secret_env),
    )
    token = token or _pick(
        blob,
        ("channel_access_token", "channelAccessToken", "access_token", "token", token_env),
    )
    return secret, token
