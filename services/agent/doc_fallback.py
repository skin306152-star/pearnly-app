# -*- coding: utf-8 -*-
"""推送定位器的单据兜底(图先话后盲区根治 · 2026-07-02)。

记账租户经 LINE 发图会直接入 purchase_docs、不写 ocr_history;事后说"把刚才那张推
MR.ERP",推送定位只查识别记录 → 恒 history_not_found。这里补第二定位源:
识别记录零命中 → 查本套账近期图片来源单据(line/photo)→ 命中就从单据反拼一行
推送载体 history(推送机械只认 ocr_history),按 source_ref 幂等复用不重插。
记账主路零改动——单据怎么记的照旧,这只是推送侧多认一个货源。
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from core import db

logger = logging.getLogger("mr-pilot")

_SOURCES = ("line", "photo", "image", "file")  # 图片/文件来源单(手录单不兜底:没原始票面)
_RECENT_LIMIT = 5


def carrier_fields_from_doc(detail: Dict[str, Any]) -> Dict[str, Any]:
    """记账单据 → 推送机械认识的 fields(只取校验/生成要用的 · 金额一律 str 同 OCR 产出形)。"""
    doc = detail.get("doc") or {}
    sup = detail.get("supplier") or {}
    items = [
        {
            "name": ln.get("description") or "",
            "qty": str(ln.get("qty") or ""),
            "price": str(ln.get("unit_price") or ""),
            "subtotal": str(ln.get("line_total") or ""),
        }
        for ln in detail.get("lines") or []
    ]
    return {
        "document_type": "tax_invoice" if doc.get("has_vat") else "receipt",
        "invoice_number": doc.get("doc_no") or "",
        "date": str(doc.get("doc_date") or "")[:10],
        "seller_name": sup.get("name") or "",
        "seller_tax": sup.get("tax_id") or "",
        "subtotal": str(doc.get("subtotal") or ""),
        "vat": str(doc.get("vat_amount") or ""),
        "total_amount": str(doc.get("grand_total") or ""),
        "items": items,
    }


def locate_pushable_doc(ctx, keyword) -> Optional[Dict[str, Any]]:
    """识别记录零命中后的单据兜底。返回 hist 形 dict(id/seller_name/total_amount/
    invoice_no)或 None(零命中/多命中歧义/任何故障 → 维持原 not_found 口径,不猜)。"""
    try:
        from services.purchase import docs as docs_svc

        ws = ctx.workspace_client_id
        if not (ctx.tenant_id and ws):
            return None
        with db.get_cursor_rls(ctx.tenant_id, workspace_client_id=ws) as cur:
            res = docs_svc.list_docs(
                cur,
                tenant_id=ctx.tenant_id,
                workspace_client_id=ws,
                q=(keyword or None),
            )
            docs = [
                d
                for d in (res.get("docs") or [])
                if d.get("source") in _SOURCES and d.get("status") in ("posted", "draft")
            ][:_RECENT_LIMIT]
            if not docs or (keyword and len(docs) > 1):
                return None  # 多命中不猜(与识别记录侧 ambiguous 同精神,交模型追问)
            doc = docs[0]
            detail = docs_svc.get_doc(
                cur, tenant_id=ctx.tenant_id, workspace_client_id=ws, doc_id=doc["id"]
            )
        if not detail:
            return None
        hid = _ensure_carrier(ctx, ws, detail)
        if not hid:
            return None
        fields = carrier_fields_from_doc(detail)
        logger.info("[doc_fallback] doc=%s -> carrier=%s", str(doc["id"])[:8], str(hid)[:8])
        return {
            "id": str(hid),
            "invoice_no": fields["invoice_number"],
            "seller_name": fields["seller_name"],
            "total_amount": fields["total_amount"],
        }
    except Exception:
        logger.warning("[doc_fallback] locate failed; keep not_found", exc_info=True)
        return None


def _ensure_carrier(ctx, ws, detail) -> Optional[str]:
    """按 source_ref=purchase_doc:<id> 幂等取/建载体行(重复"推刚才那张"不重插)。"""
    doc_id = str((detail.get("doc") or {}).get("id"))
    ref = f"purchase_doc:{doc_id}"
    with db.get_cursor_rls(ctx.tenant_id) as cur:
        cur.execute(
            "SELECT id FROM ocr_history WHERE tenant_id = %s::uuid AND source_ref = %s LIMIT 1",
            (ctx.tenant_id, ref),
        )
        row = cur.fetchone()
    if row:
        return str(row["id"])
    fields = carrier_fields_from_doc(detail)
    return db.insert_ocr_history(
        user_id=str(ctx.user["id"]),
        tenant_id=ctx.tenant_id,
        filename=f"doc-{(fields['invoice_number'] or doc_id)[:24]}",
        page_count=1,
        pages=[{"page": 1, "fields": fields}],
        confidence="high",  # 来源=用户已核对入账的单据,非生 OCR
        elapsed_ms=0,
        file_size_kb=0,
        source="line_bot",
        source_ref=ref,
        workspace_client_id=ws,
    )
