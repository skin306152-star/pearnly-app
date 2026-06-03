"""
oauth_routes.py · Google + LINE OAuth 2.0 登录(REFACTOR-B1)

从 app.py L3237-3549 抽出 · 0 业务逻辑改:
    GET /api/auth/google/start       v118.27.5 Google OAuth 一键登录入口
    GET /api/auth/google/callback    code→token→userinfo · 注册/登录 / 自动绑 google_sub
    GET /api/auth/line/start         v118.28.4 LINE Login OAuth 入口
    GET /api/auth/line/callback      code→id_token→verify · 注册/登录 / 自动绑 line_uid

共用模块状态(进程内 OAuth state TTL 10 分钟):
    - _oauth_state_cache: Dict[str, float]
    - _gen_oauth_state() / _verify_oauth_state(s)

E2E 闸:spec 01(普通邮箱登录)+ spec 14(LINE 绑定)间接覆盖。
"""

from __future__ import annotations

import json
import logging
import os
import secrets as _secrets
import time as _time
from typing import Dict
from urllib.parse import urlencode as _urlencode

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse as _RedirectResp

from core import db
from core.auth import create_access_token

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================
# v118.27.5 · Google OAuth 2.0 · 仅支持已注册账号登录(自动绑定 google_sub)
# 未注册用户:跳回 /login 提示先邮箱注册(自动建账号留 v118.27.6)
# ============================================================
_GOOGLE_CLIENT_ID = os.getenv("GOOGLE_OAUTH_CLIENT_ID", "")
_GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET", "")
_GOOGLE_REDIRECT_URI = os.getenv(
    "GOOGLE_OAUTH_REDIRECT_URI", "https://pearnly.com/api/auth/google/callback"
)
_oauth_state_cache: Dict[str, float] = {}


def _gen_oauth_state() -> str:
    s = _secrets.token_urlsafe(32)
    _oauth_state_cache[s] = _time.time()
    cutoff = _time.time() - 600
    for k in list(_oauth_state_cache.keys()):
        if _oauth_state_cache[k] < cutoff:
            _oauth_state_cache.pop(k, None)
    return s


def _verify_oauth_state(s: str) -> bool:
    if not s or s not in _oauth_state_cache:
        return False
    ts = _oauth_state_cache.pop(s)
    return _time.time() - ts < 600


@router.get("/api/auth/google/start")
async def google_oauth_start():
    if not _GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=503, detail="oauth_not_configured")
    state = _gen_oauth_state()
    params = {
        "client_id": _GOOGLE_CLIENT_ID,
        "redirect_uri": _GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "access_type": "online",
        "prompt": "select_account",
    }
    url = "https://accounts.google.com/o/oauth2/v2/auth?" + _urlencode(params)
    return _RedirectResp(url, status_code=302)


