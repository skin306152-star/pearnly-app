"""OAuth state 签名 · Google + LINE 登录共用(REFACTOR-B1 拆分自 oauth_routes)。

HMAC 无状态签名 · TTL 10 分钟 · 跨 worker 可验:state=nonce.ts.sig,用 JWT_SECRET 签,
任一 worker 都能验、无服务端存储 → workers>1 天然兼容。原存进程内存在 workers=4 时回调
命中别的 worker 会 invalid_state 登不上(2026-06-12 改 HMAC 根治)。
"""

from __future__ import annotations

import hashlib
import hmac
import os
import secrets as _secrets
import time as _time

_OAUTH_STATE_TTL = 600


def oauth_state_secret() -> bytes:
    return (os.environ.get("JWT_SECRET", "") or "pearnly-oauth-fallback").encode("utf-8")


def gen_oauth_state() -> str:
    payload = f"{_secrets.token_urlsafe(16)}.{int(_time.time())}"
    sig = hmac.new(oauth_state_secret(), payload.encode("utf-8"), hashlib.sha256).hexdigest()[:32]
    return f"{payload}.{sig}"


def verify_oauth_state(s: str) -> bool:
    parts = (s or "").split(".")
    if len(parts) != 3:
        return False
    nonce, ts, sig = parts
    expected = hmac.new(
        oauth_state_secret(), f"{nonce}.{ts}".encode("utf-8"), hashlib.sha256
    ).hexdigest()[:32]
    if not hmac.compare_digest(sig, expected):
        return False
    try:
        return _time.time() - int(ts) < _OAUTH_STATE_TTL
    except ValueError:
        return False


def login_redirect_path(user: dict) -> str:
    """登录落地分流:超管→/admin · 收银员→/pos · 其余→/home(POS PO-B1)。"""
    if bool(user.get("is_super_admin")):
        return "/admin"
    if (user.get("role") or "owner") == "cashier":
        return "/pos"
    return "/home"
