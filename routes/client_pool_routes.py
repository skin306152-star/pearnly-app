# -*- coding: utf-8 -*-
"""LINE 待问客户池 · 会计端 HTTP API(D2-S8+S9 · 方案 §7.2 拆单表)。

四端点全挂双闸:先照 workorder_routes 的 `pearnly_ai_m1` 404 范式(登录+M1 闸+权限),
再叠 `pearnly_ai_client_pool`(方案主窗拍板修正 4)——任一闸关,端点对存量用户等于不存在。
鉴权细码复用工单 tax.filing.* 系(待问池是工单外围功能,权限边界与工单裁决一致:能裁决
该工单的人才能替客户暂挂问题/推批/替客户裁决)。

写路径全部薄封装 services/line_binding 既有 store/push/decisions 通道,不新起裁决逻辑
(C4 血泪:状态词/裁决词零臆造,本文件只做鉴权 + 归属校验 + 参数翻译)。
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from pydantic import BaseModel, Field

from core import db
from core.route_helpers import authorize_pearnly_ai
from routes.workorder_routes import _auto_advance
from services.authz.deps import check_workspace_scope
from services.line_binding import client_pool_vocab as vocab
from services.line_binding import line_client_contact
from services.line_binding import line_client_pool_push as pool_push
from services.line_binding import line_client_pool_store as pool_store
from services.workorder import api as wo_api
from services.workorder import store as wo_store
from services.workspace import store as workspace_store

router = APIRouter()

# 复用工单 SoD 细码(routes/workorder_routes.py 同名常量字面量):待问池挂在工单之下,
# 谁能制单裁决谁就能替客户暂挂/推批/裁决,不另开一套权限维度。
_C_VIEW = "tax.filing.view"
_C_PREPARE = "tax.filing.create"


class StageIn(BaseModel):
    work_order_id: str = Field(..., description="票所属工单 id")
    item_id: str = Field(..., description="被暂挂的 work_order_item id")
    question_type: str = Field(..., description="direction | amount | drop | freeform")
    payload: dict = Field(default_factory=dict, description="渲染问题用(票号/供应商/候选项)")


class PushBatchIn(BaseModel):
    workspace_client_id: int = Field(..., description="账套主体 id")


class DecideIn(BaseModel):
    workspace_client_id: int = Field(..., description="账套主体 id(归属校验用)")
    decision: str = Field(..., description="face_value | recalc | exclude | assign_kind | waive")
    values: Optional[dict] = Field(None, description="recalc 时的人工补正数")
    kind: Optional[str] = Field(None, description="assign_kind 方向裁决")
    reason: Optional[str] = Field(None, max_length=500, description="waive 豁免理由")


def _authorize(request: Request, perm: str) -> tuple[dict, str]:
    """M1 闸(登录+404 fail-closed)之上再叠 client_pool 闸,同样 404 不泄漏端点存在性。"""
    from core.feature_flags import pearnly_ai_client_pool_enabled_for

    user, tenant_id = authorize_pearnly_ai(request, perm, not_found="client_pool.not_found")
    if not pearnly_ai_client_pool_enabled_for(tenant_id):
        raise HTTPException(404, detail="client_pool.not_found")
    return user, tenant_id


def _assert_owns_client(cur, request: Request, user: dict, tenant_id: str, ws_id: int) -> None:
    cur.execute(
        "SELECT 1 FROM workspace_clients WHERE id = %s AND tenant_id = %s", (ws_id, tenant_id)
    )
    if not cur.fetchone():
        raise HTTPException(404, detail="client_pool.client_not_found")
    check_workspace_scope(request, user, ws_id)


def _question_out(row: dict) -> dict:
    """裁给前端的安全子集(不带 tenant_id)。"""
    return {
        "id": row["id"],
        "workspace_client_id": row["workspace_client_id"],
        "work_order_id": row["work_order_id"],
        "item_id": row["item_id"],
        "period": row["period"],
        "question_type": row["question_type"],
        "question_payload": row.get("question_payload") or {},
        "status": row["status"],
        "batch_id": row.get("batch_id"),
        "answer_raw": row.get("answer_raw"),
        "resolution": row.get("resolution"),
        "created_at": row.get("created_at"),
        "sent_at": row.get("sent_at"),
        "answered_at": row.get("answered_at"),
        "closed_at": row.get("closed_at"),
    }


@router.post("/api/ai/client-pool/stage")
async def stage_question(req: StageIn, request: Request):
    """W3 第四动作「推 LINE 待问」落点(S9 用)。归集入池,不推送(方案 §3.1 手动攒批)。"""
    user, tenant_id = _authorize(request, _C_PREPARE)
    if req.question_type not in vocab.QUESTION_TYPES:
        raise HTTPException(
            422, detail={"code": "client_pool.unknown_question_type", "message": req.question_type}
        )

    with db.get_cursor() as cur:
        wo = wo_store.get_work_order(cur, tenant_id=tenant_id, work_order_id=req.work_order_id)
        if not wo:
            raise HTTPException(404, detail="client_pool.work_order_not_found")
        check_workspace_scope(request, user, wo["workspace_client_id"])
        item = wo_store.get_item(
            cur, tenant_id=tenant_id, work_order_id=req.work_order_id, item_id=req.item_id
        )
        if not item:
            raise HTTPException(404, detail="client_pool.item_not_found")
        workspace_client_id = wo["workspace_client_id"]
        period = wo["period"]

    try:
        question = pool_store.stage(
            tenant_id,
            workspace_client_id=workspace_client_id,
            work_order_id=req.work_order_id,
            item_id=req.item_id,
            period=period,
            question_type=req.question_type,
            question_payload=req.payload,
            created_by=f"user:{user['id']}",
        )
    except pool_store.ClientPoolError as e:
        raise HTTPException(422, detail={"code": "client_pool.stage_failed", "message": str(e)})
    if not question:
        raise HTTPException(409, detail="client_pool.stage_conflict")
    return {"ok": True, "question": _question_out(question)}


@router.get("/api/ai/client-pool")
async def list_client_pool(request: Request, workspace_client_id: Optional[int] = None):
    """S8 客户池页读侧:给定 workspace_client_id 只看该客户;缺省按本租户逐客户分组
    (只带回有 active 问题的客户,零问题的客户不占版面)。"""
    user, tenant_id = _authorize(request, _C_VIEW)

    if workspace_client_id is not None:
        with db.get_cursor() as cur:
            _assert_owns_client(cur, request, user, tenant_id, workspace_client_id)
        client = workspace_store.get_workspace_client(
            workspace_client_id, str(user["id"]), tenant_id=tenant_id
        )
        name_by_id = {workspace_client_id: (client or {}).get("name")}
        candidates = [workspace_client_id]
    else:
        clients = workspace_store.list_workspace_clients(str(user["id"]), tenant_id=tenant_id)
        name_by_id = {c["id"]: c.get("name") for c in clients}
        candidates = list(name_by_id.keys())

    groups = []
    for ws_id in candidates:
        active = pool_store.list_for_client(tenant_id, ws_id)
        if not active:
            continue
        contact = line_client_contact.get_contact(tenant_id, ws_id)
        by_status: dict = {s: [] for s in vocab.ACTIVE_STATUSES}
        for row in active:
            by_status.setdefault(row["status"], []).append(_question_out(row))
        groups.append(
            {
                "workspace_client_id": ws_id,
                "name": name_by_id.get(ws_id),
                "bound": bool(contact),
                "questions": by_status,
            }
        )
    return {"groups": groups}


@router.post("/api/ai/client-pool/push-batch")
async def push_batch(req: PushBatchIn, request: Request):
    """会计点「推这批给 XX 客户」(方案 §3.1)。结构化四态返回,永不假成功——
    调用方(前端)按 ok/reason 渲染未绑/推送失败/已发横幅,本端点本身恒 200。"""
    user, tenant_id = _authorize(request, _C_PREPARE)
    with db.get_cursor() as cur:
        _assert_owns_client(cur, request, user, tenant_id, req.workspace_client_id)
    result = pool_push.push_batch_for_client(
        tenant_id, req.workspace_client_id, actor=f"user:{user['id']}"
    )
    return result


@router.post("/api/ai/client-pool/questions/{question_id}/decide")
async def decide_question(
    question_id: int, req: DecideIn, request: Request, background: BackgroundTasks
):
    """S8 manual_review 会计裁决:走既有裁决通道 record_decision(actor=user:{id}),
    成功后问题 manual_review→applied(方案 §4.2 末段·同 line_client_answer 客户裁决路
    落库的 resolution 形状),并自动续跑工单(P-7 同源自驱,MC2-A1 补的漏接)。"""
    user, tenant_id = _authorize(request, _C_PREPARE)
    with db.get_cursor() as cur:
        _assert_owns_client(cur, request, user, tenant_id, req.workspace_client_id)

    rows = pool_store.list_for_client(
        tenant_id, req.workspace_client_id, statuses=(vocab.MANUAL_REVIEW,)
    )
    question = next((r for r in rows if r["id"] == question_id), None)
    if question is None:
        raise HTTPException(404, detail="client_pool.question_not_found")

    with db.get_cursor(commit=True) as cur:
        try:
            evt = wo_api.record_decision(
                cur,
                tenant_id=tenant_id,
                work_order_id=question["work_order_id"],
                item_id=question["item_id"],
                decision=req.decision,
                values=req.values,
                actor=f"user:{user['id']}",
                kind=req.kind,
                reason=req.reason,
            )
        except wo_api.WorkOrderApiError as e:
            code = 404 if e.code == "workorder.item_not_found" else 422
            raise HTTPException(code, detail={"code": e.code}) from e

    resolution = {"decision": req.decision, "actor": f"user:{user['id']}", "event_id": evt["id"]}
    if req.kind is not None:
        resolution["kind"] = req.kind
    if req.values is not None:
        resolution["values"] = req.values

    try:
        updated = pool_store.transition(
            tenant_id, question_id, vocab.APPLIED, resolution=resolution
        )
    except pool_store.IllegalTransitionError as e:
        raise HTTPException(
            409, detail={"code": "client_pool.illegal_transition", "message": str(e)}
        )
    _auto_advance(background, tenant_id, question["work_order_id"], user)
    return {"ok": True, "event_id": evt["id"], "question": _question_out(updated)}
