"""LINE Login OAuth 2.0 and Cowork LINE identity connection.

The shared LINE Login flow only authenticates a Pearnly account. Cowork identity
connection is an explicit, one-time flow carried in a separate OAuth state and
does not write the legacy ``line_bindings`` store.

OAuth state(HMAC 无状态签名)与 Google 登录共用 → services/auth/oauth_state.py。
"""

from __future__ import annotations

import json
import logging
import os
import secrets as _secrets
from urllib.parse import urlencode as _urlencode

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse as _RedirectResp

from core import db
from core.auth import create_access_token
from services.auth.entrance import login_entrance_allowed as _login_entrance_allowed
from services.auth.oauth_state import gen_oauth_state as _gen_oauth_state
from services.auth.oauth_state import login_redirect_path as _login_redirect_path
from services.auth.oauth_state import oauth_entry_context as _oauth_entry_context
from services.auth.oauth_state import oauth_state_entry as _oauth_state_entry
from services.auth.oauth_state import verify_oauth_state as _verify_oauth_state
from services.cowork_line import identity_store

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================
# v118.28.4 · LINE Login OAuth 2.0
# 一键登录 / 一键注册 · 跟 Google 同套机制
# email scope 需 LINE 单独审批 · 没拿到时占位 username
# ============================================================
_LINE_LOGIN_CHANNEL_ID = os.getenv("LINE_LOGIN_CHANNEL_ID", "")
_LINE_LOGIN_CHANNEL_SECRET = os.getenv("LINE_LOGIN_CHANNEL_SECRET", "")
_LINE_LOGIN_REDIRECT_URI = os.getenv(
    "LINE_LOGIN_REDIRECT_URI", "https://pearnly.com/api/auth/line/callback"
)
_COWORK_CONNECT_STATE_PREFIX = "cowork_line:"


@router.get("/api/auth/line/start")
async def line_oauth_start(entry: str = "", connect_token: str = ""):
    if not _LINE_LOGIN_CHANNEL_ID:
        raise HTTPException(status_code=503, detail="line_oauth_not_configured")
    entry_context = _oauth_entry_context(entry)
    if connect_token:
        if entry_context != "cowork" or not connect_token.startswith("clc_"):
            raise HTTPException(status_code=400, detail="cowork_line.invalid_connect_token")
        state = f"{_COWORK_CONNECT_STATE_PREFIX}{connect_token}"
    else:
        state = _gen_oauth_state(entry_context or None)
    params = {
        "response_type": "code",
        "client_id": _LINE_LOGIN_CHANNEL_ID,
        "redirect_uri": _LINE_LOGIN_REDIRECT_URI,
        "state": state,
        "scope": "openid profile email",  # v118.28.4.2 · email scope 已通过 · 自动拿邮箱
        "nonce": _secrets.token_urlsafe(16),
    }
    url = "https://access.line.me/oauth2/v2.1/authorize?" + _urlencode(params)
    return _RedirectResp(url, status_code=302)


def _cowork_connect_token(state: str) -> str:
    if not state.startswith(_COWORK_CONNECT_STATE_PREFIX):
        return ""
    token = state[len(_COWORK_CONNECT_STATE_PREFIX) :]
    return token if token.startswith("clc_") else ""


def _cowork_connect_redirect(status: str) -> _RedirectResp:
    return _RedirectResp(f"/cowork?cowork_line_connect={status}#/integrations", status_code=302)


def _finish_cowork_connect(connect_token: str, payload: dict) -> _RedirectResp:
    line_user_id = (payload.get("sub") or "").strip()
    if not line_user_id:
        return _cowork_connect_redirect("error")

    try:
        membership = identity_store.consume_connect_token(connect_token)
        if not membership:
            return _cowork_connect_redirect("expired")
        result = identity_store.bind_identity(
            membership_id=str(membership["membership_id"]),
            tenant_id=str(membership["tenant_id"]),
            user_id=str(membership["user_id"]),
            line_user_id=line_user_id,
            display_name=(payload.get("name") or "").strip() or None,
            picture_url=(payload.get("picture") or "").strip() or None,
        )
        if not result.get("success"):
            status = "conflict" if result.get("conflict") else "error"
            return _cowork_connect_redirect(status)
    except identity_store.CoworkLineIdentityError as exc:
        code = exc.code.removeprefix("cowork_line.")
        if code in {"already_connected", "line_conflict"}:
            return _cowork_connect_redirect("conflict")
        if code in {"membership_inactive", "token_expired", "token_invalid", "token_used"}:
            return _cowork_connect_redirect("expired")
        logger.warning("[cowork_line_connect] rejected: %s", code)
        return _cowork_connect_redirect("error")
    except Exception:
        logger.exception("[cowork_line_connect] failed")
        return _cowork_connect_redirect("error")
    return _cowork_connect_redirect("ok")


