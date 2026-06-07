# -*- coding: utf-8 -*-
"""销项单据路由(PO-4 · docs/sales-module/docs/13)。

薄层:鉴权 + 请求整形 + 状态错误映射(404/409);开票业务在 services/sales/document.py。
开票=钱+合规高敏:草稿可改,正式开出走事务取连号+冻结,开出后改→409。金额按
docs/04 一律字符串化传输(前端不做 float 运算)。
"""

from __future__ import annotations

import logging
from datetime import date
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response

from core import db
from core.route_helpers import _require_owner_or_super, _require_tenant
from routes.sales_schemas import ConvertIn, DocumentIn, IssueIn, NoteIn, RejectIn
from services.sales import approval as approval_svc
from services.sales import credit_note
from services.sales import dates as sales_dates
from services.sales import document as doc_svc
from services.sales import numbering
from services.sales import promptpay as promptpay_svc
from services.sales import quotation as quotation_svc
from services.sales import render as sales_render
from services.sales import seller_profile
from services.sales import settings as settings_svc

logger = logging.getLogger("mr-pilot")
router = APIRouter(prefix="/api/sales/documents", tags=["sales-documents"])

_ERR_HTTP = {
    "not_found": 404,
    "not_draft": 409,
    "already_void": 409,
    "original_not_found": 404,
    "original_not_issued": 409,
    "bad_note_type": 400,
    # 审批工作流(§F):草稿在审批模式下不能直开 / 单据不在待审状态。
    "approval_required": 409,
    "not_pending": 409,
    # 买方完整性 / 收款闸:不合规请求,语义错误(422),不占号。
    "buyer_incomplete": 422,
    "buyer_tax_id_invalid": 422,
    "buyer_branch_required": 422,
    "buyer_branch_no_invalid": 422,
    "payment_required": 422,
    # 报价转换(§L3)/ PromptPay(§L1)。
    "bad_target_type": 400,
    "not_a_quotation": 409,
    "promptpay_unset": 422,
    "already_paid": 409,
}


def _dump(req) -> dict:
    return req.model_dump() if hasattr(req, "model_dump") else req.dict()


def _m(v) -> Optional[str]:
    return str(v) if v is not None else None


def _payment_payload(pay: Optional[dict]) -> Optional[dict]:
    """收款块:把 date 字符串解析成 date(无效 422),其余透传给业务层归一化。"""
    if not pay:
        return None
    d = None
    if pay.get("date"):
        try:
            d = date.fromisoformat(pay["date"])
        except ValueError:
            raise HTTPException(422, detail="sales.bad_payment_date")
    return {
        "status": pay.get("status"),
        "paid_amount": pay.get("paid_amount"),
        "method": pay.get("method"),
        "date": d,
    }


def _opt_date(raw: Optional[str], code: str = "bad_due_date") -> Optional[date]:
    if not raw:
        return None
    try:
        return date.fromisoformat(raw)
    except ValueError:
        raise HTTPException(422, detail=f"sales.{code}")


def _resolve_issue_date(raw: Optional[str]) -> date:
    """开票日:给了就用(校 ISO),否则默认曼谷当天;再过未来/跨期护栏(§G)。"""
    if raw:
        try:
            on = date.fromisoformat(raw)
        except ValueError:
            raise HTTPException(422, detail="sales.bad_issue_date")
    else:
        on = sales_dates.bangkok_today()
    err = sales_dates.validate_issue_date(on)
    if err:
        raise HTTPException(422, detail=f"sales.{err}")
    return on


def _line_out(ln: dict) -> dict:
    return {
        "line_no": ln.get("line_no"),
        "product_id": str(ln["product_id"]) if ln.get("product_id") else None,
        "description": ln.get("description"),
        "qty": _m(ln.get("qty")),
        "unit_price": _m(ln.get("unit_price")),
        "discount": _m(ln.get("discount")),
        "discount_pct": _m(ln.get("discount_pct")),
        "vat_applicable": bool(ln.get("vat_applicable")),
        "line_total": _m(ln.get("line_total")),
    }


