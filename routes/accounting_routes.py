# -*- coding: utf-8 -*-
"""自动做账接口(docs/accounting/03 契约 · 信封同 POS)。

鉴权:读 = 任意成员(员工只看);写(审/改/作废/撤销重做/手工凭证/科目/映射/设置)= 账号
owner(invited_by is None)。套账解析 fail-closed(缺 → workspace.required)。模块门控
accounting。错误码 4 语键由前端窗口接(本层只返 message_key)。
"""

from __future__ import annotations

from datetime import date
from typing import Optional

from fastapi import APIRouter, Query, Request
from pydantic import BaseModel

from core import db
from core.pos_api import PosError, ok
from routes.accounting_common import auth_member, gate, resolve_ws, uid
from services.accounting import coa_preset, posting, review
from services.accounting import settings as acct_settings
from services.accounting import store as acct_store
from services.accounting import vouchers as jv

router = APIRouter(prefix="/api/accounting", tags=["accounting"])


class ReviewIn(BaseModel):
    account_overrides: Optional[dict] = None
    remember: bool = False


class VoucherPatchIn(BaseModel):
    account_overrides: dict


class ManualLineIn(BaseModel):
    account_id: str
    dr_cr: str
    amount: float
    memo: Optional[str] = None


class ManualVoucherIn(BaseModel):
    voucher_date: date
    description: str
    lines: list[ManualLineIn]


class AccountIn(BaseModel):
    code: Optional[str] = None
    name_zh: Optional[str] = None
    name_th: Optional[str] = None
    acct_type: Optional[str] = None
    parent_id: Optional[str] = None
    is_active: Optional[bool] = None
    sort: Optional[int] = None


class MappingIn(BaseModel):
    role: str
    account_id: str


class SettingsIn(BaseModel):
    auto_post: Optional[bool] = None
    auto_post_threshold: Optional[float] = None
    auto_post_rules: Optional[dict] = None
    accounting_standard: Optional[str] = None
    inventory_method: Optional[str] = None
    base_currency: Optional[str] = None
    start_period: Optional[str] = None


@router.get("/vouchers")
async def api_list_vouchers(
    request: Request,
    period: Optional[str] = Query(None),
    source_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    method: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
    workspace_client_id: Optional[int] = Query(None),
):
    _, tid = auth_member(request, "acct.entry.view")
    with db.get_cursor_rls(tid, commit=False) as cur:
        gate(cur, tid)
        ws = resolve_ws(cur, request, tid, workspace_client_id)
        cur_period = period or date.today().strftime("%Y-%m")
        items = jv.list_vouchers(
            cur,
            tenant_id=tid,
            workspace_client_id=ws,
            period=period,
            source_type=source_type,
            status=status,
            method=method,
            q=q,
        )
        summary = jv.summary(cur, tenant_id=tid, workspace_client_id=ws, period=cur_period)
        return ok({"summary": summary, "items": items})


@router.get("/vouchers/{voucher_id}")
async def api_get_voucher(
    voucher_id: str, request: Request, workspace_client_id: Optional[int] = Query(None)
):
    _, tid = auth_member(request, "acct.entry.view")
    with db.get_cursor_rls(tid, commit=False) as cur:
        gate(cur, tid)
        ws = resolve_ws(cur, request, tid, workspace_client_id)
        voucher = jv.get_voucher(cur, tenant_id=tid, workspace_client_id=ws, voucher_id=voucher_id)
        if voucher is None:
            raise PosError("acct.unexpected", 404, detail="voucher_not_found")
        return ok({"voucher": voucher})


@router.post("/vouchers/manual")
async def api_manual_voucher(
    req: ManualVoucherIn, request: Request, workspace_client_id: Optional[int] = Query(None)
):
    user, tid = auth_member(request, "acct.entry.review")
    with db.get_cursor_rls(tid, commit=True) as cur:
        gate(cur, tid)
        ws = resolve_ws(cur, request, tid, workspace_client_id)
        voucher = posting.create_manual_voucher(
            cur,
            tenant_id=tid,
            workspace_client_id=ws,
            voucher_date=req.voucher_date,
            description=req.description,
            lines=[ln.model_dump() for ln in req.lines],
            created_by=uid(user),
        )
        return ok({"voucher": voucher})


