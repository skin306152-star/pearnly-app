# -*- coding: utf-8 -*-
"""LINE LIFF 鉴权 + 复核屏入口(契约 05 §3.1)。

LIFF 在 LINE webview 内打开网页复核屏(§五),复用现有 purchase-form,不重做成 Flex。
POST /api/line/liff/auth:LIFF id_token → 验签(LINE verify)→ 查绑定 → 签 Pearnly token。
GET /liff/purchase/{doc_id}:LIFF 页入口 → 跳 /home 复核屏(前端 JS 取 token 后渲染)。
两者公开(id_token 即凭证 · 进 PUBLIC_ROUTES)。

⚠️ create_access_token 走 1 账号 1 设备 jti 轮换 → LIFF 登录会使 LIFF 成为活跃设备
(web 端 token 失效)。这是产品取舍,留用户验收确认是否需独立 LIFF 会话。
"""

from __future__ import annotations

import os
from typing import Optional

import requests
from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from core import db
from core.auth import create_access_token
from core.pos_api import PosError, ok

router = APIRouter(tags=["line-liff"])

_VERIFY_ENDPOINT = "https://api.line.me/oauth2/v2.1/verify"


def _verify_id_token(id_token: str) -> Optional[dict]:
    """LINE 验 LIFF id_token。返回 claims 或 None。

    audience = LIFF 所属 LINE Login 频道 = LINE_LIFF_ID 前缀(与网页登录频道 LINE_LOGIN_CHANNEL_ID
    分开·别用错频道否则 aud 不匹配验签必败)。无 LIFF_ID 才回退网页登录频道。
    """
    liff_id = os.getenv("LINE_LIFF_ID", "").strip()
    channel_id = (
        liff_id.split("-")[0] if liff_id else os.getenv("LINE_LOGIN_CHANNEL_ID", "").strip()
    )
    if not id_token or not channel_id:
        return None
    try:
        resp = requests.post(
            _VERIFY_ENDPOINT,
            data={"id_token": id_token, "client_id": channel_id},
            timeout=15,
        )
        if resp.status_code != 200:
            return None
        return resp.json()
    except requests.RequestException:
        return None


class LiffAuthIn(BaseModel):
    id_token: str = ""


@router.post("/api/line/liff/auth")
async def api_liff_auth(req: LiffAuthIn):
    """LIFF id_token → 验签 → 查 LINE 绑定 → 签 Pearnly token(webview 内用)。"""
    claims = _verify_id_token(req.id_token)
    line_user_id = (claims or {}).get("sub")
    if not line_user_id:
        raise PosError("purchase.unexpected", 401, detail="liff_verify_failed")
    user = db.get_user_by_line_user_id(line_user_id)
    if not user:
        # 未绑定 → 引导先在 LINE 发绑定码绑定 Pearnly 账号。
        raise PosError("purchase.unexpected", 403, detail="line_not_bound")
    token = create_access_token(
        user_id=str(user["id"]),
        username=user.get("username") or "",
        plan=user.get("plan") or "free",
        tenant_id=str(user["tenant_id"]) if user.get("tenant_id") else None,
        role=user.get("role") or "owner",
    )
    return ok({"token": token, "username": user.get("username") or ""})


@router.get("/api/line/liff/config")
async def api_liff_config():
    """前端取 LIFF ID(公开·非密)→ liff.init。未配则空,前端走站内回退。"""
    return ok({"liff_id": os.getenv("LINE_LIFF_ID", "").strip()})


@router.get("/liff/purchase/{doc_id}")
async def liff_purchase_entry(doc_id: str, request: Request, view: str = "", ws: str = ""):
    """LIFF 页入口:跳 /home 复核屏(前端按 liff 参数走 LIFF 鉴权 + 打开该单)。

    view=receipt(PO-7)→ 落只读详情页(出/下载替代收据),非编辑复核屏。
    ws=该单所属套账 → 复核屏自动切到该套账并跳过套账门。
    """
    extra = ("&view=receipt" if view == "receipt" else "") + (f"&ws={ws}" if ws else "")
    return RedirectResponse(f"/home?liff=purchase&doc={doc_id}{extra}", status_code=302)


@router.get("/liff/purchase-inbox/{item_id}")
async def liff_purchase_inbox_entry(item_id: str, request: Request, ws: str = ""):
    """LIFF 入口(待归类):跳 /home 待归类页(前端走 LIFF 鉴权 + 定位该待归类项)。"""
    extra = f"&ws={ws}" if ws else ""
    return RedirectResponse(f"/home?liff=purchase&inbox={item_id}{extra}", status_code=302)
