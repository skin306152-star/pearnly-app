# -*- coding: utf-8 -*-
"""替代收据 PDF 访问 token(HMAC 签名 · LINE 外部浏览器无会话 → 自带鉴权)。

token 内嵌 tenant/ws/draft/exp,HMAC(JWT_SECRET) 防篡改;路由验签 + 未过期即放行,
不需 DB 查权限。由 confirm 回执时签发。纯逻辑叶子(可单测)。
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
from typing import Optional

TTL_SECONDS = 7 * 24 * 3600  # 凭证链接 7 天有效


def _secret() -> bytes:
    return (os.environ.get("JWT_SECRET", "") or "pearnly-dev-secret").encode("utf-8")


def sign(*, draft_id: str, tenant_id: str, ws: int, now_ts: int) -> str:
    payload = {"d": draft_id, "t": tenant_id, "w": int(ws), "e": int(now_ts) + TTL_SECONDS}
    raw = base64.urlsafe_b64encode(json.dumps(payload).encode("utf-8")).decode("ascii").rstrip("=")
    sig = hmac.new(_secret(), raw.encode("ascii"), hashlib.sha256).hexdigest()[:32]
    return f"{raw}.{sig}"


def verify(token: str, now_ts: int) -> Optional[dict]:
    """验签 + 未过期 → payload;否则 None。"""
    try:
        raw, sig = (token or "").split(".", 1)
    except ValueError:
        return None
    expect = hmac.new(_secret(), raw.encode("ascii"), hashlib.sha256).hexdigest()[:32]
    if not hmac.compare_digest(sig, expect):
        return None
    try:
        pad = "=" * (-len(raw) % 4)
        payload = json.loads(base64.urlsafe_b64decode(raw + pad))
    except Exception:
        return None
    if int(payload.get("e", 0)) < now_ts:
        return None
    return payload