def _doc_out(d: dict) -> dict:
    return {
        "id": str(d["id"]),
        "doc_type": d.get("doc_type"),
        "doc_number": d.get("doc_number"),
        "client_id": int(d["client_id"]) if d.get("client_id") is not None else None,
        "seller_workspace_client_id": (
            int(d["seller_workspace_client_id"])
            if d.get("seller_workspace_client_id") is not None
            else None
        ),
        "issue_date": d["issue_date"].isoformat() if d.get("issue_date") else None,
        "status": d.get("status"),
        "currency": d.get("currency"),
        "subtotal": _m(d.get("subtotal")),
        "discount_total": _m(d.get("discount_total")),
        "header_discount_amount": _m(d.get("header_discount_amount")),
        "header_discount_pct": _m(d.get("header_discount_pct")),
        "vat_rate": _m(d.get("vat_rate")),
        "vat_amount": _m(d.get("vat_amount")),
        "price_includes_vat": bool(d.get("price_includes_vat")),
        "wht_rate": _m(d.get("wht_rate")),
        "wht_amount": _m(d.get("wht_amount")),
        "grand_total": _m(d.get("grand_total")),
        "issued_at": d["issued_at"].isoformat() if d.get("issued_at") else None,
        "pdf_sha256": d.get("pdf_sha256"),
        "references_document_id": (
            str(d["references_document_id"]) if d.get("references_document_id") else None
        ),
        "reference_reason": d.get("reference_reason"),
        "due_date": d["due_date"].isoformat() if d.get("due_date") else None,
        "payment_terms": d.get("payment_terms"),
        "buyer": {
            "type": d.get("buyer_type"),
            "name": d.get("buyer_name"),
            "address": d.get("buyer_address"),
            "tax_id": d.get("buyer_tax_id"),
            "branch_type": d.get("buyer_branch_type"),
            "branch_no": d.get("buyer_branch_no"),
        },
        "payment": {
            "status": d.get("payment_status"),
            "paid_amount": _m(d.get("paid_amount")),
            "method": d.get("payment_method"),
            "date": d["payment_date"].isoformat() if d.get("payment_date") else None,
        },
        "approval": {
            "approved_by": d.get("approved_by"),
            "approved_at": d["approved_at"].isoformat() if d.get("approved_at") else None,
            "rejected_reason": d.get("rejected_reason"),
        },
        "created_at": d["created_at"].isoformat() if d.get("created_at") else None,
        "lines": [_line_out(ln) for ln in d.get("lines", [])],
    }


def _fail(code: str):
    raise HTTPException(_ERR_HTTP.get(code, 400), detail=f"sales.{code}")


@router.get("")
async def api_list_documents(
    request: Request,
    status: Optional[str] = None,
    client_id: Optional[int] = None,
    q: Optional[str] = None,
):
    tid, _ = _require_tenant(request)
    with db.get_cursor_rls(tid) as cur:
        rows = doc_svc.list_documents(cur, tenant_id=tid, status=status, client_id=client_id, q=q)
    return {"documents": [_doc_out(r) for r in rows]}


@router.post("")
async def api_create_document(req: DocumentIn, request: Request):
    tid, uid = _require_tenant(request)
    p = _dump(req)
    with db.get_cursor_rls(tid, commit=True) as cur:
        doc = doc_svc.create_draft(
            cur,
            tenant_id=tid,
            created_by=uid,
            doc_type=p["doc_type"],
            client_id=p["client_id"],
            seller_workspace_client_id=p["seller_workspace_client_id"],
            currency=p["currency"],
            vat_rate=p["vat_rate"],
            wht_rate=p["wht_rate"],
            lines=p["lines"],
            buyer=p.get("buyer"),
            payment=_payment_payload(p.get("payment")),
            header_discount_amount=p["header_discount_amount"],
            header_discount_pct=p["header_discount_pct"],
            price_includes_vat=p["price_includes_vat"],
            due_date=_opt_date(p.get("due_date")),
            payment_terms=p.get("payment_terms"),
        )
    return {"ok": True, "document": _doc_out(doc)}


@router.get("/{doc_id}")
async def api_get_document(doc_id: str, request: Request):
    tid, _ = _require_tenant(request)
    with db.get_cursor_rls(tid) as cur:
        doc = doc_svc.get_document(cur, tenant_id=tid, doc_id=doc_id)
    if not doc:
        _fail("not_found")
    return {"document": _doc_out(doc)}


@router.get("/{doc_id}/pdf")
async def api_document_pdf(
    doc_id: str,
    request: Request,
    page: str = "A4",
    copy: str = "original",
    copies_layout: str = "separate",
):
    """生成合规 PDF(卖方账套 + 买方客户 + 明细 · VAT 分列 · 连号)。

    page=A4|A5(§E1)· copy=original|copy(正本给买方 / 副本自留 · §E2)·
    copies_layout=separate|two_up(省纸:正副本同页 · §E2)。
    """
    tid, _ = _require_tenant(request)
    with db.get_cursor_rls(tid) as cur:
        doc = doc_svc.get_document(cur, tenant_id=tid, doc_id=doc_id)
        if not doc:
            _fail("not_found")
        data = sales_render.build_pdf(
            cur, tenant_id=tid, doc=doc, page=page, copy_kind=copy, copies_layout=copies_layout
        )
    suffix = "_set" if copies_layout == "two_up" else ("" if copy == "original" else "_copy")
    filename = (doc.get("doc_number") or "document").replace("/", "_") + suffix
    return Response(
        content=data,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{filename}.pdf"'},
    )


