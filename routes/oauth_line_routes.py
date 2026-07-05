"""oauth_line_routes.py · LINE Login OAuth 2.0 登录 + 「用 LINE 连接」补绑(REFACTOR-B1)

从 oauth_routes.py 抽出(0 业务逻辑改 · 仅拆文件到 <500):
    GET /api/me/connect-line/start   已登录用户一键连接 LINE(state 签入 user_id)
    GET /api/auth/line/start         v118.28.4 LINE Login OAuth 入口
    GET /api/auth/line/callback      code→id_token→verify · 注册/登录 / 自动绑 line_uid / 补绑分流

OAuth state(HMAC 无状态签名)与 Google 登录共用 → services/auth/oauth_state.py。
E2E 闸:spec 14(LINE 绑定)间接覆盖。
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import secrets as _secrets
import time as _time
from urllib.parse import urlencode as _urlencode

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse as _RedirectResp

from core import db
from core.auth import create_access_token, get_current_user_from_request
from services.auth.oauth_state import _OAUTH_STATE_TTL
from services.auth.oauth_state import gen_oauth_state as _gen_oauth_state
from services.auth.oauth_state import login_redirect_path as _login_redirect_path
from services.auth.oauth_state import oauth_state_secret as _oauth_state_secret
from services.auth.oauth_state import verify_oauth_state as _verify_oauth_state

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


# ── 「用 LINE 连接」(已登录用户补绑 LINE)· state 签入 user_id,复用登录 callback,按 state 分流 ──
def _gen_connect_state(user_id: str) -> str:
    payload = f"{user_id}~{_secrets.token_urlsafe(8)}~{int(_time.time())}"
    sig = hmac.new(_oauth_state_secret(), payload.encode("utf-8"), hashlib.sha256).hexdigest()[:32]
    return f"{payload}~{sig}"


def _parse_connect_state(s: str):
    """连接态 state → user_id;非连接态/无效/过期 → None。"""
    parts = (s or "").split("~")
    if len(parts) != 4:
        return None
    uid, nonce, ts, sig = parts
    expected = hmac.new(
        _oauth_state_secret(), f"{uid}~{nonce}~{ts}".encode("utf-8"), hashlib.sha256
    ).hexdigest()[:32]
    if not hmac.compare_digest(sig, expected):
        return None
    try:
        if _time.time() - int(ts) >= _OAUTH_STATE_TTL:
            return None
    except ValueError:
        return None
    return uid


@router.get("/api/me/connect-line/start")
async def connect_line_start(request: Request):
    """已登录用户(如 Google 登录)一键连接 LINE:返回授权 URL,前端跳转。state 签入当前 user_id。"""
    user = get_current_user_from_request(request)
    if not _LINE_LOGIN_CHANNEL_ID:
        raise HTTPException(status_code=503, detail="line_oauth_not_configured")
    params = {
        "response_type": "code",
        "client_id": _LINE_LOGIN_CHANNEL_ID,
        "redirect_uri": _LINE_LOGIN_REDIRECT_URI,  # 复用已注册的登录 callback
        "state": _gen_connect_state(str(user["id"])),
        "scope": "openid profile",
        "nonce": _secrets.token_urlsafe(16),
        "bot_prompt": "aggressive",  # 顺带提示加好友
    }
    return {"url": "https://access.line.me/oauth2/v2.1/authorize?" + _urlencode(params)}


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
        # 登录页提示加 Pearnly Bot 为好友(登录频道已关联 OA·与 Bot 同 provider)。
        "bot_prompt": "aggressive",
    }
    url = "https://access.line.me/oauth2/v2.1/authorize?" + _urlencode(params)
    return _RedirectResp(url, status_code=302)


async def _handle_connect_line(user_id: str, code: str):
    """已登录用户补绑 LINE:换 code 拿 sub → 绑当前账号 + 绑 Bot + 推欢迎卡 → 回集成页。"""
    if not code or not _LINE_LOGIN_CHANNEL_ID or not _LINE_LOGIN_CHANNEL_SECRET:
        return _RedirectResp("/home?line_connect=error#integrations", status_code=302)
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
                return _RedirectResp("/home?line_connect=error#integrations", status_code=302)
            id_token = tr.json().get("id_token")
            vr = await client.post(
                "https://api.line.me/oauth2/v2.1/verify",
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                data={"id_token": id_token, "client_id": _LINE_LOGIN_CHANNEL_ID},
            )
            if vr.status_code != 200:
                return _RedirectResp("/home?line_connect=error#integrations", status_code=302)
            payload = vr.json()
    except Exception as e:
        logger.error(f"[line_connect] fetch failed: {e}")
        return _RedirectResp("/home?line_connect=error#integrations", status_code=302)

    sub = payload.get("sub")
    user = db.find_user_by_id(user_id)
    if not sub or not user:
        return _RedirectResp("/home?line_connect=error#integrations", status_code=302)
    try:
        db.link_line_uid_to_user(user_id, sub)
        ok = db.create_or_update_line_binding(
            user_id=user_id,
            line_user_id=sub,
            display_name=(payload.get("name") or None),
            picture_url=(payload.get("picture") or None),
        )
        if not ok:
            # 该 LINE 已绑别的 Pearnly 账号 → 诚实提示,不假装成功。
            return _RedirectResp("/home?line_connect=conflict#integrations", status_code=302)
        from services.line_binding import line_imagemap, line_reply

        line_reply.push_messages_context(
            sub,
            line_imagemap.welcome_messages(user.get("preferred_lang")),
            tenant_id=str(user["tenant_id"]) if user.get("tenant_id") else None,
        )
    except Exception as e:
        logger.warning(f"[line_connect] 绑定/推送失败: {e}")
        return _RedirectResp("/home?line_connect=error#integrations", status_code=302)
    return _RedirectResp("/home?line_connect=ok#integrations", status_code=302)


@router.get("/api/auth/line/callback")
async def line_oauth_callback(code: str = "", state: str = "", error: str = ""):
    if error:
        return _RedirectResp(f"/login?oauth_error={error}", status_code=302)
    # 「用 LINE 连接」分流:state 签入了 user_id → 补绑当前账号(不走登录建号),回集成页。
    _connect_uid = _parse_connect_state(state)
    if _connect_uid:
        return await _handle_connect_line(_connect_uid, code)
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

    # 登录即自动绑定 Bot:登录频道(2010411313)与 Messaging Bot 同一 Provider「Pearnly」→
    # 登录拿到的 sub == Bot 看到的 userId → 直接写 line_bindings,免手输 6 位码。
    # best-effort:已绑/冲突/失败都不拦登录。已是好友则 push 欢迎卡+新手轮播(=登录后 LINE 自动弹卡);
    # 非好友 push 静默失败(用户加好友后发任意消息仍已连上)。
    try:
        db.create_or_update_line_binding(
            user_id=str(user["id"]),
            line_user_id=line_uid,
            display_name=line_name or None,
            picture_url=line_picture or None,
        )
        from services.line_binding import line_imagemap, line_reply

        line_reply.push_messages_context(
            line_uid,
            line_imagemap.welcome_messages(user.get("preferred_lang")),
            tenant_id=str(user["tenant_id"]) if user.get("tenant_id") else None,
        )
    except Exception as e:
        logger.warning(f"[line_login] 自动绑定 Bot 跳过(不拦登录): {e}")

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
    # v118.28.2 · 超管 → /admin · 普通用户 → /home · POS PO-B1 · cashier → /pos
    _redirect_path = _login_redirect_path(user)
    return HTMLResponse(f"""<!doctype html>
<html><head><meta charset="utf-8"><title>Pearnly · Signing in...</title></head>
<body style="font-family:-apple-system,sans-serif;background:#0a0e27;color:#fff;display:flex;align-items:center;justify-content:center;height:100vh;margin:0">
<div>Signing you in...</div>
<script>
try {{ localStorage.setItem("mrpilot_token", {safe_token}); }} catch(e) {{}}
window.location.replace("{_redirect_path}");
</script>
</body></html>""")
