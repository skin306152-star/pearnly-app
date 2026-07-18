# -*- coding: utf-8 -*-
"""操作员花名册管理 API(波3 · DL-8)· owner-only。

守卫 = dms_routes._authorize(C1 通用无码守卫:dms_portal 闸 + 入口作用域 + plan 推送闸)
叠加 owner-only。操作员 user 永不该有 dms 门 token(只走 LINE),此处防御性再判 role:非
owner → 403 owner_only。所有 {user_id} 由 service 层校验属本租户且有档案行(防跨租户 · 防对
owner 自身操作)。写侧沿用 request.json() 手取(同 dms_routes 风格),不引 pydantic 模型。
"""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Request

from core.route_helpers import _tid
from routes.dms_routes import _authorize as _dms_authorize
from services.dms_roster import service as roster
from services.erp import push_store

router = APIRouter()

# service 错误码 → HTTP 状态(4xx 语义诚实,不把可预期失败裸成 500)。
_ERR_STATUS = {
    "dms_roster.no_tenant": 400,
    "dms_roster.required_fields": 422,
    "dms_roster.invalid_role": 400,
    "dms_roster.invalid_status": 400,
    "dms_roster.no_endpoint": 400,
    "dms_roster.not_found": 404,
    "dms_roster.inactive": 400,
    "dms_roster.endpoint_missing": 400,
    "dms_roster.endpoint_update_failed": 500,
    "dms_roster.create_failed": 500,
    "dms_roster.endpoint_failed": 500,
    "dms_roster.bind_code_failed": 500,
}


def _require_owner(request: Request) -> Dict[str, Any]:
    user = _dms_authorize(request)
    if (user.get("role") or "") != "owner":
        raise HTTPException(403, detail="dms_roster.owner_only")
    return user


def _unwrap(result: Dict[str, Any]) -> Dict[str, Any]:
    err = result.get("error")
    if err:
        raise HTTPException(_ERR_STATUS.get(err, 400), detail=err)
    return result


@router.get("/api/dms/operators")
async def list_operators(request: Request):
    owner = _require_owner(request)
    return _unwrap(roster.list_operators(owner))


@router.post("/api/dms/operators")
async def create_operator(request: Request):
    owner = _require_owner(request)
    body = await request.json()
    return _unwrap(
        roster.create_operator(
            owner,
            display_name=body.get("display_name"),
            dms_username=body.get("dms_username"),
            dms_password=body.get("dms_password"),
            dms_role=body.get("dms_role"),
        )
    )


@router.patch("/api/dms/operators/{user_id}")
async def update_operator(user_id: str, request: Request):
    owner = _require_owner(request)
    body = await request.json()
    return _unwrap(
        roster.update_operator(
            owner,
            user_id,
            display_name=body.get("display_name"),
            dms_role=body.get("dms_role"),
            dms_username=body.get("dms_username"),
            dms_password=body.get("dms_password"),
        )
    )


@router.post("/api/dms/operators/{user_id}/status")
async def set_operator_status(user_id: str, request: Request):
    owner = _require_owner(request)
    body = await request.json()
    return _unwrap(roster.set_status(owner, user_id, str(body.get("status") or "").strip()))


@router.post("/api/dms/operators/{user_id}/bind-code")
async def issue_operator_bind_code(user_id: str, request: Request):
    owner = _require_owner(request)
    return _unwrap(roster.issue_bind_code(owner, user_id))


@router.get("/api/dms/records")
async def dms_tenant_records(request: Request, limit: int = 100, offset: int = 0):
    """C6 · owner 视角全租户 mrerp_dms 推送记录 + 操作员归属列(owner 限本租户)。"""
    owner = _require_owner(request)
    return push_store.list_dms_push_logs_for_tenant(
        _tid(owner), limit=min(max(limit, 1), 200), offset=max(0, offset)
    )
