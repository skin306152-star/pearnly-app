"""LINE LIFF ID-token verification shared by active product channels."""

from __future__ import annotations

import os
from typing import Optional

import requests

from services.line_platform.channels import PROVIDER_LIFF_ENVS

_VERIFY_ENDPOINT = "https://api.line.me/oauth2/v2.1/verify"

# Env names that may verify against the shared Provider LINE Login channel id when no LIFF id is
# configured: the Provider apps the channel registry can hand out (``PROVIDER_LIFF_ENVS``) plus
# the product envs whose deployment only ever configured ``LINE_LOGIN_CHANNEL_ID``. A DMS OA can
# only end up here by declaring its Provider LIFF in the registry; every other env name (a new
# OA's own ``LINE_*_LIFF_ID``) fails closed instead of accepting a token minted elsewhere.
_LIFF_ID_FALLBACK_ENVS = ("LINE_DMS_LIFF_ID", "LINE_COWORK_LIFF_ID")
_SHARED_LOGIN_CHANNEL_ENVS = frozenset(PROVIDER_LIFF_ENVS) | {
    *_LIFF_ID_FALLBACK_ENVS,
    "LINE_ERP_LIFF_ID",
}


def verify_id_token(id_token: str, liff_env: str) -> Optional[dict]:
    env_name = (liff_env or "").strip()
    liff_id = os.getenv(env_name, "").strip() if env_name else ""
    if not liff_id and env_name in _LIFF_ID_FALLBACK_ENVS:
        liff_id = os.getenv("LINE_LIFF_ID", "").strip()
    if liff_id:
        channel_id = liff_id.split("-")[0]
    elif env_name in _SHARED_LOGIN_CHANNEL_ENVS:
        channel_id = os.getenv("LINE_LOGIN_CHANNEL_ID", "").strip()
    else:
        # Non-legacy OA without its own LIFF id: refuse before any verify request.
        return None
    if not id_token or not channel_id:
        return None
    try:
        response = requests.post(
            _VERIFY_ENDPOINT,
            data={"id_token": id_token, "client_id": channel_id},
            timeout=15,
        )
    except requests.RequestException:
        return None
    return response.json() if response.status_code == 200 else None
