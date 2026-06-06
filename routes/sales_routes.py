# -*- coding: utf-8 -*-
"""销项单据路由(PO-4 · docs/sales-module/docs/13)。

薄层:鉴权 + 请求整形 + 状态错误映射(404/409);开票业务在 services/sales/document.py。
开票=钱+合规高敏:草稿可改,正式开出走事务取连号+冻结,开出后改→409。金额按
docs/04 一律字符串化传输(前端不做 float 运算)。
"""

from __future__ import annotations

import logging
from datetime import date
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response
from pydantic import BaseModel, Field

from core import db
from core.auth import get_current_user_from_request
from services.sales import buyer as buyer_mod
from services.sales import credit_note
from services.sales import dates as sales_dates
from services.sales import document as doc_svc
from services.sales import numbering
from services.sales import pdf as pdf_svc
from services.sales import seller_profile

logger = logging.getLogger("mr-pilot")
router = APIRouter(prefix="/api/sales/documents", tags=["sales-documents"])

_ERR_HTTP = {
    "not_found": 404,
    "not_draft": 409,
    "already_void": 409,
    "original_not_found": 404,
    "original_not_issued": 409,
    "bad_note_type": 400,
    # 买方完整性 / 收款闸:不合规请求,语义错误(422),不占号。
    "buyer_incomplete": 422,
    "buyer_tax_id_invalid": 422,
    "buyer_branch_required": 422,
    "buyer_branch_no_invalid": 422,
    "payment_required": 422,
}


def _require_tenant(request: Request) -> tuple[str, Optional[str]]:
    user = get_current_user_from_request(request)
    tid = user.get("tenant_id") if user else None
    if not tid:
        raise HTTPException(400, detail="sales.tenant_required")
    return str(tid), (str(user["id"]) if user and user.get("id") else None)


class LineIn(BaseModel):
    description: str = Field(..., min_length=1, max_length=500)
    product_id: Optional[str] = Field(None, max_length=64)
    qty: float = Field(1, ge=0)
    unit_price: float = Field(0, ge=0)
    discount: float = Field(0, ge=0)
    discount_pct: Optional[float] = Field(None, ge=0, le=100)
    vat_applicable: bool = True


class BuyerIn(BaseModel):
    """买方块(docs/15)。type 决定 tax_id 语义与分店是否适用;后端再归一化+校验。"""

    type: str = Field("company", max_length=20)
    name: Optional[str] = Field(None, max_length=300)
    address: Optional[str] = Field(None, max_length=500)
    tax_id: Optional[str] = Field(None, max_length=40)
    branch_type: Optional[str] = Field(None, max_length=10)
    branch_no: Optional[str] = Field(None, max_length=10)


class PaymentIn(BaseModel):
    """收款块(docs/16 §J2)。收据/合并单开出前必须已收款。"""

    status: str = Field("unpaid", max_length=12)
    paid_amount: float = Field(0, ge=0)
    method: Optional[str] = Field(None, max_length=20)
    date: Optional[str] = Field(None, description="YYYY-MM-DD")


class DocumentIn(BaseModel):
    doc_type: str = Field("tax_invoice", max_length=40)
    client_id: Optional[int] = None
    seller_workspace_client_id: Optional[int] = None
    currency: str = Field("THB", max_length=8)
    vat_rate: float = Field(7, ge=0, le=100)
    wht_rate: float = Field(0, ge=0, le=100)
    header_discount_amount: float = Field(0, ge=0)
    header_discount_pct: float = Field(0, ge=0, le=100)
    due_date: Optional[str] = Field(None, description="YYYY-MM-DD · 账期到期日")
    payment_terms: Optional[str] = Field(None, max_length=200)
    lines: list[LineIn] = Field(..., min_length=1)
    buyer: Optional[BuyerIn] = None
    payment: Optional[PaymentIn] = None


