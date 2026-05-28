"""
line_account_merge_routes.py · LINE 临时账号补邮箱 + 合并老账号(REFACTOR-B1)

从 app.py L3548-3620 抽出 · 0 业务逻辑改:
    GET  /api/me/needs_email           前端查是否是 line_xxx@line.local 临时占位
    POST /api/me/line_complete_email   补邮箱:
        - 该 email 已绑老账号 → merge_line_account_into_existing + 颁老账号 token
        - 不存在 → update_user_email_and_username + 重发 token(username 变)

E2E 闸:spec 14(LINE binding)间接覆盖。
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

import db
from auth import get_current_user_from_request, create_access_token

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
    line_uid = user.get("line_uid")

    # 检查该 email 是否已被其他账号占用
    existing = db.find_user_by_username(email_raw)
    if existing and str(existing["id"]) != cur_user_id:
        # 合并到老账号
        if not line_uid:
            raise HTTPException(status_code=500, detail="missing_line_uid")
        ok = db.merge_line_account_into_existing(cur_user_id, str(existing["id"]), line_uid)
        if not ok:
            raise HTTPException(status_code=500, detail="merge_failed")
        # 颁老账号 token
        merged_user = db.find_user_by_id(str(existing["id"]))
        if not merged_user:
            raise HTTPException(status_code=500, detail="target_user_lost")
        db.update_last_login(str(merged_user["id"]))
        new_token = create_access_token(
            user_id=str(merged_user["id"]),
            username=merged_user["username"],
            plan=merged_user.get("plan") or "free",
            tenant_id=str(merged_user["tenant_id"]) if merged_user.get("tenant_id") else None,
            role=merged_user.get("role") or "owner",
            is_super_admin=bool(merged_user.get("is_super_admin")),
            remember_me=True,
        )
        return {"ok": True, "merged": True, "token": new_token}
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
