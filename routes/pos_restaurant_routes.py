# -*- coding: utf-8 -*-
"""餐厅 POS 前台/后厨/埋单路由(POS 项目 · PO-R1/R2/R3 · docs/pos/restaurant/02 §2-5)。

薄层:require_tenant(收银员可调)→ 模块守门(pos)→ 账套归属 → 调 services/pos/restaurant。统一 POS 信封。
收银员 token 自带 workspace_client_id/cashier_id;老板调需带 workspace_client_id。写端单事务
(get_cursor_rls commit=True):开台/点单/送厨房/状态流转/埋单全原子。
"""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Query, Request
from pydantic import BaseModel, Field

from core import db
from core.pos_api import PosError, assert_module_enabled, ok, pos_auth, require_workspace
from services.pos.restaurant import (
    checkout as checkout_svc,
    kitchen as kitchen_svc,
    sessions as sessions_svc,
    tables as tables_svc,
)

router = APIRouter(prefix="/api/pos/restaurant", tags=["pos-restaurant"])


def _subject(request: Request) -> tuple[dict, str]:
    user = pos_auth(request)
    tid = user.get("tenant_id")
    if not tid:
        raise PosError("pos.forbidden", 403)
    return user, str(tid)


def _resolve_ws(user: dict, override: Optional[int]) -> int:
    ws = user.get("workspace_client_id") or override
    if ws is None:
        raise PosError("pos.forbidden", 403)
    return int(ws)


def _run(request: Request, ws_override: Optional[int], fn, commit: bool):
    user, tid = _subject(request)
    ws = _resolve_ws(user, ws_override)
    with db.get_cursor_rls(tid, commit=commit) as cur:
        assert_module_enabled(cur, tid, "pos")
        require_workspace(cur, tid, ws)
        return ok(fn(cur, tid, ws, user))


def _created_by(user: dict) -> Optional[str]:
    return str(user["id"]) if user.get("id") else None


# ── 总览 / 开台 ───────────────────────────────────────────────────────
@router.get("/tables")
async def api_overview(
    request: Request,
    workspace_client_id: Optional[int] = Query(None),
    area_id: Optional[int] = Query(None),
):
    return _run(
        request,
        workspace_client_id,
        lambda cur, tid, ws, user: tables_svc.overview(
            cur, tenant_id=tid, workspace_client_id=ws, area_id=area_id
        ),
        commit=False,
    )


class OpenTableRequest(BaseModel):
    workspace_client_id: Optional[int] = None
    party_size: int = Field(1, ge=1)
    service_type: str = "dine_in"


@router.post("/tables/{table_id}/open")
async def api_open_table(table_id: int, req: OpenTableRequest, request: Request):
    return _run(
        request,
        req.workspace_client_id,
        lambda cur, tid, ws, user: sessions_svc.open_session(
            cur,
            tenant_id=tid,
            workspace_client_id=ws,
            table_id=table_id,
            party_size=req.party_size,
            service_type=req.service_type,
            cashier_id=user.get("cashier_id"),
            created_by=_created_by(user),
        ),
        commit=True,
    )


# ── 本桌单 / 点单 ─────────────────────────────────────────────────────
@router.get("/sessions/{session_id}")
async def api_session_detail(
    session_id: str, request: Request, workspace_client_id: Optional[int] = Query(None)
):
    return _run(
        request,
        workspace_client_id,
        lambda cur, tid, ws, user: sessions_svc.session_detail(
            cur, tenant_id=tid, session_id=session_id
        ),
        commit=False,
    )


class OrderLine(BaseModel):
    product_id: str
    qty: float = Field(..., gt=0)
    sell_unit: Optional[str] = None
    line_discount: float = Field(0, ge=0)
    note: Optional[str] = None


class AddLinesRequest(BaseModel):
    workspace_client_id: Optional[int] = None
    lines: List[OrderLine] = Field(..., min_length=1)


@router.post("/sessions/{session_id}/lines")
async def api_add_lines(session_id: str, req: AddLinesRequest, request: Request):
    lines = [m.model_dump() for m in req.lines]
    return _run(
        request,
        req.workspace_client_id,
        lambda cur, tid, ws, user: sessions_svc.add_lines(
            cur,
            tenant_id=tid,
            workspace_client_id=ws,
            session_id=session_id,
            lines=lines,
            created_by=_created_by(user),
        ),
        commit=True,
    )


class UpdateLineRequest(BaseModel):
    workspace_client_id: Optional[int] = None
    qty: Optional[float] = None
    note: Optional[str] = None


@router.patch("/sessions/{session_id}/lines/{line_id}")
async def api_update_line(session_id: str, line_id: str, req: UpdateLineRequest, request: Request):
    return _run(
        request,
        req.workspace_client_id,
        lambda cur, tid, ws, user: sessions_svc.update_draft(
            cur, tenant_id=tid, session_id=session_id, line_id=line_id, qty=req.qty, note=req.note
        ),
        commit=True,
    )