@router.get("/api/auth/line/callback")
async def line_oauth_callback(code: str = "", state: str = "", error: str = ""):
    connect_token = _cowork_connect_token(state)
    if error:
        if connect_token:
            return _cowork_connect_redirect("error")
        return _RedirectResp(f"/login?oauth_error={error}", status_code=302)
    if not connect_token and not _verify_oauth_state(state):
        return _RedirectResp("/login?oauth_error=invalid_state", status_code=302)
    _entry_ctx = "cowork" if connect_token else _oauth_state_entry(state)
    if not code:
        if connect_token:
            return _cowork_connect_redirect("error")
        return _RedirectResp("/login?oauth_error=no_code", status_code=302)
    if not _LINE_LOGIN_CHANNEL_ID or not _LINE_LOGIN_CHANNEL_SECRET:
        if connect_token:
            return _cowork_connect_redirect("error")
        return _RedirectResp("/login?oauth_error=line_not_configured", status_code=302)

    # code → access_token + id_token
    try:
        import httpx as _httpx

        async with _httpx.AsyncClient(timeout=15) as client:
            tr = await client.post(
                "https://api.line.me/oauth2/v2.1/token",
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": _LINE_LOGIN_REDIRECT_URI,
                    "client_id": _LINE_LOGIN_CHANNEL_ID,
                    "client_secret": _LINE_LOGIN_CHANNEL_SECRET,
                },
            )
            if tr.status_code != 200:
                logger.error(
                    f"[LINE OAuth] token exchange failed {tr.status_code}: {tr.text[:300]}"
                )
                if connect_token:
                    return _cowork_connect_redirect("error")
                return _RedirectResp("/login?oauth_error=line_token_fail", status_code=302)
            tok_data = tr.json()
            id_token = tok_data.get("id_token")
            if not id_token:
                if connect_token:
                    return _cowork_connect_redirect("error")
                return _RedirectResp("/login?oauth_error=line_no_id_token", status_code=302)

            # 用 LINE 的 verify 端点 · 服务端验证 id_token + 拿 payload
            vr = await client.post(
                "https://api.line.me/oauth2/v2.1/verify",
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                data={
                    "id_token": id_token,
                    "client_id": _LINE_LOGIN_CHANNEL_ID,
                },
            )
            if vr.status_code != 200:
                logger.error(
                    f"[LINE OAuth] id_token verify failed {vr.status_code}: {vr.text[:300]}"
                )
                if connect_token:
                    return _cowork_connect_redirect("error")
                return _RedirectResp("/login?oauth_error=line_verify_fail", status_code=302)
            payload = vr.json()
    except Exception as e:
        logger.error(f"[LINE OAuth] callback fetch failed: {e}")
        if connect_token:
            return _cowork_connect_redirect("error")
        return _RedirectResp("/login?oauth_error=line_fetch_fail", status_code=302)

    if connect_token:
        return _finish_cowork_connect(connect_token, payload)

    line_uid = payload.get("sub")
    line_name = (payload.get("name") or "").strip()
    line_picture = (payload.get("picture") or "").strip()
    line_email = (payload.get("email") or "").strip().lower()  # email scope 没批通常没这个
    if not line_uid:
        return _RedirectResp("/login?oauth_error=line_no_sub", status_code=302)

    # 1) 用 line_uid 找
    user = db.find_user_by_line_uid(line_uid)
    if not user:
        # 2) 如果有 email · 用 email 找现有账号 · 自动绑 line_uid(老用户首次用 LINE 登录)
        if line_email:
            existing = db.find_user_by_username(line_email)
            if existing:
                db.link_line_uid_to_user(str(existing["id"]), line_uid)
                user = db.find_user_by_username(line_email)
        if not user:
            # 3) 全新用户 · LINE 一键注册
            try:
                from services.auth.oauth_create import create_user_via_line_oauth

                user = create_user_via_line_oauth(
                    line_uid=line_uid,
                    display_name=line_name or None,
                    email=line_email or None,
                    picture=line_picture or None,
                    ip=None,
                    ua=None,
                    entry=_entry_ctx,
                )
            except Exception as e:
                logger.error(f"[LINE OAuth] one-click signup failed: {e}")
                user = None
            if not user:
                return _RedirectResp("/login?oauth_error=line_signup_failed", status_code=302)

    if not _login_entrance_allowed(_entry_ctx or "main", user):
        error_path = "/cowork" if _entry_ctx == "cowork" else "/login"
        return _RedirectResp(f"{error_path}?oauth_error=invalid_credentials", status_code=302)

    # 颁 JWT
    db.update_last_login(str(user["id"]))
    if line_picture:
        try:
            db.update_user_avatar(str(user["id"]), line_picture)
        except Exception as e:
            logger.warning(f"[line_login] 同步用户头像失败: {e}")
    _safe_plan = user.get("plan") or "free"
    token = create_access_token(
        user_id=str(user["id"]),
        username=user["username"],
        plan=_safe_plan,
        tenant_id=str(user["tenant_id"]) if user.get("tenant_id") else None,
        role=user.get("role") or "owner",
        is_super_admin=bool(user.get("is_super_admin")),
        remember_me=True,
        entry=_entry_ctx or "main",
    )

    safe_token = json.dumps(token)
    # v118.28.2 · 超管 → /admin · 普通用户 → /home · POS PO-B1 · cashier → /pos
    _redirect_path = _login_redirect_path(user, entry=_entry_ctx)
    return HTMLResponse(f"""<!doctype html>
<html><head><meta charset="utf-8"><title>Pearnly · Signing in...</title></head>
<body style="font-family:-apple-system,sans-serif;background:#0a0e27;color:#fff;display:flex;align-items:center;justify-content:center;height:100vh;margin:0">
<div>Signing you in...</div>
<script>
try {{ localStorage.setItem("mrpilot_token", {safe_token}); }} catch(e) {{}}
window.location.replace("{_redirect_path}");
</script>
</body></html>""")