@router.post("/vouchers/{voucher_id}/review")
async def api_review_voucher(
    voucher_id: str,
    req: ReviewIn,
    request: Request,
    workspace_client_id: Optional[int] = Query(None),
):
    user, tid = auth_member(request, "acct.entry.review")
    with db.get_cursor_rls(tid, commit=True) as cur:
        gate(cur, tid)
        ws = resolve_ws(cur, request, tid, workspace_client_id)
        voucher = review.review_voucher(
            cur,
            tenant_id=tid,
            workspace_client_id=ws,
            voucher_id=voucher_id,
            account_overrides=req.account_overrides,
            remember=req.remember,
            reviewed_by=uid(user),
        )
        return ok({"voucher": voucher})


@router.patch("/vouchers/{voucher_id}")
async def api_patch_voucher(
    voucher_id: str,
    req: VoucherPatchIn,
    request: Request,
    workspace_client_id: Optional[int] = Query(None),
):
    """改科目(仅待审 · 金额来自业务单不可改;posted 改走撤销重做/调整分录)。"""
    user, tid = auth_member(request, "acct.entry.review")
    with db.get_cursor_rls(tid, commit=True) as cur:
        gate(cur, tid)
        ws = resolve_ws(cur, request, tid, workspace_client_id)
        voucher = jv.get_voucher(cur, tenant_id=tid, workspace_client_id=ws, voucher_id=voucher_id)
        if voucher is None:
            raise PosError("acct.unexpected", 404, detail="voucher_not_found")
        if voucher["status"] != "pending_review":
            raise PosError("acct.not_pending", 409)
        jv.apply_account_overrides(
            cur,
            tenant_id=tid,
            workspace_client_id=ws,
            voucher_id=voucher_id,
            account_overrides=req.account_overrides,
        )
        return ok(
            {
                "voucher": jv.get_voucher(
                    cur, tenant_id=tid, workspace_client_id=ws, voucher_id=voucher_id
                )
            }
        )


@router.post("/vouchers/{voucher_id}/void")
async def api_void_voucher(
    voucher_id: str, request: Request, workspace_client_id: Optional[int] = Query(None)
):
    _, tid = auth_member(request, "acct.entry.approve")
    with db.get_cursor_rls(tid, commit=True) as cur:
        gate(cur, tid)
        ws = resolve_ws(cur, request, tid, workspace_client_id)
        voucher = posting.void_voucher(
            cur, tenant_id=tid, workspace_client_id=ws, voucher_id=voucher_id
        )
        return ok({"voucher": voucher})


@router.post("/vouchers/{voucher_id}/unpost")
async def api_unpost_voucher(
    voucher_id: str, request: Request, workspace_client_id: Optional[int] = Query(None)
):
    """安全带②:撤销重做(void + 同 source 重判·吃最新映射/记忆)。"""
    user, tid = auth_member(request, "acct.entry.approve")
    with db.get_cursor_rls(tid, commit=True) as cur:
        gate(cur, tid)
        ws = resolve_ws(cur, request, tid, workspace_client_id)
        voucher = posting.unpost_voucher(
            cur, tenant_id=tid, workspace_client_id=ws, voucher_id=voucher_id, created_by=uid(user)
        )
        return ok({"voucher": voucher})


@router.get("/review")
async def api_review_queue(
    request: Request,
    period: Optional[str] = Query(None),
    workspace_client_id: Optional[int] = Query(None),
):
    _, tid = auth_member(request, "acct.entry.review")
    with db.get_cursor_rls(tid, commit=False) as cur:
        gate(cur, tid)
        ws = resolve_ws(cur, request, tid, workspace_client_id)
        items = review.list_pending(cur, tenant_id=tid, workspace_client_id=ws, period=period)
        return ok({"count": len(items), "items": items})


@router.get("/accounts")
async def api_list_accounts(
    request: Request,
    type: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
    workspace_client_id: Optional[int] = Query(None),
):
    _, tid = auth_member(request, "acct.entry.view")
    # commit=True:首次访问顺手 seed 预置科目(屏3 永不空态)
    with db.get_cursor_rls(tid, commit=True) as cur:
        gate(cur, tid)
        ws = resolve_ws(cur, request, tid, workspace_client_id)
        coa_preset.ensure_seeded(cur, tenant_id=tid, workspace_client_id=ws)
        items = acct_store.list_accounts(
            cur, tenant_id=tid, workspace_client_id=ws, acct_type=type, q=q
        )
        return ok({"accounts": items})