@router.delete("/sessions/{session_id}/lines/{line_id}")
async def api_delete_line(
    session_id: str,
    line_id: str,
    request: Request,
    workspace_client_id: Optional[int] = Query(None),
):
    return _run(
        request,
        workspace_client_id,
        lambda cur, tid, ws, user: sessions_svc.delete_draft(
            cur, tenant_id=tid, session_id=session_id, line_id=line_id
        ),
        commit=True,
    )


# ── 送厨房 / 取消 ─────────────────────────────────────────────────────
class SendKitchenRequest(BaseModel):
    workspace_client_id: Optional[int] = None
    line_ids: Optional[List[str]] = None


@router.post("/sessions/{session_id}/send-kitchen")
async def api_send_kitchen(session_id: str, req: SendKitchenRequest, request: Request):
    return _run(
        request,
        req.workspace_client_id,
        lambda cur, tid, ws, user: sessions_svc.send_kitchen(
            cur,
            tenant_id=tid,
            workspace_client_id=ws,
            session_id=session_id,
            line_ids=req.line_ids,
            created_by=_created_by(user),
        ),
        commit=True,
    )


@router.post("/sessions/{session_id}/cancel")
async def api_cancel_session(
    session_id: str, request: Request, workspace_client_id: Optional[int] = Query(None)
):
    return _run(
        request,
        workspace_client_id,
        lambda cur, tid, ws, user: sessions_svc.cancel_session(
            cur, tenant_id=tid, session_id=session_id
        ),
        commit=True,
    )


# ── 后厨板 / KOT 状态机 ───────────────────────────────────────────────
@router.get("/kitchen")
async def api_kitchen(
    request: Request,
    workspace_client_id: Optional[int] = Query(None),
    late_minutes: int = Query(15, ge=1),
):
    return _run(
        request,
        workspace_client_id,
        lambda cur, tid, ws, user: kitchen_svc.board(
            cur, tenant_id=tid, workspace_client_id=ws, late_minutes=late_minutes
        ),
        commit=False,
    )


class KotStatusRequest(BaseModel):
    workspace_client_id: Optional[int] = None
    status: str


@router.post("/kot/{kot_id}/status")
async def api_kot_status(kot_id: str, req: KotStatusRequest, request: Request):
    return _run(
        request,
        req.workspace_client_id,
        lambda cur, tid, ws, user: kitchen_svc.set_kot_status(
            cur, tenant_id=tid, workspace_client_id=ws, kot_id=kot_id, status=req.status
        ),
        commit=True,
    )


@router.post("/kot/items/{line_id}/status")
async def api_kot_item_status(line_id: str, req: KotStatusRequest, request: Request):
    return _run(
        request,
        req.workspace_client_id,
        lambda cur, tid, ws, user: kitchen_svc.set_item_status(
            cur, tenant_id=tid, line_id=line_id, status=req.status
        ),
        commit=True,
    )


# ── 埋单 ──────────────────────────────────────────────────────────────
@router.post("/sessions/{session_id}/request-bill")
async def api_request_bill(
    session_id: str, request: Request, workspace_client_id: Optional[int] = Query(None)
):
    return _run(
        request,
        workspace_client_id,
        lambda cur, tid, ws, user: checkout_svc.request_bill(
            cur, tenant_id=tid, session_id=session_id
        ),
        commit=True,
    )


@router.get("/sessions/{session_id}/bill")
async def api_bill_preview(
    session_id: str,
    request: Request,
    workspace_client_id: Optional[int] = Query(None),
    mode: str = Query("whole"),
    line_ids: Optional[List[str]] = Query(None),
    ways: Optional[int] = Query(None),
    price_includes_vat: bool = Query(True),
    service_rate: str = Query("10"),
):
    return _run(
        request,
        workspace_client_id,
        lambda cur, tid, ws, user: checkout_svc.bill_preview(
            cur,
            tenant_id=tid,
            session_id=session_id,
            mode=mode,
            line_ids=line_ids,
            ways=ways,
            price_includes_vat=price_includes_vat,
            service_rate=service_rate,
        ),
        commit=False,
    )


class CheckoutPayment(BaseModel):
    method: str
    amount: float
    ref: Optional[str] = None


class HeaderDiscount(BaseModel):
    type: str = "none"
    value: float = 0


class CheckoutRequest(BaseModel):
    workspace_client_id: Optional[int] = None
    client_uuid: Optional[str] = None
    shift_id: Optional[str] = None
    terminal_id: Optional[int] = None
    mode: str = "whole"
    line_ids: Optional[List[str]] = None
    ways: Optional[int] = None
    price_includes_vat: bool = True
    service_rate: str = "10"
    member_client_id: Optional[int] = None
    header_discount: Optional[HeaderDiscount] = None
    payments: List[CheckoutPayment] = Field(default_factory=list)
    sold_at: Optional[str] = None


@router.post("/sessions/{session_id}/checkout")
async def api_checkout(session_id: str, req: CheckoutRequest, request: Request):
    payload = req.model_dump()
    return _run(
        request,
        req.workspace_client_id,
        lambda cur, tid, ws, user: checkout_svc.checkout(
            cur,
            tenant_id=tid,
            workspace_client_id=ws,
            session_id=session_id,
            payload=payload,
            cashier_id=user.get("cashier_id"),
            created_by=_created_by(user),
        ),
        commit=True,
    )