class IssueIn(BaseModel):
    prefix: Optional[str] = Field(None, max_length=20)
    reset: str = Field("yearly")
    issue_date: Optional[str] = Field(None, description="YYYY-MM-DD · 默认今天")


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
        "wht_amount": _m(d.get("wht_amount")),
        "grand_total": _m(d.get("grand_total")),
        "issued_at": d["issued_at"].isoformat() if d.get("issued_at") else None,
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
        "created_at": d["created_at"].isoformat() if d.get("created_at") else None,
        "lines": [_line_out(ln) for ln in d.get("lines", [])],
    }


def _fail(code: str):
    raise HTTPException(_ERR_HTTP.get(code, 400), detail=f"sales.{code}")


def _pdf_parties(cur, tid: str, doc: dict):
    """PDF 双方来源:已开出从冻结快照取(docs/16 §A · 不实时 join);草稿实时组合。"""
    snap = doc.get("parties_snapshot")
    if snap:
        return snap.get("seller"), snap.get("buyer")
    seller = None
    if doc.get("seller_workspace_client_id"):
        seller = seller_profile.get_seller(
            cur, tenant_id=tid, workspace_client_id=doc["seller_workspace_client_id"]
        )
    if doc.get("buyer_type"):
        buyer = buyer_mod.from_row(doc)
    elif doc.get("client_id"):  # 旧单据回退:买方来自 clients
        buyer = seller_profile.get_buyer(cur, tenant_id=tid, client_id=doc["client_id"])
    else:
        buyer = None
    return seller, buyer


@router.get("")
async def api_list_documents(
    request: Request, status: Optional[str] = None, client_id: Optional[int] = None
):
    tid, _ = _require_tenant(request)
    with db.get_cursor_rls(tid) as cur:
        rows = doc_svc.list_documents(cur, tenant_id=tid, status=status, client_id=client_id)
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
async def api_document_pdf(doc_id: str, request: Request, page: str = "A4", copy: str = "original"):
    """生成合规 PDF(卖方账套 + 买方客户 + 明细 · VAT 分列 · 连号)。

    page=A4|A5(§E1)· copy=original|copy(正本给买方 / 副本自留 · §E2)。
    """
    tid, _ = _require_tenant(request)
    with db.get_cursor_rls(tid) as cur:
        doc = doc_svc.get_document(cur, tenant_id=tid, doc_id=doc_id)
        if not doc:
            _fail("not_found")
        seller, buyer = _pdf_parties(cur, tid, doc)
    body = _doc_out(doc)
    # pdf 收款区读扁平字段;_doc_out 把收款放在嵌套块,这里补扁平给渲染层。
    body["payment_status"] = doc.get("payment_status")
    body["payment_method"] = doc.get("payment_method")
    body["paid_amount"] = _m(doc.get("paid_amount"))
    body["payment_date"] = doc["payment_date"].isoformat() if doc.get("payment_date") else None
    data = pdf_svc.render_invoice_pdf(body, seller, buyer, page=page, copy_kind=copy)
    suffix = "" if copy == "original" else "_copy"
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
            due_date=_opt_date(p.get("due_date")),
            payment_terms=p.get("payment_terms"),
        )
        if err:
            _fail(err)
        doc = doc_svc.get_document(cur, tenant_id=tid, doc_id=doc_id)
    return {"ok": True, "document": _doc_out(doc)}


@router.post("/{doc_id}/issue")
async def api_issue_document(doc_id: str, req: IssueIn, request: Request):
    tid, _ = _require_tenant(request)
    p = _dump(req)
    on = _resolve_issue_date(p.get("issue_date"))
    reset = p.get("reset") or numbering.RESET_YEARLY
    with db.get_cursor_rls(tid, commit=True) as cur:
        doc, err = doc_svc.issue_document(
            cur, tenant_id=tid, doc_id=doc_id, prefix=p.get("prefix"), reset=reset, on=on
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


class NoteIn(BaseModel):
    reason: Optional[str] = Field(None, max_length=500)
    vat_rate: float = Field(7, ge=0, le=100)
    wht_rate: float = Field(0, ge=0, le=100)
    lines: list[LineIn] = Field(..., min_length=1)
    prefix: Optional[str] = Field(None, max_length=20)
    reset: str = Field("yearly")
    issue_date: Optional[str] = Field(None, description="YYYY-MM-DD · 默认今天")


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
