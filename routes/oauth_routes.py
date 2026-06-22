"""
oauth_routes.py · Google OAuth 2.0 登录(REFACTOR-B1)

从 app.py L3237-3549 抽出 · 0 业务逻辑改:
    GET /api/auth/google/start       v118.27.5 Google OAuth 一键登录入口
    GET /api/auth/google/callback    code→token→userinfo · 注册/登录 / 自动绑 google_sub

OAuth state(HMAC 无状态签名 · TTL 10 分钟 · 跨 worker 可验)与 LINE 登录共用,
抽到 services/auth/oauth_state.py;LINE 登录路由见 routes/oauth_line_routes.py。

E2E 闸:spec 01(普通邮箱登录)间接覆盖。
"""

from __future__ import annotations

import json
import logging
import os
from urllib.parse import urlencode as _urlencode

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse as _RedirectResp

from core import db
from core.auth import create_access_token
from services.auth.oauth_state import gen_oauth_state as _gen_oauth_state
from services.auth.oauth_state import login_redirect_path as _login_redirect_path
from services.auth.oauth_state import oauth_state_secret as _oauth_state_secret  # noqa: F401
from services.auth.oauth_state import verify_oauth_state as _verify_oauth_state

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


# ============================================================
# in-app webview 突围 · Google OAuth 在 LINE 内置浏览器被 disallowed_useragent(403)拦死。
# LINE 识别 openExternalBrowser=1 → 自动用系统浏览器(Safari/Chrome)重新打开当前入口,
# 在系统浏览器里 Google 登录才合规。ext=1 守卫:外开后 UA 不再含 Line/ 且带 ext → 不二次突围。
# 仅针对 Google;LINE Login 在 LINE 内置浏览器本就合规,无需突围。
# ============================================================
# base url 取值对齐同范式(line_proof._base_url / pos_auth._pos_base_url):用 `or` 而非
# getenv 默认值,这样 PEARNLY_BASE_URL 设为空串时仍回落到 pearnly.com(不致空 base)。
_PEARNLY_BASE = (os.getenv("PEARNLY_BASE_URL") or "https://pearnly.com").rstrip("/")


def _is_line_inapp(ua: str) -> bool:
    return "Line/" in (ua or "")


# 突围页内容在 import 时即完全确定(base + 固定入口)→ 预构建一次,冷登录路径不重复渲染。
_BREAKOUT_URL = json.dumps(f"{_PEARNLY_BASE}/api/auth/google/start?ext=1&openExternalBrowser=1")
_BREAKOUT_HTML = f"""<!doctype html>
<html lang="th"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Pearnly</title></head>
<body style="font-family:-apple-system,sans-serif;background:#0a0e27;color:#fff;display:flex;align-items:center;justify-content:center;height:100vh;margin:0;text-align:center;padding:24px">
<div>
<p>กำลังเปิดเบราว์เซอร์เพื่อเข้าสู่ระบบด้วย Google…</p>
<p style="opacity:.7;font-size:14px">Opening your browser to sign in with Google…</p>
<p style="margin-top:20px"><a href={_BREAKOUT_URL} style="color:#7aa2ff">แตะที่นี่ถ้าไม่เปิดอัตโนมัติ / Tap here</a></p>
</div>
<script>location.replace({_BREAKOUT_URL});</script>
</body></html>"""


def _external_browser_breakout() -> HTMLResponse:
    return HTMLResponse(_BREAKOUT_HTML)


@router.get("/api/auth/google/start")
async def google_oauth_start(request: Request, ext: int = 0):
    if not _GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=503, detail="oauth_not_configured")
    # LINE 内置浏览器里直接跳 Google 会 403(disallowed_useragent)→ 先弹到系统浏览器再登录。
    if not ext and _is_line_inapp(request.headers.get("user-agent", "")):
        return _external_browser_breakout()
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
    # POS PO-B1 · role=cashier → /pos(收银员只进收银前台)
    safe_token = json.dumps(token)
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
