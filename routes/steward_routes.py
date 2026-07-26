# -*- coding: utf-8 -*-
"""智能管家 HTTP API:会话 + 消息 + 任务(B3 起消息异步:入队秒回,执行在 worker)。

六端点(前端契约,static/ai/ai-api-steward.js 逐条对齐):
  GET  /api/ai/steward/status                  闸态探针(闸关也回 200 {enabled:false})
  POST /api/ai/steward/sessions                建会话
  GET  /api/ai/steward/sessions/{sid}          重建消息流 + 当前任务 id
  POST /api/ai/steward/sessions/{sid}/messages 说一句话 → 立即应承(+ 入队的任务 id)
  GET  /api/ai/steward/tasks/{tid}             左窗任务数据(轮询;失联任务就地收口)
  POST /api/ai/steward/tasks/{tid}/cancel      取消还在跑的任务(幂等)

除 status 外全组挂 `pearnly_ai_steward`(tenant 级默认关 · fail-closed · 叠加 pearnly_ai_m1):
闸关一律 404 —— 对存量用户等于不存在。status 走 m1 鉴权但把 steward 闸态当数据返回,免得
闸关用户每开一次 /ai 就吃一条 404(照 front_desk /status 先例)。

权限统一用 tax.filing.view:管家 M1 只读,它能看到的每一样(矩阵/工单/推送/识别记录)都是
「看申报工作」这一层的东西,不另立细码;写能力(B3 写工具)届时再叠自己的动作权限。

编排薄:本层只做鉴权 + 作用域 + 取值,一句话怎么变成任务在 services/steward。
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from core import db, feature_flags
from core.route_helpers import authorize_pearnly_ai
from services.authz.deps import get_authz
from services.steward import copy as steward_copy, orchestrator, store, worker
from services.steward.registry import ToolContext

router = APIRouter()
logger = logging.getLogger(__name__)

_C_VIEW = "tax.filing.view"
_NOT_FOUND = "steward.not_found"
_MAX_TEXT = 2000


class MessageIn(BaseModel):
    text: str = Field(..., min_length=1, max_length=8000, description="会计说的一句话")
    lang: str = Field("", max_length=8, description="回复语言(zh/th);不给则按这句话自判")


def _authorize(request: Request) -> tuple[dict, str]:
    """登录 + 双闸(pearnly_ai_m1 叠加 pearnly_ai_steward · 关→404 fail-closed)+ 读权限。"""
    user, tenant_id = authorize_pearnly_ai(request, _C_VIEW, not_found=_NOT_FOUND)
    if not feature_flags.pearnly_ai_steward_enabled_for(tenant_id):
        raise HTTPException(404, detail=_NOT_FOUND)
    return user, tenant_id


def _context(request: Request, user: dict, tenant_id: str, lang: str = "") -> ToolContext:
    """工具执行身份:账套作用域与 /api/tax-profile/matrix 同源(被分派成员只看分到的)。"""
    authz = get_authz(request, user)
    allowed = None
    if not user.get("is_super_admin") and authz.scope_mode == "assigned":
        allowed = frozenset(int(i) for i in (authz.workspace_ids or frozenset()))
    return ToolContext(
        user=user,
        tenant_id=tenant_id,
        user_id=str(user["id"]),
        allowed_client_ids=allowed,
        lang=lang,
    )


def _session_or_404(cur, *, tenant_id: str, session_id: str, user_id: str) -> dict:
    session = store.get_session(cur, tenant_id=tenant_id, session_id=session_id, user_id=user_id)
    if not session:
        raise HTTPException(404, detail=_NOT_FOUND)
    return session


@router.get("/api/ai/steward/status")
async def get_status(request: Request):
    """探针专用:闸态当数据返回,不走闸 404(前端据此挂三态,免 console 噪音)。"""
    _user, tenant_id = authorize_pearnly_ai(request, _C_VIEW, not_found=_NOT_FOUND)
    return {"enabled": bool(feature_flags.pearnly_ai_steward_enabled_for(tenant_id))}


@router.post("/api/ai/steward/sessions")
async def create_session(request: Request):
    """建会话。标题留空,第一句话落库时自动填(见 orchestrator)。"""
    user, tenant_id = _authorize(request)
    store.ensure_once()
    with db.get_cursor(commit=True) as cur:
        session = store.create_session(cur, tenant_id=tenant_id, user_id=str(user["id"]))
    return {"session_id": str(session["id"])}


@router.get("/api/ai/steward/sessions/{session_id}")
async def get_session(session_id: str, request: Request):
    """重建消息流(刷新页面靠服务端重建,不在浏览器存对话)。"""
    user, tenant_id = _authorize(request)
    store.ensure_once()
    with db.get_cursor() as cur:
        _session_or_404(cur, tenant_id=tenant_id, session_id=session_id, user_id=str(user["id"]))
        messages = store.list_messages(cur, tenant_id=tenant_id, session_id=session_id)
        current = store.latest_task_id(cur, tenant_id=tenant_id, session_id=session_id)
    out = {
        "session_id": session_id,
        "messages": [store.public_message(m) for m in messages],
    }
    if current:
        out["current_task_id"] = current
    return out


@router.post("/api/ai/steward/sessions/{session_id}/messages")
async def post_message(session_id: str, req: MessageIn, request: Request):
    """说一句话 → 立即返回应承;派了活就给 task_id + task_status,前端轮询左窗看真进度。
    工具执行在后台 worker(接分钟级长活的前提),追问/降级/超范围仍当场回。"""
    user, tenant_id = _authorize(request)
    store.ensure_once()
    with db.get_cursor() as cur:
        _session_or_404(cur, tenant_id=tenant_id, session_id=session_id, user_id=str(user["id"]))
    ctx = _context(request, user, tenant_id, lang=req.lang)
    text = req.text.strip()[:_MAX_TEXT]
    return orchestrator.handle_message(ctx, session_id=session_id, text=text)


@router.get("/api/ai/steward/tasks/{task_id}")
async def get_task(task_id: str, request: Request):
    """左窗任务数据(前端直接喂 B1 状态组件)。查询前先把失联任务就地收口 ——
    worker 死了/急停了,轮询的人也要在超时限后看到诚实的 failed,不是永远转圈。"""
    _user, tenant_id = _authorize(request)
    store.ensure_once()
    with db.get_cursor(commit=True) as cur:
        worker.heal_stale(cur, tenant_id=tenant_id, task_id=task_id)
        task = store.get_task(cur, tenant_id=tenant_id, task_id=task_id)
    if not task:
        raise HTTPException(404, detail=_NOT_FOUND)
    return store.public_task(task)


@router.post("/api/ai/steward/tasks/{task_id}/cancel")
async def cancel_task(task_id: str, request: Request):
    """取消任务。只有还在跑的能取消;已收尾的原样返回(幂等,连点两下不报错)。
    与 worker 收尾赛跑时先落者赢:取消落定后,晚到的执行结果被 finish 守卫拒收。"""
    _user, tenant_id = _authorize(request)
    store.ensure_once()
    with db.get_cursor(commit=True) as cur:
        task = store.get_task(cur, tenant_id=tenant_id, task_id=task_id)
        if not task:
            raise HTTPException(404, detail=_NOT_FOUND)
        if task["status"] == store.TASK_RUNNING:
            lang = (task.get("payload") or {}).get("lang") or steward_copy.DEFAULT_LANG
            reason = steward_copy.fail_reason(worker.ERR_CANCELLED, lang)
            cancelled = store.cancel_task(
                cur,
                tenant_id=tenant_id,
                task_id=task_id,
                steps=store.fail_steps(task.get("steps") or [], reason),
            )
            task = cancelled or store.get_task(cur, tenant_id=tenant_id, task_id=task_id)
    return store.public_task(task)
