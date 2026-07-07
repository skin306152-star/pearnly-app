# -*- coding: utf-8 -*-
"""集成中心 · Google Drive/Sheets 授权路由(独立外流 OAuth · 契约 05 §2.1)。

status/connect/disconnect 走 auth_member(成员·按当前套账);callback 公开(state 即凭证,
encode tenant/ws/user · 进 PUBLIC_ROUTES)。凭据按套账存(google_store)· 绝不跨套账串。
未配产品 OAuth client(env)→ status 返 configured=false,connect 返友好提示不 500。
"""

from __future__ import annotations

import secrets
from typing import Optional

from fastapi import APIRouter, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from core import db
from core.pos_api import PosError, ok
from routes.purchase_common import auth_member, resolve_ws, uid as _uid
from services.export import google_oauth, google_store

router = APIRouter(prefix="/api/integrations/google", tags=["integrations-google"])
_LAUNCH_PREFIX = "launch:"


def _redirect_uri(request: Request) -> str:
    """callback 地址:env 优先(prod 必须与 OAuth client 注册一致),否则按请求基址推。"""
    return google_oauth.redirect_uri(
        default=str(request.base_url).rstrip("/") + "/api/integrations/google/callback"
    )


def _launch_state(ticket: str) -> str:
    return _LAUNCH_PREFIX + ticket


def _connect_launch_url(ticket: str) -> str:
    return f"/api/integrations/google/connect?launch={ticket}"


@router.get("/status")
async def api_status(request: Request, workspace_client_id: Optional[int] = Query(None)):
    _, tid = auth_member(request, "purchase.doc.view")
    with db.get_cursor_rls(tid, commit=False) as cur:
        ws = resolve_ws(cur, request, tid, workspace_client_id)
        cred = google_store.get_credential(cur, tenant_id=tid, workspace_client_id=ws)
    return ok(
        {
            "configured": google_oauth.is_configured(),
            "connected": bool(cred),
            "email": (cred or {}).get("google_email") or "",
            "scope": (cred or {}).get("scope") or "",
        }
    )


@router.post("/connect/start")
async def api_connect_start(request: Request, workspace_client_id: Optional[int] = Query(None)):
    user, tid = auth_member(request, "purchase.doc.approve")
    if not google_oauth.is_configured():
        raise PosError("purchase.unexpected", 503, detail="google_oauth_not_configured")
    ticket = secrets.token_urlsafe(24)
    with db.get_cursor_rls(tid, commit=True) as cur:
        ws = resolve_ws(cur, request, tid, workspace_client_id)
        google_store.save_state(
            cur,
            state=_launch_state(ticket),
            tenant_id=tid,
            workspace_client_id=ws,
            user_id=_uid(user),
        )
    return ok({"url": _connect_launch_url(ticket)})


@router.get("/connect")
async def api_connect(
    request: Request,
    workspace_client_id: Optional[int] = Query(None),
    launch: Optional[str] = Query(None),
):
    state = secrets.token_urlsafe(24)

    if launch:
        with db.get_cursor(commit=True) as cur:
            owner = google_store.consume_state(cur, state=_launch_state(launch))
        if not owner:
            raise PosError("purchase.forbidden", 403, detail="google_oauth_launch_expired")
        tid = owner["tenant_id"]
        ws = owner["workspace_client_id"]
        user_id = owner["user_id"]
    else:
        user, tid = auth_member(request, "purchase.doc.approve")
        with db.get_cursor_rls(tid, commit=False) as cur:
            ws = resolve_ws(cur, request, tid, workspace_client_id)
        user_id = _uid(user)

    if not google_oauth.is_configured():
        raise PosError("purchase.unexpected", 503, detail="google_oauth_not_configured")
    with db.get_cursor(commit=True) as cur:
        google_store.save_state(
            cur, state=state, tenant_id=tid, workspace_client_id=ws, user_id=user_id
        )
    url = google_oauth.build_authorize_url(state=state, redirect=_redirect_uri(request))
    resp = RedirectResponse(url, status_code=302)
    resp.headers["Cache-Control"] = "no-store"
    resp.headers["Referrer-Policy"] = "no-referrer"
    return resp


@router.get("/callback")
async def api_callback(
    request: Request, code: Optional[str] = Query(None), state: Optional[str] = Query(None)
):
    """Google 重定向回调(公开·state 即凭证)。换码存凭据 → 回采购导出页(连接入口所在)。"""
    if not code or not state:
        return HTMLResponse("<p>授权失败:缺少参数,请重试。</p>", status_code=400)
    with db.get_cursor(commit=True) as cur:
        owner = google_store.consume_state(cur, state=state)
    if not owner:
        return HTMLResponse("<p>授权已过期,请重新发起连接。</p>", status_code=400)
    try:
        tok = google_oauth.exchange_code(code=code, redirect=_redirect_uri(request))
    except Exception:  # noqa: BLE001
        return HTMLResponse("<p>授权失败:换取令牌出错,请重试。</p>", status_code=502)
    with db.get_cursor(commit=True) as cur:
        google_store.upsert_credential(
            cur,
            tenant_id=owner["tenant_id"],
            workspace_client_id=owner["workspace_client_id"],
            google_email=tok["email"],
            access_token=tok["access_token"],
            refresh_token=tok["refresh_token"],
            expires_at=tok["expires_at"],
            scope=tok["scope"],
            created_by=owner["user_id"],
        )
    return RedirectResponse("/home#/purchase-export", status_code=302)


@router.post("/disconnect")
async def api_disconnect(request: Request, workspace_client_id: Optional[int] = Query(None)):
    _, tid = auth_member(request, "purchase.doc.approve")
    with db.get_cursor_rls(tid, commit=True) as cur:
        ws = resolve_ws(cur, request, tid, workspace_client_id)
        google_store.delete_credential(cur, tenant_id=tid, workspace_client_id=ws)
    return ok({"disconnected": True})