@router.patch("/{doc_id}")
async def api_update_document(doc_id: str, req: DocumentIn, request: Request):
    tid, _ = _require_tenant(request)
    p = _dump(req)
    with db.get_cursor_rls(tid, commit=True) as cur:
        err = doc_svc.update_draft(
            cur,
            tenant_id=tid,
            doc_id=doc_id,
            doc_type=p["doc_type"],
            client_id=p["client_id"],
            seller_workspace_client_id=p["seller_workspace_client_id"],
            currency=p["currency"],
            vat_rate=p["vat_rate"],
            wht_rate=p["wht_rate"],
            lines=p["lines"],
            buyer=p.get("buyer"),
            payment=_payment_payload(p.get("payment")),
            header_discount_amount=p["header_discount_amount"],
            header_discount_pct=p["header_discount_pct"],
            price_includes_vat=p["price_includes_vat"],
            due_date=_opt_date(p.get("due_date")),
            payment_terms=p.get("payment_terms"),
        )
        if err:
            _fail(err)
        doc = doc_svc.get_document(cur, tenant_id=tid, doc_id=doc_id)
    return {"ok": True, "document": _doc_out(doc)}


@router.post("/{doc_id}/issue")
async def api_issue_document(doc_id: str, req: IssueIn, request: Request):
    """正式开出。连号前缀/重置/起始号与审批模式取账套设置(§M7)默认,请求可覆盖前缀/重置/日期。
    审批模式开启(!=none)时草稿不能直开,返 approval_required(走提交→审批)。"""
    tid, _ = _require_tenant(request)
    p = _dump(req)
    on = _resolve_issue_date(p.get("issue_date"))
    with db.get_cursor_rls(tid, commit=True) as cur:
        st = settings_svc.get_settings(cur, tenant_id=tid)
        doc, err = doc_svc.issue_document(
            cur,
            tenant_id=tid,
            doc_id=doc_id,
            prefix=p.get("prefix") or st["number_prefix"],
            reset=p.get("reset") or st["number_reset"],
            on=on,
            start=st["number_start"],
            approval_mode=st["approval_mode"],
        )
        if err:
            _fail(err)
    return {"ok": True, "document": _doc_out(doc)}


@router.post("/{doc_id}/void")
async def api_void_document(doc_id: str, request: Request):
    tid, _ = _require_tenant(request)
    with db.get_cursor_rls(tid, commit=True) as cur:
        err = doc_svc.void_document(cur, tenant_id=tid, doc_id=doc_id)
        if err:
            _fail(err)
    return {"ok": True}


@router.delete("/{doc_id}")
async def api_delete_draft(doc_id: str, request: Request):
    """删除草稿(仅草稿可删 · 未占连号)。已开/已作废 → 409 not_draft。"""
    tid, _ = _require_tenant(request)
    with db.get_cursor_rls(tid, commit=True) as cur:
        err = doc_svc.delete_draft(cur, tenant_id=tid, doc_id=doc_id)
        if err:
            _fail(err)
    return {"ok": True}


@router.post("/{doc_id}/submit")
async def api_submit_for_approval(doc_id: str, request: Request):
    """提交审批(§F):草稿/被驳回 → 待审批。任意成员可提交。"""
    tid, _ = _require_tenant(request)
    with db.get_cursor_rls(tid, commit=True) as cur:
        err = approval_svc.submit_for_approval(cur, tenant_id=tid, doc_id=doc_id)
        if err:
            _fail(err)
        doc = doc_svc.get_document(cur, tenant_id=tid, doc_id=doc_id)
    return {"ok": True, "document": _doc_out(doc)}


