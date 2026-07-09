"""
line_account_merge_routes.py · LINE 临时账号补邮箱(REFACTOR-B1 + P0 安全修复)

    GET  /api/me/needs_email           前端查是否是 line_xxx@line.local 临时占位
    POST /api/me/line_complete_email   补邮箱:
        - 该 email 已绑他人账号 → 409 拒绝,不合并、不发 token(邮箱从未验证归属,
          曾经这里直接合并 + 颁发目标账号 token,是可被任何知情者利用的账户接管漏洞)
        - 不存在(或就是本账号自己)→ update_user_email_and_username + 重发 token

E2E 闸:spec 14(LINE binding)间接覆盖。
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from core import db
from core.auth import get_current_user_from_request, create_access_token

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/api/me/needs_email")
async def me_needs_email(request: Request):
    user = get_current_user_from_request(request)
    uname = user.get("username") or ""
    needs = db.is_line_placeholder_username(uname)
    return {"needs_email": bool(needs)}


class _LinePostEmail(BaseModel):
    email: str


@router.post("/api/me/line_complete_email")
async def me_line_complete_email(payload: _LinePostEmail, request: Request):
    user = get_current_user_from_request(request)
    cur_username = user.get("username") or ""
    if not db.is_line_placeholder_username(cur_username):
        raise HTTPException(status_code=400, detail="not_a_line_temp_account")

    email_raw = (payload.email or "").strip().lower()
    if not email_raw or "@" not in email_raw or "." not in email_raw.split("@", 1)[1]:
        raise HTTPException(status_code=400, detail="email_invalid")

    cur_user_id = str(user["id"])

    # 检查该 email 是否已被其他账号占用
    existing = db.find_user_by_username(email_raw)
    if existing and str(existing["id"]) != cur_user_id:
        # P0:此邮箱从未验证归属(只查了格式)。命中他人账号绝不可合并/发 token——
        # 否则任何人报出受害者邮箱就能借自己的 LINE 占位账号顶替登录(账户接管)。
        # 命中即拒,指引去走原账号登录后在设置里主动绑定。
        raise HTTPException(status_code=409, detail="email_registered_use_login")
    else:
        # 直接更新临时账号
        ok = db.update_user_email_and_username(cur_user_id, email_raw)
        if not ok:
            raise HTTPException(status_code=500, detail="update_failed")
        # token 里的 username 变了 · 重发一次
        refreshed = db.find_user_by_id(cur_user_id)
        new_token = create_access_token(
            user_id=cur_user_id,
            username=refreshed["username"],
            plan=refreshed.get("plan") or "free",
            tenant_id=str(refreshed["tenant_id"]) if refreshed.get("tenant_id") else None,
            role=refreshed.get("role") or "owner",
            is_super_admin=bool(refreshed.get("is_super_admin")),
            remember_me=True,
        )
        return {"ok": True, "merged": False, "token": new_token}