@router.get("/api/auth/google/callback")
async def google_oauth_callback(code: str = "", state: str = "", error: str = ""):
    if error:
        return _RedirectResp(f"/login?oauth_error={error}", status_code=302)
    if not _verify_oauth_state(state):
        return _RedirectResp("/login?oauth_error=invalid_state", status_code=302)
    if not code:
        return _RedirectResp("/login?oauth_error=no_code", status_code=302)
    if not _GOOGLE_CLIENT_ID or not _GOOGLE_CLIENT_SECRET:
        return _RedirectResp("/login?oauth_error=not_configured", status_code=302)

    # code → access_token → userinfo
    try:
        import httpx as _httpx

        async with _httpx.AsyncClient(timeout=15) as client:
            tr = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "code": code,
                    "client_id": _GOOGLE_CLIENT_ID,
                    "client_secret": _GOOGLE_CLIENT_SECRET,
                    "redirect_uri": _GOOGLE_REDIRECT_URI,
                    "grant_type": "authorization_code",
                },
            )
            if tr.status_code != 200:
                logger.error(f"[OAuth] token exchange failed {tr.status_code}: {tr.text[:300]}")
                return _RedirectResp("/login?oauth_error=token_fail", status_code=302)
            tok_data = tr.json()
            access_token = tok_data.get("access_token")
            if not access_token:
                return _RedirectResp("/login?oauth_error=no_access_token", status_code=302)
            ur = await client.get(
                "https://openidconnect.googleapis.com/v1/userinfo",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            if ur.status_code != 200:
                return _RedirectResp("/login?oauth_error=userinfo_fail", status_code=302)
            uinfo = ur.json()
    except Exception as e:
        logger.error(f"[OAuth] callback fetch failed: {e}")
        return _RedirectResp("/login?oauth_error=fetch_fail", status_code=302)

    sub = uinfo.get("sub")
    email = (uinfo.get("email") or "").lower().strip()
    picture = (uinfo.get("picture") or "").strip()  # v118.27.5.3 · Google 头像 URL
    if not sub or not email:
        return _RedirectResp("/login?oauth_error=invalid_userinfo", status_code=302)

    # 1) 用 google_sub 找
    user = db.find_user_by_google_sub(sub)
    if not user:
        # 2) 用 email/username 找现有账号 · 自动绑定 google_sub(老用户首次用 Google 登录)
        existing = db.find_user_by_username(email)
        if existing:
            db.link_google_sub_to_user(str(existing["id"]), sub)
            user = db.find_user_by_username(email)
        else:
            # 3) v118.27.5.1 · 全新用户 · Google 一键注册(主流 SaaS 标准做法)
            try:
                from services.auth.oauth_create import create_user_via_google_oauth

                _name = (uinfo.get("name") or "").strip() or None
                user = create_user_via_google_oauth(
                    email=email,
                    full_name=_name,
                    google_sub=sub,
                    ip=None,  # callback 这里取不到 client IP · 留空
                    ua=None,
                )
            except Exception as e:
                logger.error(f"[OAuth] google one-click signup failed: {e}")
                user = None
            if not user:
                return _RedirectResp("/login?oauth_error=signup_failed", status_code=302)

    # 颁 JWT(跟普通 login 走同一函数)
    db.update_last_login(str(user["id"]))
    # v118.27.5.3 · 同步 Google 头像(每次登录 refresh · 用户 Google 头像变了也跟随)
    if picture:
        try:
            db.update_user_avatar(str(user["id"]), picture)
        except Exception as e:
            logger.warning(f"[google_oauth] 同步用户头像失败: {e}")
    _safe_plan = user.get("plan") or "free"
    token = create_access_token(
        user_id=str(user["id"]),
        username=user["username"],
        plan=_safe_plan,
        tenant_id=str(user["tenant_id"]) if user.get("tenant_id") else None,
        role=user.get("role") or "owner",
        is_super_admin=bool(user.get("is_super_admin")),
        remember_me=True,
    )

    # 中间页 set localStorage 再跳 /home 或 /admin(callback 是 GET 不能直接 set)
    # v118.28.2 · 超管 → /admin · 普通用户 → /home
    safe_token = json.dumps(token)
    _redirect_path = "/admin" if bool(user.get("is_super_admin")) else "/home"
    return HTMLResponse(f"""<!doctype html>
<html><head><meta charset="utf-8"><title>Pearnly · Signing in...</title></head>
<body style="font-family:-apple-system,sans-serif;background:#0a0e27;color:#fff;display:flex;align-items:center;justify-content:center;height:100vh;margin:0">
<div>Signing you in...</div>
<script>
try {{ localStorage.setItem("mrpilot_token", {safe_token}); }} catch(e) {{}}
window.location.replace("{_redirect_path}");
</script>
</body></html>""")


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


@router.get("/api/auth/line/start")
async def line_oauth_start():
    if not _LINE_LOGIN_CHANNEL_ID:
        raise HTTPException(status_code=503, detail="line_oauth_not_configured")
    state = _gen_oauth_state()
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


@router.get("/api/auth/line/callback")
async def line_oauth_callback(code: str = "", state: str = "", error: str = ""):
    if error:
        return _RedirectResp(f"/login?oauth_error={error}", status_code=302)
    if not _verify_oauth_state(state):
        return _RedirectResp("/login?oauth_error=invalid_state", status_code=302)
    if not code:
        return _RedirectResp("/login?oauth_error=no_code", status_code=302)
    if not _LINE_LOGIN_CHANNEL_ID or not _LINE_LOGIN_CHANNEL_SECRET:
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
                return _RedirectResp("/login?oauth_error=line_token_fail", status_code=302)
            tok_data = tr.json()
            id_token = tok_data.get("id_token")
            if not id_token:
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
                return _RedirectResp("/login?oauth_error=line_verify_fail", status_code=302)
            payload = vr.json()
    except Exception as e:
        logger.error(f"[LINE OAuth] callback fetch failed: {e}")
        return _RedirectResp("/login?oauth_error=line_fetch_fail", status_code=302)

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
                )
            except Exception as e:
                logger.error(f"[LINE OAuth] one-click signup failed: {e}")
                user = None
            if not user:
                return _RedirectResp("/login?oauth_error=line_signup_failed", status_code=302)

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
    )

    safe_token = json.dumps(token)
    # v118.28.2 · 超管 → /admin · 普通用户 → /home
    _redirect_path = "/admin" if bool(user.get("is_super_admin")) else "/home"
    return HTMLResponse(f"""<!doctype html>
<html><head><meta charset="utf-8"><title>Pearnly · Signing in...</title></head>
<body style="font-family:-apple-system,sans-serif;background:#0a0e27;color:#fff;display:flex;align-items:center;justify-content:center;height:100vh;margin:0">
<div>Signing you in...</div>
<script>
try {{ localStorage.setItem("mrpilot_token", {safe_token}); }} catch(e) {{}}
window.location.replace("{_redirect_path}");
</script>
</body></html>""")
