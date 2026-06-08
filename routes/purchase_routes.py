# -*- coding: utf-8 -*-
"""商户采购单据路由 · 建/列/详/改/入账/付款/作废/删 + 行↔商品(docs/purchasing/02 §1-2)。

录入(建/列/详/改草稿/入账/删草稿/匹配商品)= 任意成员;审付款/作废 = 账号 owner。
套账隔离 + expense 门控走 purchase_common。薄层:解析上下文 → 游标(写端 commit)→ 调
services/purchase{docs,posting}。统一 POS 信封。intake 分流 / 凭据 / 汇总见后续路由文件。
"""

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Query, Request, Response
from pydantic import BaseModel, Field

from core import db
from core.pos_api import PosError, ok
from routes.purchase_common import auth_member, auth_owner, gate, resolve_ws, uid as _uid
from services.purchase import documents as documents_svc
from services.purchase import docs as docs_svc
from services.purchase import posting as posting_svc
from services.purchase import reports as reports_svc
from services.purchase import settings as settings_svc

router = APIRouter(prefix="/api/purchase", tags=["purchase-docs"])


class DocIn(BaseModel):
    workspace_client_id: Optional[int] = None
    doc_kind: str = "expense"
    supplier: Optional[dict] = None
    doc_no: Optional[str] = None
    doc_date: Optional[str] = None
    has_vat: Optional[bool] = None
    currency: str = "THB"
    fx_rate: float = 1
    requester: Optional[str] = None
    requester_user_id: Optional[str] = None
    approval_status: Optional[str] = None
    due_date: Optional[str] = None
    source: Optional[str] = None
    lines: list[dict[str, Any]] = Field(default_factory=list)
    discount_total: float = 0
    rounding: float = 0
    grand_total: Optional[float] = None
    ocr_raw: Optional[dict] = None


class PostIn(BaseModel):
    workspace_client_id: Optional[int] = None
    auto_stock_in: Optional[bool] = None


class PayIn(BaseModel):
    workspace_client_id: Optional[int] = None
    amount: float = 0
    method: Optional[str] = None
    date: Optional[str] = None
    note: Optional[str] = None


class MatchIn(BaseModel):
    workspace_client_id: Optional[int] = None
    product_id: Optional[str] = None
    create: Optional[dict] = None


@router.post("/docs")
async def api_create_doc(req: DocIn, request: Request):
    user, tid = auth_member(request)
    with db.get_cursor_rls(tid, commit=True) as cur:
        gate(cur, tid)
        ws = resolve_ws(cur, request, tid, req.workspace_client_id)
        cfg = settings_svc.get_settings(cur, tenant_id=tid, workspace_client_id=ws)
        res = docs_svc.create_doc(
            cur,
            tenant_id=tid,
            workspace_client_id=ws,
            created_by=_uid(user),
            data=req.model_dump(),
            settings=cfg,
            status="draft",
        )
        return ok(res)


@router.get("/docs")
async def api_list_docs(
    request: Request,
    workspace_client_id: Optional[int] = Query(None),
    kind: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    unpaid: bool = Query(False),
    q: Optional[str] = Query(None),
):
    _, tid = auth_member(request)
    with db.get_cursor_rls(tid, commit=False) as cur:
        gate(cur, tid)
        ws = resolve_ws(cur, request, tid, workspace_client_id)
        return ok(
            docs_svc.list_docs(
                cur,
                tenant_id=tid,
                workspace_client_id=ws,
                kind=kind,
                status=status,
                unpaid=unpaid,
                q=q,
            )
        )


@router.get("/docs/{doc_id}")
async def api_get_doc(
    doc_id: str, request: Request, workspace_client_id: Optional[int] = Query(None)
):
    _, tid = auth_member(request)
    with db.get_cursor_rls(tid, commit=False) as cur:
        gate(cur, tid)
        ws = resolve_ws(cur, request, tid, workspace_client_id)
        res = docs_svc.get_doc(cur, tenant_id=tid, workspace_client_id=ws, doc_id=doc_id)
        if res is None:
            raise PosError("purchase.unexpected", 404)
        return ok(res)


