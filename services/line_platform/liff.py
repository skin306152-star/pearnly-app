"""LINE LIFF ID-token verification shared by active product channels."""

from __future__ import annotations

import os
from typing import Optional

import requests

_VERIFY_ENDPOINT = "https://api.line.me/oauth2/v2.1/verify"


def verify_id_token(id_token: str, liff_env: str) -> Optional[dict]:
    liff_id = os.getenv(liff_env, "").strip()
    if not liff_id and liff_env in {"LINE_DMS_LIFF_ID", "LINE_COWORK_LIFF_ID"}:
        liff_id = os.getenv("LINE_LIFF_ID", "").strip()
    channel_id = (
        liff_id.split("-")[0] if liff_id else os.getenv("LINE_LOGIN_CHANNEL_ID", "").strip()
    )
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
