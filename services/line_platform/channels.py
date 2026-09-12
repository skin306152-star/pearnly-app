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

# Env vars holding a LINE Login (LIFF) app id owned by the shared Pearnly Provider. A DMS OA may
# reuse one of these only when its ``LineChannel`` declares it in ``provider_liff_env``; a new OA
# that declares nothing resolves to no LIFF at all and fails closed (see
# ``tests/unit/test_dms_channel_registry_contract.py``). Never widen this implicitly.
PROVIDER_LIFF_ENVS: Tuple[str, ...] = ("LINE_LIFF_ID",)

# Third-party QR renderer already used by the DMS bind-code dialog (CSP img-src allows it).
# The QR payload is always the channel's public add-friend URL, so QR / link / ID cannot diverge.
QR_IMAGE_ENDPOINT = "https://api.qrserver.com/v1/create-qr-code/"
_FRIEND_URL_PREFIX = "https://line.me/R/ti/p/"

# Webhook entry points are derived from the stable key so a registry entry can never be half
# wired: ``dms`` keeps the historical path, every other OA gets ``/<key without dms_ prefix>``.
_WEBHOOK_BASE = "/api/line/dms/webhook"


@dataclass(frozen=True)
class LineChannel:
    """Public identity + credential env names for one OA. Never holds a secret value.

    ``liff_env`` names this OA's own LIFF app id. ``provider_liff_env`` names the shared Provider
    LIFF app the OA is explicitly allowed to reuse while it has no LIFF of its own; leaving it
    empty is the fail-closed default, so an OA only borrows the shared login app when the registry
    says so (never because of its key prefix or its Provider).
    """

    key: str
    product: str
    display_name: str
    basic_id: str
    secret_env: str
    token_env: str
    credentials_env: str = ""
    liff_env: str = ""
    provider_liff_env: str = ""

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
# All three DMS Messaging API channels and the shared LINE Login channel live under the same
# LINE Provider. LINE therefore gives the same user id to their ID tokens and webhook events;
# channel_key still scopes every Pearnly binding, session and ticket. The LIFF reuse that follows
# from sharing a Provider is declared per OA through ``provider_liff_env`` (see the class doc).
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
        provider_liff_env="LINE_LIFF_ID",
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
        provider_liff_env="LINE_LIFF_ID",
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
        provider_liff_env="LINE_LIFF_ID",
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


def resolve(channel_key: Optional[str]) -> Optional[str]:
    """Strict key resolution for invariant paths.

    Empty / missing → the legacy ``dms`` OA (old callers keep working on exactly one OA).
    Unknown non-empty → ``None`` so binding / state / lock scoping fails closed instead of
    silently treating a foreign key as the legacy OA. Browser-facing and back-compat payloads
    keep using :func:`normalize`.
    """
    key = (channel_key or "").strip()
    if not key:
        return DEFAULT_DMS_CHANNEL
    return key if key in DMS_CHANNELS else None


def is_valid(channel_key: Optional[str]) -> bool:
    return (channel_key or "").strip() in DMS_CHANNELS


def public(channel_key: Optional[str]) -> dict:
    """Public payload for a key; unknown key falls back to the legacy OA (never leaks secrets)."""
    return DMS_CHANNELS[normalize(channel_key)].public()


def list_public() -> List[dict]:
    return [DMS_CHANNELS[key].public() for key in DMS_CHANNELS]


def _env_value(name: str) -> str:
    return (os.environ.get(name) or "").strip() if name else ""


def liff_id(channel_key: Optional[str]) -> str:
    """LIFF app id for an OA: its own app, else the Provider LIFF it explicitly declares.

    A/B and the legacy DMS OA are Messaging API channels under the same LINE Provider, while LIFF
    belongs to its LINE Login channel. They therefore reuse the Provider LIFF while
    ``provider_liff_env`` says so. The URL and backend token still carry ``channel_key`` and
    resolve the matching binding, so sharing login identity does not merge OA sessions or
    credentials. Unknown / undeclared keys → "" (fail closed, never another OA's link).
    """
    key = resolve(channel_key)
    if key is None:
        return ""
    cfg = DMS_CHANNELS[key]
    return _env_value(cfg.liff_env) or _env_value(cfg.provider_liff_env)


def liff_env_name(channel_key: Optional[str]) -> str:
    """Env var holding this OA's effective LIFF id; "" = no declared LIFF (fail closed).

    Token verification derives its ``client_id`` from this env name, so an OA that declares no
    LIFF ownership is refused before any verify request instead of borrowing the Provider app.
    """
    cfg = get(channel_key)
    if not cfg:
        return ""
    if _env_value(cfg.liff_env):
        return cfg.liff_env
    if _env_value(cfg.provider_liff_env):
        return cfg.provider_liff_env
    return ""


def webhook_path(channel_key: Optional[str]) -> str:
    """POST path serving one OA's webhook; unknown non-empty key → "" (no route, so 404)."""
    key = resolve(channel_key)
    if key is None:
        return ""
    if key == DEFAULT_DMS_CHANNEL:
        return _WEBHOOK_BASE
    return f"{_WEBHOOK_BASE}/{key[4:] if key.startswith('dms_') else key}"


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
        ("channel_secret", "channelSecret", "secret", secret_env, "LINE_CHANNEL_SECRET"),
    )
    token = token or _pick(
        blob,
        (
            "channel_access_token",
            "channelAccessToken",
            "access_token",
            "token",
            token_env,
            "LINE_CHANNEL_ACCESS_TOKEN",
        ),
    )
    return secret, token
