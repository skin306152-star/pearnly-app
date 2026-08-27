"""OAuth state 签名 · Google + LINE 登录共用(REFACTOR-B1 拆分自 oauth_routes)。

HMAC 无状态签名 · TTL 10 分钟 · 跨 worker 可验。兼容旧 nonce.ts.sig，并支持把
Cowork 入口签入 nonce.ts.entry.sig，供 OAuth 回调安全恢复注册产品上下文。
"""

from __future__ import annotations

import hashlib
import hmac
import os
import secrets as _secrets
import time as _time

_OAUTH_STATE_TTL = 600

# 共享 OAuth 登录只服务会计主站与 Cowork。ERP 是邀请制独立登录门，不能由查询参数签发。
_OAUTH_ENTRANCES = frozenset({"main", "cowork"})


def oauth_entry_context(entry: str) -> str:
    """只接受共享 OAuth 实际支持的入口。"""
    e = (entry or "").strip().lower()
    return e if e in _OAUTH_ENTRANCES else ""


def oauth_state_secret() -> bytes:
    return (os.environ.get("JWT_SECRET", "") or "pearnly-oauth-fallback").encode("utf-8")


def _split_state(s: str):
    """验签并解析新旧两种 state；非法或过期返回 None。"""
    parts = (s or "").split(".")
    if len(parts) not in (3, 4):
        return None
    sig = parts[-1]
    body = ".".join(parts[:-1])
    expected = hmac.new(oauth_state_secret(), body.encode("utf-8"), hashlib.sha256).hexdigest()[:32]
    if not hmac.compare_digest(sig, expected):
        return None
    body_parts = parts[:-1]
    nonce = body_parts[0]
    ts = body_parts[1]
    entry = body_parts[2] if len(body_parts) == 3 else None
    if entry is not None and entry not in _OAUTH_ENTRANCES:
        return None
    try:
        if _time.time() - int(ts) >= _OAUTH_STATE_TTL:
            return None
    except ValueError:
        return None
    return nonce, ts, entry


def gen_oauth_state(entry: str = None) -> str:
    """生成签名 state；未知入口按旧的无上下文格式处理。"""
    payload = f"{_secrets.token_urlsafe(16)}.{int(_time.time())}"
    safe_entry = oauth_entry_context(entry)
    if safe_entry:
        payload = f"{payload}.{safe_entry}"
    sig = hmac.new(oauth_state_secret(), payload.encode("utf-8"), hashlib.sha256).hexdigest()[:32]
    return f"{payload}.{sig}"


def verify_oauth_state(s: str) -> bool:
    return _split_state(s) is not None


def oauth_state_entry(s: str) -> str | None:
    """读取已验签入口；旧格式、非法或过期均返回 None。"""
    parsed = _split_state(s)
    return parsed[2] if parsed else None


def login_redirect_path(user: dict, entry: str = None) -> str:
    """登录落地分流，并让 Cowork OAuth 回到自己的会话槽。"""
    if bool(user.get("is_super_admin")):
        return "/admin"
    if (user.get("role") or "owner") == "cashier":
        return "/cashier"
    if entry == "cowork":
        return "/home?canonical=cowork"
    return "/home"