@router.post("/accounts")
async def api_create_account(
    req: AccountIn, request: Request, workspace_client_id: Optional[int] = Query(None)
):
    _, tid = auth_member(request, "acct.coa.manage")
    with db.get_cursor_rls(tid, commit=True) as cur:
        gate(cur, tid)
        ws = resolve_ws(cur, request, tid, workspace_client_id)
        coa_preset.ensure_seeded(cur, tenant_id=tid, workspace_client_id=ws)
        account = acct_store.create_account(
            cur, tenant_id=tid, workspace_client_id=ws, data=req.model_dump(exclude_none=True)
        )
        return ok({"account": account})


@router.patch("/accounts/{account_id}")
async def api_update_account(
    account_id: str,
    req: AccountIn,
    request: Request,
    workspace_client_id: Optional[int] = Query(None),
):
    _, tid = auth_member(request, "acct.coa.manage")
    with db.get_cursor_rls(tid, commit=True) as cur:
        gate(cur, tid)
        ws = resolve_ws(cur, request, tid, workspace_client_id)
        account = acct_store.update_account(
            cur,
            tenant_id=tid,
            workspace_client_id=ws,
            account_id=account_id,
            data=req.model_dump(exclude_unset=True),
        )
        return ok({"account": account})


@router.get("/mappings")
async def api_list_mappings(request: Request, workspace_client_id: Optional[int] = Query(None)):
    _, tid = auth_member(request, "acct.entry.view")
    with db.get_cursor_rls(tid, commit=True) as cur:
        gate(cur, tid)
        ws = resolve_ws(cur, request, tid, workspace_client_id)
        coa_preset.ensure_seeded(cur, tenant_id=tid, workspace_client_id=ws)
        return ok(
            {"mappings": acct_store.list_mappings(cur, tenant_id=tid, workspace_client_id=ws)}
        )


@router.put("/mappings")
async def api_set_mapping(
    req: MappingIn, request: Request, workspace_client_id: Optional[int] = Query(None)
):
    _, tid = auth_member(request, "acct.coa.manage")
    with db.get_cursor_rls(tid, commit=True) as cur:
        gate(cur, tid)
        ws = resolve_ws(cur, request, tid, workspace_client_id)
        acct_store.set_mapping(
            cur, tenant_id=tid, workspace_client_id=ws, role=req.role, account_id=req.account_id
        )
        return ok(
            {"mappings": acct_store.list_mappings(cur, tenant_id=tid, workspace_client_id=ws)}
        )


@router.get("/settings")
async def api_get_settings(request: Request, workspace_client_id: Optional[int] = Query(None)):
    _, tid = auth_member(request, "acct.entry.view")
    with db.get_cursor_rls(tid, commit=False) as cur:
        gate(cur, tid)
        ws = resolve_ws(cur, request, tid, workspace_client_id)
        return ok(
            {"settings": acct_settings.get_settings(cur, tenant_id=tid, workspace_client_id=ws)}
        )


@router.put("/settings")
async def api_update_settings(
    req: SettingsIn, request: Request, workspace_client_id: Optional[int] = Query(None)
):
    _, tid = auth_member(request, "acct.settings.manage")
    with db.get_cursor_rls(tid, commit=True) as cur:
        gate(cur, tid)
        ws = resolve_ws(cur, request, tid, workspace_client_id)
        settings = acct_settings.update_settings(
            cur, tenant_id=tid, workspace_client_id=ws, data=req.model_dump(exclude_unset=True)
        )
        return ok({"settings": settings})


@router.get("/learned")
async def api_list_learned(request: Request, workspace_client_id: Optional[int] = Query(None)):
    """可见规则(智能不黑箱):review_learned 学到的全部列出。"""
    _, tid = auth_member(request, "acct.entry.view")
    with db.get_cursor_rls(tid, commit=False) as cur:
        gate(cur, tid)
        ws = resolve_ws(cur, request, tid, workspace_client_id)
        return ok({"items": review.list_learned(cur, tenant_id=tid, workspace_client_id=ws)})


@router.delete("/learned/{learned_id}")
async def api_delete_learned(
    learned_id: str, request: Request, workspace_client_id: Optional[int] = Query(None)
):
    _, tid = auth_member(request, "acct.coa.manage")
    with db.get_cursor_rls(tid, commit=True) as cur:
        gate(cur, tid)
        ws = resolve_ws(cur, request, tid, workspace_client_id)
        review.delete_learned(cur, tenant_id=tid, workspace_client_id=ws, learned_id=learned_id)
        return ok({})