@router.put("/docs/{doc_id}")
async def api_update_doc(doc_id: str, req: DocIn, request: Request):
    user, tid = auth_member(request)
    with db.get_cursor_rls(tid, commit=True) as cur:
        gate(cur, tid)
        ws = resolve_ws(cur, request, tid, req.workspace_client_id)
        cfg = settings_svc.get_settings(cur, tenant_id=tid, workspace_client_id=ws)
        res = docs_svc.update_draft(
            cur,
            tenant_id=tid,
            workspace_client_id=ws,
            created_by=_uid(user),
            doc_id=doc_id,
            data=req.model_dump(),
            settings=cfg,
        )
        return ok(res)


@router.post("/docs/{doc_id}/post")
async def api_post_doc(doc_id: str, req: PostIn, request: Request):
    user, tid = auth_member(request)
    with db.get_cursor_rls(tid, commit=True) as cur:
        gate(cur, tid)
        ws = resolve_ws(cur, request, tid, req.workspace_client_id)
        cfg = settings_svc.get_settings(cur, tenant_id=tid, workspace_client_id=ws)
        auto = req.auto_stock_in if req.auto_stock_in is not None else cfg["auto_stock_in"]
        res = posting_svc.post_doc(
            cur,
            tenant_id=tid,
            workspace_client_id=ws,
            doc_id=doc_id,
            auto_stock_in=auto,
            created_by=_uid(user),
        )
        return ok(res)


@router.post("/docs/{doc_id}/pay")
async def api_pay_doc(doc_id: str, req: PayIn, request: Request):
    _, tid = auth_owner(request)
    with db.get_cursor_rls(tid, commit=True) as cur:
        gate(cur, tid)
        ws = resolve_ws(cur, request, tid, req.workspace_client_id)
        res = posting_svc.pay_doc(
            cur, tenant_id=tid, workspace_client_id=ws, doc_id=doc_id, amount=req.amount
        )
        return ok(res)


@router.post("/docs/{doc_id}/void")
async def api_void_doc(doc_id: str, req: PostIn, request: Request):
    user, tid = auth_owner(request)
    with db.get_cursor_rls(tid, commit=True) as cur:
        gate(cur, tid)
        ws = resolve_ws(cur, request, tid, req.workspace_client_id)
        res = posting_svc.void_doc(
            cur,
            tenant_id=tid,
            workspace_client_id=ws,
            doc_id=doc_id,
            created_by=_uid(user),
        )
        return ok(res)


@router.delete("/docs/{doc_id}")
async def api_delete_doc(
    doc_id: str, request: Request, workspace_client_id: Optional[int] = Query(None)
):
    _, tid = auth_member(request)
    with db.get_cursor_rls(tid, commit=True) as cur:
        gate(cur, tid)
        ws = resolve_ws(cur, request, tid, workspace_client_id)
        docs_svc.delete_doc(cur, tenant_id=tid, workspace_client_id=ws, doc_id=doc_id)
        return ok({"deleted": True})


@router.post("/lines/{line_id}/match-product")
async def api_match_product(line_id: str, req: MatchIn, request: Request):
    _, tid = auth_member(request)
    with db.get_cursor_rls(tid, commit=True) as cur:
        gate(cur, tid)
        ws = resolve_ws(cur, request, tid, req.workspace_client_id)
        res = docs_svc.match_line_product(
            cur,
            tenant_id=tid,
            workspace_client_id=ws,
            line_id=line_id,
            product_id=req.product_id,
            create=req.create,
        )
        return ok(res)


# ---- 凭据生成 / 附件 / 汇总 ---------------------------------------------------


class AttachmentIn(BaseModel):
    workspace_client_id: Optional[int] = None
    kind: str = "bill"
    url: str = ""


