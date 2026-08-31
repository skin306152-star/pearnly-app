# -*- coding: utf-8 -*-
"""商品收发存报表(Stock Card)API · ERP 门户按当前独立账套出进销存流水。

复用 accounting_common 的鉴权/套账解析/模块门控(与 acct.books 同一套四段式:auth_member
→ get_cursor_rls → gate(accounting 模块) → resolve_ws),权限码另立 stockcard.* 两档
(report.view 读;opening.manage 写期初 · 见 services/authz/registry.py)。网页只暴露一个
只读主视图 GET /report + 期初读/写 /openings;旧「汇总→单品详情」流程的 /summary、/card、
/excluded、/merge 路由已按 2026-08-27 口径删除,服务层 summary()/card() 仅供 Steward 内部
调用。
不设灰度闸(Zihao 2026-08-07 拍板:做完测完直接全开,accounting 模块闸 + 权限码就是
全部控制面);status 探针保留,回答的是「本租户 accounting 模块开没开」,供前端挂菜单三态。

数字字段一律输出字符串(core/route_helpers 惯例:Decimal 经默认 JSON 编码器会被前端当
float 解析,精度漂移在钱这里不可接受)。
"""

from __future__ import annotations

from datetime import date
from typing import Optional

from fastapi import APIRouter, Query, Request
from pydantic import BaseModel, Field

from core import db
from core.pos_api import PosError
from routes.accounting_common import auth_member, gate, resolve_ws
from services.stockcard import opening as opening_svc
from services.stockcard import report as report_svc
from services.erp import team_access

router = APIRouter(prefix="/api/stockcard", tags=["stockcard"])

_C_VIEW = "stockcard.report.view"
_C_MANAGE = "stockcard.opening.manage"


def _parse_date(raw: str, *, field: str) -> date:
    """报表层用真 date 对象比较(report.py 拿 psycopg2 读回的 date 逐行比大小),query
    string 在这里一次性转好,不把字符串漏进服务层跟 date 混比。解析逻辑单一来源见
    services.stockcard.opening.parse_iso_date(与期初层共用,错误码各自的 stockcard.bad_date)。"""
    return opening_svc.parse_iso_date(raw, code="stockcard.bad_date", field=field)


class OpeningIn(BaseModel):
    product_id: Optional[str] = Field(None, description="挂到商品主档;留空则按 name 归组")
    name: Optional[str] = Field(None, max_length=200, description="无商品档时按清洗名归组")
    qty: str = Field(..., description="Decimal 字符串")
    unit_cost: str = Field(..., description="Decimal 字符串 · 不含 VAT 净单价")
    as_of_date: str = Field(..., description="ISO 日期,期初「截至这天」的结存")


class OpeningsIn(BaseModel):
    rows: list[OpeningIn] = Field(..., min_length=1, max_length=500)


def _public_opening(row: dict) -> dict:
    return {
        "id": row["id"],
        "product_id": str(row["product_id"]) if row.get("product_id") else None,
        "name_key": row.get("name_key"),
        "qty": str(row["qty"]),
        "unit_cost": str(row["unit_cost"]),
        "as_of_date": report_svc.iso_or_raw(row["as_of_date"]),
    }


@router.get("/status")
async def api_status(request: Request):
    """模块态探针:accounting 模块关也 200(照 routes/steward_routes.py 惯例,前端挂三态)。"""
    _, tenant_id = auth_member(request, _C_VIEW)
    with db.get_cursor_rls(tenant_id) as cur:
        try:
            gate(cur, tenant_id)
            module_on = True
        except PosError:
            module_on = False
    return {"ok": True, "enabled": module_on}


@router.get("/report")
async def api_report(
    request: Request,
    workspace_client_id: int = Query(...),
    date_from: str = Query(...),
    date_to: str = Query(...),
):
    """网页主视图唯一端点:一次请求返回按商品连续排列的完整 13 列表格(groups)。

    2026-08-27 拍板:删除旧「汇总→单品详情」流程的 /summary、/card、/excluded 路由;旧的
    report.summary()/card() 仍保留给 Steward 内部汇报,但不再驱动网页。参考图没有未入账/
    状态/归并/规则/搜索,全部不做 —— 只额外保留已拍板的期初库存录入(/openings)。"""
    user, tid = auth_member(request, _C_VIEW)
    creator = team_access.record_creator_scope(request, user)
    d_from = _parse_date(date_from, field="date_from")
    d_to = _parse_date(date_to, field="date_to")
    with db.get_cursor_rls(tid, commit=False) as cur:
        gate(cur, tid)
        ws = resolve_ws(cur, request, tid, workspace_client_id)
        rows = report_svc.groups(
            cur,
            tenant_id=tid,
            workspace_client_id=ws,
            date_from=d_from,
            date_to=d_to,
            created_by=creator,
        )
    return {"ok": True, "groups": rows}


@router.get("/openings")
async def api_list_openings(request: Request, workspace_client_id: int = Query(...)):
    user, tid = auth_member(request, _C_VIEW)
    creator = team_access.record_creator_scope(request, user)
    with db.get_cursor_rls(tid, commit=False) as cur:
        gate(cur, tid)
        ws = resolve_ws(cur, request, tid, workspace_client_id)
        rows = opening_svc.list_openings(
            cur, tenant_id=tid, workspace_client_id=ws, created_by=creator
        )
    return {"ok": True, "rows": [_public_opening(r) for r in rows]}


@router.post("/openings")
async def api_upsert_openings(
    req: OpeningsIn, request: Request, workspace_client_id: int = Query(...)
):
    user, tid = auth_member(request, _C_MANAGE)
    with db.get_cursor_rls(tid, commit=True) as cur:
        gate(cur, tid)
        ws = resolve_ws(cur, request, tid, workspace_client_id)
        rows = opening_svc.upsert_openings(
            cur,
            tenant_id=tid,
            workspace_client_id=ws,
            rows=[r.model_dump() for r in req.rows],
            created_by=user.get("id"),
        )
    return {"ok": True, "rows": [_public_opening(r) for r in rows]}
