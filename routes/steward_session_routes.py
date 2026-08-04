# -*- coding: utf-8 -*-
"""管家会话管理 HTTP API(S1 会话流改版):列表 / 改名 / 删除 + 附件送出前删除 + 成本余额。

五端点(前端契约,static/ai/ai-api-steward.js 逐条对齐):
  GET  /api/ai/steward/sessions                   本人会话列表(侧栏历史;空会话不列)
  POST /api/ai/steward/sessions/{sid}/rename      改名(只改标题,不动消息)
  POST /api/ai/steward/sessions/{sid}/delete      删除(行级 CASCADE + 提交后删盘上原件)
  POST /api/ai/steward/attachments/{aid}/delete   删还没送出的附件(已随消息送出的 409)
  GET  /api/ai/steward/budget?session_id=...      成本余额(会话/租户日两级 已用与上限)

守门与 steward_routes 同一套(routes/steward_common):双闸 fail-closed 404 +
会话三锚归属(租户/会话/本人)。改名/删除是本人自己的工作记录,view 权限即可 ——
这里没有跨人的数据,不需要更高的动作权限。
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from core import db
from routes.steward_common import NOT_FOUND, authorize_steward, session_or_404
from services.steward import attachments, budget, sessions_dal, store

router = APIRouter()
logger = logging.getLogger(__name__)

_ATTACHMENT_BOUND = "steward.attachment_bound"
_EMPTY_TITLE = "steward.empty_title"


class RenameIn(BaseModel):
    title: str = Field(..., min_length=1, max_length=120, description="新标题")


@router.get("/api/ai/steward/sessions")
async def list_sessions(request: Request):
    """本人会话列表(最近活跃在前)。只列说过话的会话:挂载时预建、一句没说的空会话
    是草稿位不是历史记录。"""
    user, tenant_id = authorize_steward(request)
    store.ensure_once()
    with db.get_cursor() as cur:
        rows = sessions_dal.list_sessions(cur, tenant_id=tenant_id, user_id=str(user["id"]))
    return {"sessions": [sessions_dal.public_session(r) for r in rows]}


@router.post("/api/ai/steward/sessions/{session_id}/rename")
async def rename_session(session_id: str, req: RenameIn, request: Request):
    user, tenant_id = authorize_steward(request)
    store.ensure_once()
    # min_length=1 挡不住纯空白(" " 长度是 1),strip 后再判一次。
    title = req.title.strip()
    if not title:
        raise HTTPException(422, detail=_EMPTY_TITLE)
    with db.get_cursor(commit=True) as cur:
        ok = sessions_dal.rename_session(
            cur,
            tenant_id=tenant_id,
            session_id=session_id,
            user_id=str(user["id"]),
            title=title,
        )
    if not ok:
        raise HTTPException(404, detail=NOT_FOUND)
    return {"ok": True, "title": title[:120]}


@router.post("/api/ai/steward/sessions/{session_id}/delete")
async def delete_session(session_id: str, request: Request):
    """删会话。行级由 ON DELETE CASCADE 收(消息/任务/附件行),盘上的附件原件在
    【事务提交后】逐件删 —— 先删文件再回滚会留下行还在、件已没的死引用;反向顺序
    最坏只是文件多活到 30 天 TTL 清扫,不产生错账。"""
    user, tenant_id = authorize_steward(request)
    store.ensure_once()
    with db.get_cursor(commit=True) as cur:
        refs = sessions_dal.delete_session(
            cur, tenant_id=tenant_id, session_id=session_id, user_id=str(user["id"])
        )
    if refs is None:
        raise HTTPException(404, detail=NOT_FOUND)
    for ref in refs:
        attachments.remove_file(ref)
    return {"ok": True}


@router.post("/api/ai/steward/attachments/{attachment_id}/delete")
async def delete_attachment(attachment_id: str, request: Request):
    """删还没送出的附件(附件盘上的 ×)。已随消息送出的是对话留痕,409 拒删 ——
    气泡下的原件行消失等于改历史。文件同样在提交后删。"""
    user, tenant_id = authorize_steward(request)
    store.ensure_once()
    with db.get_cursor(commit=True) as cur:
        row = attachments.get_owned(
            cur, tenant_id=tenant_id, attachment_id=attachment_id, user_id=str(user["id"])
        )
        if not row:
            raise HTTPException(404, detail=NOT_FOUND)
        if row.get("message_id"):
            raise HTTPException(409, detail=_ATTACHMENT_BOUND)
        cur.execute(
            "DELETE FROM steward_attachments WHERE tenant_id = %s AND id = %s",
            (tenant_id, attachment_id),
        )
    attachments.remove_file(str(row.get("file_ref") or ""))
    return {"ok": True}


@router.get("/api/ai/steward/budget")
async def get_budget(request: Request, session_id: str):
    """成本余额(读侧,只看不占坑)。会话归属先判 —— 余额按会话汇总,别人的会话连
    数字也不该看到。"""
    user, tenant_id = authorize_steward(request)
    store.ensure_once()
    with db.get_cursor() as cur:
        session_or_404(cur, tenant_id=tenant_id, session_id=session_id, user_id=str(user["id"]))
    return budget.snapshot(tenant_id=tenant_id, session_id=session_id)
