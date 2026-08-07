# -*- coding: utf-8 -*-
"""商品收发存报表(Stock Card)API · 事务所端按客户账套出进销存流水。

复用 accounting_common 的鉴权/套账解析/模块门控(与 acct.books 同一套四段式:auth_member
→ get_cursor_rls → gate(accounting 模块) → resolve_ws),权限码另立 stockcard.* 两档
(report.view 读;opening.manage 写期初/归并 · 见 services/authz/registry.py)。业务闸再叠
stock_card_report 灰度(默认关 · 超管在平台后台按租户放量):status 探针闸关也 200(前端
按 enabled 挂三态);其余业务端点闸关一律 403,不裸露"这功能存在但你用不了"之外的信息。

数字字段一律输出字符串(core/route_helpers 惯例:Decimal 经默认 JSON 编码器会被前端当
float 解析,精度漂移在钱这里不可接受)。
"""

from __future__ import annotations

from datetime import date
from typing import Optional

from fastapi import APIRouter, Query, Request
from pydantic import BaseModel, Field

from core import db, feature_flags
from core.pos_api import PosError
from routes.accounting_common import auth_member, gate, resolve_ws
from services.stockcard import merge as merge_svc
from services.stockcard import opening as opening_svc
from services.stockcard import report as report_svc

router = APIRouter(prefix="/api/stockcard", tags=["stockcard"])

_C_VIEW = "stockcard.report.view"
_C_MANAGE = "stockcard.opening.manage"


def _require_enabled(tenant_id: str) -> None:
    """业务端点闸关一律 403(status 探针例外 · 见 api_status)。"""
    if not feature_flags.stock_card_report_enabled_for(tenant_id):
        raise PosError("stockcard.disabled", 403)


def _parse_date(raw: str, *, field: str) -> date:
    """报表层用真 date 对象比较(report.py 拿 psycopg2 读回的 date 逐行比大小),query
    string 在这里一次性转好,不把字符串漏进服务层跟 date 混比。"""
    try:
        return date.fromisoformat(raw.strip())
    except (ValueError, AttributeError) as e:
        raise PosError("stockcard.bad_date", 422, detail=field) from e


class OpeningIn(BaseModel):
    product_id: Optional[str] = Field(None, description="挂到商品主档;留空则按 name 归组")
    name: Optional[str] = Field(None, max_length=200, description="无商品档时按清洗名归组")
    qty: str = Field(..., description="Decimal 字符串")
    unit_cost: str = Field(..., description="Decimal 字符串 · 不含 VAT 净单价")
    as_of_date: str = Field(..., description="ISO 日期,期初「截至这天」的结存")


class OpeningsIn(BaseModel):
    rows: list[OpeningIn] = Field(..., min_length=1, max_length=500)


class MergeIn(BaseModel):
    name_key: str = Field(..., min_length=1, description="要归并的 name: 轨清洗品名")
    product_id: str = Field(..., min_length=1, description="并入的目标商品(须已存在于本账套)")


def _public_opening(row: dict) -> dict:
    return {
        "id": row["id"],
        "product_id": str(row["product_id"]) if row.get("product_id") else None,
        "name_key": row.get("name_key"),
        "qty": str(row["qty"]),
        "unit_cost": str(row["unit_cost"]),
        "as_of_date": row["as_of_date"].isoformat()
        if hasattr(row["as_of_date"], "isoformat")
        else row["as_of_date"],
    }


@router.get("/status")
async def api_status(request: Request):
    """闸态探针:闸关也 200(照 routes/steward_routes.py 惯例,前端挂三态)。"""
    _, tenant_id = auth_member(request, _C_VIEW)
    with db.get_cursor_rls(tenant_id) as cur:
        try:
            gate(cur, tenant_id)
            module_on = True
        except PosError:
            module_on = False
    enabled = module_on and feature_flags.stock_card_report_enabled_for(tenant_id)
    return {"ok": True, "enabled": enabled}