@router.post("/{doc_id}/approve")
async def api_approve_document(doc_id: str, req: IssueIn, request: Request):
    """审批通过(§F · 仅 owner/超管):待审批 → 取号开出 + 记审批人。"""
    user = _require_owner_or_super(request)
    tid, uid = _require_tenant(request)
    p = _dump(req)
    on = _resolve_issue_date(p.get("issue_date"))
    approver = str(user.get("id")) if user.get("id") else uid
    with db.get_cursor_rls(tid, commit=True) as cur:
        st = settings_svc.get_settings(cur, tenant_id=tid)
        doc, err = approval_svc.approve(
            cur,
            tenant_id=tid,
            doc_id=doc_id,
            approver=approver,
            prefix=p.get("prefix") or st["number_prefix"],
            reset=p.get("reset") or st["number_reset"],
            on=on,
            start=st["number_start"],
        )
        if err:
            _fail(err)
    return {"ok": True, "document": _doc_out(doc)}


@router.post("/{doc_id}/reject")
async def api_reject_document(doc_id: str, req: RejectIn, request: Request):
    """驳回(§F · 仅 owner/超管):待审批 → 驳回(留理由),改后回到草稿。"""
    _require_owner_or_super(request)
    tid, _ = _require_tenant(request)
    with db.get_cursor_rls(tid, commit=True) as cur:
        err = approval_svc.reject(
            cur, tenant_id=tid, doc_id=doc_id, reason=_dump(req).get("reason")
        )
        if err:
            _fail(err)
        doc = doc_svc.get_document(cur, tenant_id=tid, doc_id=doc_id)
    return {"ok": True, "document": _doc_out(doc)}


def _make_note(doc_id: str, req: NoteIn, request: Request, note_type: str) -> dict:
    tid, uid = _require_tenant(request)
    p = _dump(req)
    on = _resolve_issue_date(p.get("issue_date"))
    with db.get_cursor_rls(tid, commit=True) as cur:
        note, err = credit_note.create_note(
            cur,
            tenant_id=tid,
            created_by=uid,
            original_id=doc_id,
            note_type=note_type,
            reason=p.get("reason"),
            lines=p["lines"],
            vat_rate=p["vat_rate"],
            wht_rate=p["wht_rate"],
            prefix=p.get("prefix"),
            reset=p.get("reset") or numbering.RESET_YEARLY,
            on=on,
        )
        if err:
            _fail(err)
    return {"ok": True, "document": _doc_out(note)}


@router.post("/{doc_id}/credit-note")
async def api_credit_note(doc_id: str, req: NoteIn, request: Request):
    """红冲 ใบลดหนี้:引用已开出原单 · 自身连号开出。"""
    return _make_note(doc_id, req, request, "credit_note")


@router.post("/{doc_id}/debit-note")
async def api_debit_note(doc_id: str, req: NoteIn, request: Request):
    """补开 ใบเพิ่มหนี้:引用已开出原单 · 自身连号开出。"""
    return _make_note(doc_id, req, request, "debit_note")


@router.post("/{doc_id}/convert")
async def api_convert_quotation(doc_id: str, req: ConvertIn, request: Request):
    """报价单 → 发票转换(§L3):复制成目标类型草稿,引用原报价单(报价单本身不变)。"""
    tid, uid = _require_tenant(request)
    target = _dump(req)["target_doc_type"]
    with db.get_cursor_rls(tid, commit=True) as cur:
        doc, err = quotation_svc.convert_quotation(
            cur, tenant_id=tid, created_by=uid, quote_id=doc_id, target_doc_type=target
        )
        if err:
            _fail(err)
    return {"ok": True, "document": _doc_out(doc)}


@router.get("/{doc_id}/promptpay-qr")
async def api_promptpay_qr(doc_id: str, request: Request):
    """PromptPay 付款二维码 PNG(§L1):金额=应付额(partial 取未收余额)。已收款不出。"""
    tid, _ = _require_tenant(request)
    with db.get_cursor_rls(tid) as cur:
        doc = doc_svc.get_document(cur, tenant_id=tid, doc_id=doc_id)
        if not doc:
            _fail("not_found")
        if (doc.get("payment_status") or "unpaid") == "paid":
            _fail("already_paid")
        sid = doc.get("seller_workspace_client_id")
        seller = (
            seller_profile.get_seller(cur, tenant_id=tid, workspace_client_id=sid) if sid else None
        )
    promptpay_id = (seller or {}).get("promptpay_id")
    if not promptpay_id:
        _fail("promptpay_unset")
    grand = Decimal(str(doc.get("grand_total") or 0))
    paid = Decimal(str(doc.get("paid_amount") or 0))
    amount = grand - paid if doc.get("payment_status") == "partial" else grand
    png = promptpay_svc.build_qr_png(promptpay_id, f"{amount:.2f}")
    return Response(content=png, media_type="image/png", headers={"Cache-Control": "no-store"})
