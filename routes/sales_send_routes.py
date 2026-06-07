# -*- coding: utf-8 -*-
"""发票发送 + 公开分享(PO-7 · docs/16 §L5)。

POST /{id}/send 只两档(各渠道唯一发法):
- channel=email:Pearnly 官方代发——hello@pearnly.com 发 PDF,From 显示卖方名、Reply-To 卖方邮箱。
- channel=line:生成公开分享链接,卖方用自己 LINE 转给买家(不在此推送)。
其余渠道一律拒(私人 Gmail / LINE 官号推送已砍,不做)。

GET /shared/{token}/pdf:公开能力链接(不鉴权·token 即凭证),凭 token 反查渲染 PDF。
薄层:鉴权 + 整形;发送/分享/渲染在 services/sales/{send,share,render}.py。
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response
from pydantic import BaseModel, Field

from core import db
from core.route_helpers import _require_tenant
from services.sales import document as doc_svc
from services.sales import pdf as pdf_svc
from services.sales import render as sales_render
from services.sales import send as send_svc
from services.sales import share as share_svc

logger = logging.getLogger("mr-pilot")
router = APIRouter(prefix="/api/sales/documents", tags=["sales-send"])

_ERR_HTTP = {
    "not_found": 404,
    "not_issued": 409,
    "recipient_required": 422,
    "unsupported_channel": 400,
    "send_failed": 502,
}


def _fail(code: str, detail: Optional[str] = None):
    raise HTTPException(_ERR_HTTP.get(code, 400), detail=detail or f"sales.{code}")


class SendIn(BaseModel):
    channel: str = Field(..., max_length=10, description="email(官方代发)| line(分享链接)")
    to: Optional[str] = Field(None, max_length=200, description="收件邮箱(email 渠道)")
    message: Optional[str] = Field(None, max_length=2000, description="附言(可选)")


def _email_content(doc: dict, seller: dict, message: Optional[str]) -> tuple[str, str]:
    """官方代发邮件主题/正文(泰英双语 · 简洁)。卖方名 + 单号 + 可选附言。"""
    seller_name = (seller or {}).get("name") or "Pearnly"
    num = doc.get("doc_number") or ""
    label = pdf_svc._DOC_LABEL.get(doc.get("doc_type"), doc.get("doc_type") or "เอกสาร / Document")
    subject = f"{label} {num} · {seller_name}"
    note = f"<p style='white-space:pre-wrap'>{message}</p>" if message and message.strip() else ""
    html = (
        f"<div style='font-family:sans-serif;font-size:14px;color:#1f2937'>"
        f"<p>เรียน ลูกค้า / Dear customer,</p>"
        f"<p>เอกสาร <b>{label} {num}</b> จาก <b>{seller_name}</b> แนบมาในอีเมลนี้ (PDF).<br>"
        f"Please find <b>{label} {num}</b> from <b>{seller_name}</b> attached as a PDF.</p>"
        f"{note}"
        f"<p style='color:#6b7280;font-size:12px'>ส่งผ่าน Pearnly · ตอบกลับอีเมลนี้เพื่อติดต่อผู้ขาย / "
        f"Sent via Pearnly · reply to reach the seller.</p></div>"
    )
    return subject, html


@router.post("/{doc_id}/send")
async def api_send_document(doc_id: str, req: SendIn, request: Request):
    """发送已开票:channel=email 官方代发 PDF;channel=line 出分享链接。各渠道唯一发法,其余拒。"""
    tid, uid = _require_tenant(request)
    p = req.model_dump() if hasattr(req, "model_dump") else req.dict()
    channel = p["channel"]
    if channel not in ("email", "line"):
        _fail("unsupported_channel", detail=f"sales.unsupported_channel:{channel}")
    with db.get_cursor_rls(tid, commit=True) as cur:
        doc = doc_svc.get_document(cur, tenant_id=tid, doc_id=doc_id)
        if not doc:
            _fail("not_found")
        if not doc.get("doc_number"):
            _fail("not_issued")

        if channel == "email":
            to = (p.get("to") or "").strip()
            if not to:
                _fail("recipient_required")
            parties = sales_render.resolve_parties(cur, tenant_id=tid, doc=doc)
            seller = parties[0]
            pdf_bytes = sales_render.build_pdf(
                cur,
                tenant_id=tid,
                doc=doc,
                parties=parties,
                page=doc.get("paper_size") or "A4",
                copies_layout=doc.get("copies_layout") or "separate",
                lang=doc.get("doc_language") or "th_en",
            )
            subject, html = _email_content(doc, seller or {}, p.get("message"))
            ok, err = send_svc.send_email_with_pdf(
                to_email=to,
                subject=subject,
                html_body=html,
                pdf_bytes=pdf_bytes,
                pdf_name=(doc.get("doc_number") or "document").replace("/", "_"),
                from_name=(seller or {}).get("name") or "Pearnly",
                reply_to=(seller or {}).get("email"),
            )
            send_svc.record_send(
                cur,
                tenant_id=tid,
                doc_id=doc_id,
                channel="email",
                identity="official",
                recipient=to,
                status="sent" if ok else "failed",
                error=None if ok else err,
                created_by=uid,
            )
            if not ok:
                _fail("send_failed", detail=f"sales.send_failed:{err}")
            return {"ok": True, "channel": "email", "identity": "official", "recipient": to}

        token = share_svc.get_or_create_share_token(cur, tenant_id=tid, doc_id=doc_id)
        share_url = f"{str(request.base_url).rstrip('/')}/api/sales/documents/shared/{token}/pdf"
        send_svc.record_send(
            cur,
            tenant_id=tid,
            doc_id=doc_id,
            channel="line",
            identity="self",
            recipient=None,
            status="link_created",
            error=None,
            created_by=uid,
        )
        return {"ok": True, "channel": "line", "identity": "self", "share_url": share_url}


@router.get("/shared/{token}/pdf")
async def api_shared_pdf(token: str, page: str = ""):
    """公开发票 PDF(能力链接·不鉴权):token 不可猜即凭证;凭 token 反查租户/单据后渲染。"""
    with db.get_cursor_rls(bypass=True) as cur:
        ref = share_svc.resolve_token(cur, token)
        if not ref:
            raise HTTPException(404, detail="sales.not_found")
        tid = str(ref["tenant_id"])
        doc = doc_svc.get_document(cur, tenant_id=tid, doc_id=ref["document_id"])
        if not doc:
            raise HTTPException(404, detail="sales.not_found")
        data = sales_render.build_pdf(
            cur,
            tenant_id=tid,
            doc=doc,
            page=page or doc.get("paper_size") or "A4",
            copies_layout=doc.get("copies_layout") or "separate",
            lang=doc.get("doc_language") or "th_en",
        )
    filename = (doc.get("doc_number") or "invoice").replace("/", "_")
    return Response(
        content=data,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{filename}.pdf"'},
    )
