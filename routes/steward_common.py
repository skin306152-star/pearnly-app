# -*- coding: utf-8 -*-
"""管家路由的公共守门(S1 拆出):双闸鉴权与会话归属判定。

steward_routes / steward_session_routes / steward_stream_routes 三个文件同一套门,
各抄一份必漂(闸序、fail-closed 的 404 码、归属三锚,错一处就是越权面)。"""

from __future__ import annotations

from fastapi import HTTPException, Request

from core import feature_flags
from core.route_helpers import authorize_pearnly_ai
from services.steward import store

C_VIEW = "tax.filing.view"
NOT_FOUND = "steward.not_found"


def authorize_steward(request: Request, perm: str = C_VIEW) -> tuple[dict, str]:
    """登录 + 双闸(pearnly_ai_m1 叠加 pearnly_ai_steward · 关→404 fail-closed)+ 动作权限。"""
    user, tenant_id = authorize_pearnly_ai(request, perm, not_found=NOT_FOUND)
    if not feature_flags.pearnly_ai_steward_enabled_for(tenant_id):
        raise HTTPException(404, detail=NOT_FOUND)
    return user, tenant_id


def session_or_404(cur, *, tenant_id: str, session_id: str, user_id: str) -> dict:
    session = store.get_session(cur, tenant_id=tenant_id, session_id=session_id, user_id=user_id)
    if not session:
        raise HTTPException(404, detail=NOT_FOUND)
    return session