def _renderer_for(kind: str):
    """凭据 kind → 渲染函数(替代收据 / 扣缴凭证)。"""
    return (
        documents_svc.render_substitute_receipt
        if kind == "substitute_receipt"
        else documents_svc.render_wht_cert
    )


def _gen_credential(request: Request, doc_id: str, ws_override, kind: str):
    """生成凭据(替代收据/扣缴凭证)· owner 限定 · 渲染校验后登记附件。"""
    _, tid = auth_owner(request)
    with db.get_cursor_rls(tid, commit=True) as cur:
        gate(cur, tid)
        ws = resolve_ws(cur, request, tid, ws_override)
        _renderer_for(kind)(cur, tenant_id=tid, workspace_client_id=ws, doc_id=doc_id)  # 校验可生成
        att = documents_svc.record_generated(
            cur, tenant_id=tid, workspace_client_id=ws, doc_id=doc_id, kind=kind
        )
        return ok({"attachment": att})


@router.post("/docs/{doc_id}/substitute-receipt")
async def api_substitute_receipt(doc_id: str, req: PostIn, request: Request):
    return _gen_credential(request, doc_id, req.workspace_client_id, "substitute_receipt")


@router.post("/docs/{doc_id}/wht-cert")
async def api_wht_cert(doc_id: str, req: PostIn, request: Request):
    return _gen_credential(request, doc_id, req.workspace_client_id, "wht_cert")


@router.get("/docs/{doc_id}/document.pdf")
async def api_document_pdf(
    doc_id: str,
    request: Request,
    kind: str = Query("substitute_receipt"),
    workspace_client_id: Optional[int] = Query(None),
):
    _, tid = auth_member(request)
    if documents_svc.get_generated_kind(kind) is None:
        raise PosError("purchase.line_invalid", 422, detail="bad_kind")
    with db.get_cursor_rls(tid, commit=False) as cur:
        gate(cur, tid)
        ws = resolve_ws(cur, request, tid, workspace_client_id)
        renderer = (
            documents_svc.render_substitute_receipt
            if kind == "substitute_receipt"
            else documents_svc.render_wht_cert
        )
        pdf = renderer(cur, tenant_id=tid, workspace_client_id=ws, doc_id=doc_id)
    return Response(content=pdf, media_type="application/pdf")


@router.post("/docs/{doc_id}/attachments")
async def api_add_attachment(doc_id: str, req: AttachmentIn, request: Request):
    _, tid = auth_member(request)
    with db.get_cursor_rls(tid, commit=True) as cur:
        gate(cur, tid)
        ws = resolve_ws(cur, request, tid, req.workspace_client_id)
        att = documents_svc.add_attachment(
            cur, tenant_id=tid, workspace_client_id=ws, doc_id=doc_id, kind=req.kind, url=req.url
        )
        return ok({"attachment": att})


@router.delete("/attachments/{attachment_id}")
async def api_delete_attachment(
    attachment_id: str, request: Request, workspace_client_id: Optional[int] = Query(None)
):
    _, tid = auth_owner(request)
    with db.get_cursor_rls(tid, commit=True) as cur:
        gate(cur, tid)
        ws = resolve_ws(cur, request, tid, workspace_client_id)
        documents_svc.delete_attachment(
            cur, tenant_id=tid, workspace_client_id=ws, attachment_id=attachment_id
        )
        return ok({"deleted": True})


@router.get("/summary")
async def api_summary(
    request: Request,
    workspace_client_id: Optional[int] = Query(None),
    date_from: Optional[str] = Query(None, alias="from"),
    date_to: Optional[str] = Query(None, alias="to"),
):
    _, tid = auth_member(request)
    with db.get_cursor_rls(tid, commit=False) as cur:
        gate(cur, tid)
        ws = resolve_ws(cur, request, tid, workspace_client_id)
        return ok(
            reports_svc.summary(
                cur, tenant_id=tid, workspace_client_id=ws, date_from=date_from, date_to=date_to
            )
        )