@router.get("/summary")
async def api_summary(
    request: Request,
    workspace_client_id: int = Query(...),
    date_from: str = Query(...),
    date_to: str = Query(...),
):
    _, tid = auth_member(request, _C_VIEW)
    d_from = _parse_date(date_from, field="date_from")
    d_to = _parse_date(date_to, field="date_to")
    with db.get_cursor_rls(tid, commit=False) as cur:
        gate(cur, tid)
        _require_enabled(tid)
        ws = resolve_ws(cur, request, tid, workspace_client_id)
        payload = report_svc.summary(
            cur, tenant_id=tid, workspace_client_id=ws, date_from=d_from, date_to=d_to
        )
    return {"ok": True, **payload}


@router.get("/card")
async def api_card(
    request: Request,
    workspace_client_id: int = Query(...),
    key: str = Query(...),
    date_from: str = Query(...),
    date_to: str = Query(...),
):
    _, tid = auth_member(request, _C_VIEW)
    d_from = _parse_date(date_from, field="date_from")
    d_to = _parse_date(date_to, field="date_to")
    with db.get_cursor_rls(tid, commit=False) as cur:
        gate(cur, tid)
        _require_enabled(tid)
        ws = resolve_ws(cur, request, tid, workspace_client_id)
        payload = report_svc.card(
            cur, tenant_id=tid, workspace_client_id=ws, key=key, date_from=d_from, date_to=d_to
        )
    if payload is None:
        raise PosError("stockcard.not_found", 404)
    return {"ok": True, **payload}


@router.get("/excluded")
async def api_excluded(
    request: Request,
    workspace_client_id: int = Query(...),
    date_from: str = Query(...),
    date_to: str = Query(...),
):
    _, tid = auth_member(request, _C_VIEW)
    d_from = _parse_date(date_from, field="date_from")
    d_to = _parse_date(date_to, field="date_to")
    with db.get_cursor_rls(tid, commit=False) as cur:
        gate(cur, tid)
        _require_enabled(tid)
        ws = resolve_ws(cur, request, tid, workspace_client_id)
        rows = report_svc.excluded(
            cur, tenant_id=tid, workspace_client_id=ws, date_from=d_from, date_to=d_to
        )
    return {"ok": True, "rows": rows}


@router.get("/openings")
async def api_list_openings(request: Request, workspace_client_id: int = Query(...)):
    _, tid = auth_member(request, _C_VIEW)
    with db.get_cursor_rls(tid, commit=False) as cur:
        gate(cur, tid)
        _require_enabled(tid)
        ws = resolve_ws(cur, request, tid, workspace_client_id)
        rows = opening_svc.list_openings(cur, tenant_id=tid, workspace_client_id=ws)
    return {"ok": True, "rows": [_public_opening(r) for r in rows]}


@router.post("/openings")
async def api_upsert_openings(
    req: OpeningsIn, request: Request, workspace_client_id: int = Query(...)
):
    user, tid = auth_member(request, _C_MANAGE)
    with db.get_cursor_rls(tid, commit=True) as cur:
        gate(cur, tid)
        _require_enabled(tid)
        ws = resolve_ws(cur, request, tid, workspace_client_id)
        rows = opening_svc.upsert_openings(
            cur,
            tenant_id=tid,
            workspace_client_id=ws,
            rows=[r.model_dump() for r in req.rows],
            created_by=user.get("id"),
        )
    return {"ok": True, "rows": [_public_opening(r) for r in rows]}


@router.post("/merge")
async def api_merge(req: MergeIn, request: Request, workspace_client_id: int = Query(...)):
    user, tid = auth_member(request, _C_MANAGE)
    with db.get_cursor_rls(tid, commit=True) as cur:
        gate(cur, tid)
        _require_enabled(tid)
        ws = resolve_ws(cur, request, tid, workspace_client_id)
        result = merge_svc.merge_into_product(
            cur,
            tenant_id=tid,
            workspace_client_id=ws,
            name_key=req.name_key,
            product_id=req.product_id,
            actor=user,
        )
    if result is None:
        raise PosError("stockcard.merge_target_missing", 422)
    return {"ok": True, **result}
