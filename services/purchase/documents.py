# -*- coding: utf-8 -*-
"""凭据生成(替代收据 / 扣缴凭证)+ 附件 DAL(商户采购 · Paypers 对标 · docs/purchasing/02 §3)。

复用销项 reportlab 泰文模板(services/sales/pdf.render_invoice_pdf),不从零造:
  - 替代收据(ใบรับรองแทนใบเสร็จ):无正规发票的费用 → 由本主体(付款方)开具使其合规可抵。
  - 扣缴凭证(หนังสือรับรองการหักภาษี ณ ที่จ่าย):wht_amount>0 时,证明已代扣预扣税。
卖方块=本套账主体(seller_profile),买方块=供应商。PDF 按需重生成(不存 blob,确定性)。
attachments 表挂票图 / 系统生成凭据(generated=true)。隔离=每句 WHERE tenant_id。调用方管事务。
"""

from __future__ import annotations

from decimal import Decimal
from typing import Optional

from core.pos_api import PosError
from services.purchase import docs as docs_svc
from services.purchase import suppliers as sup_svc
from services.purchase.attachment_files import resolve_upload_ref

_GENERATED_KINDS = ("substitute_receipt", "wht_cert")
_UPLOAD_KINDS = ("bill", "payment_proof")


def _seller_block(cur, *, tenant_id, workspace_client_id) -> dict:
    """本套账主体 = 凭据签发方(卖方块)。无资料则最小占位。"""
    from services.sales import seller_profile

    s = seller_profile.get_seller(cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id)
    return s or {"name": "", "tax_id": "", "address": ""}


def _buyer_block(cur, *, tenant_id, workspace_client_id, supplier_id) -> dict:
    """供应商 = 凭据对手方(买方块)。"""
    if not supplier_id:
        return {"name": "", "type": "company"}
    s = sup_svc.get_supplier(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, supplier_id=supplier_id
    )
    if not s:
        return {"name": "", "type": "company"}
    return {
        "name": s.get("name") or "",
        "type": "company",
        "tax_id": s.get("tax_id") or "",
        "address": s.get("address") or "",
        "branch_type": s.get("branch_type") or "none",
        "branch_no": s.get("branch_no") or "",
    }


def _money(v) -> str:
    return str(Decimal(str(v or 0)).quantize(Decimal("0.01")))


def _doc_lines_for_pdf(lines: list) -> list:
    return [
        {
            "line_no": ln["line_no"],
            "description": ln.get("description") or "",
            "qty": ln.get("qty"),
            "unit_price": ln.get("unit_price"),
            "line_total": ln.get("line_total"),
        }
        for ln in lines or []
    ]


def render_substitute_receipt(
    cur, *, tenant_id, workspace_client_id, doc_id, lang="th_en"
) -> bytes:
    """替代收据 PDF(全额费用·本主体签发)。"""
    from services.sales.pdf import render_invoice_pdf

    bundle = docs_svc.get_doc(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, doc_id=doc_id
    )
    if bundle is None:
        raise PosError("purchase.unexpected", 404)
    d = bundle["doc"]
    doc = {
        "doc_type": "receipt",
        "doc_number": (d.get("doc_no") or f"SR-{str(doc_id)[:8]}"),
        "issue_date": d.get("doc_date"),
        "currency": d.get("currency") or "THB",
        "subtotal": _money(d.get("subtotal")),
        "vat_rate": "7" if d.get("has_vat") else "0",
        "vat_amount": _money(d.get("vat_amount")),
        "wht_amount": _money(d.get("wht_amount")),
        "grand_total": _money(d.get("grand_total")),
        "lines": _doc_lines_for_pdf(bundle["lines"]),
    }
    seller = _seller_block(cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id)
    buyer = _buyer_block(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        supplier_id=d.get("supplier_id"),
    )
    return render_invoice_pdf(doc, seller, buyer, page="A4", lang=lang)


def render_wht_cert(cur, *, tenant_id, workspace_client_id, doc_id, lang="th_en") -> bytes:
    """扣缴凭证 PDF(wht_amount>0)。仅展示代扣信息。"""
    from services.sales.pdf import render_invoice_pdf

    bundle = docs_svc.get_doc(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, doc_id=doc_id
    )
    if bundle is None:
        raise PosError("purchase.unexpected", 404)
    d = bundle["doc"]
    wht = Decimal(str(d.get("wht_amount") or 0))
    if wht <= 0:
        raise PosError("purchase.amount_mismatch", 422, detail="no_wht")
    doc = {
        "doc_type": "receipt",
        "doc_number": f"WHT-{str(doc_id)[:8]}",
        "issue_date": d.get("doc_date"),
        "currency": d.get("currency") or "THB",
        "subtotal": _money(d.get("subtotal")),
        "vat_rate": "0",
        "vat_amount": "0.00",
        "wht_amount": _money(wht),
        "grand_total": _money(wht),
        "lines": [
            {
                "line_no": 1,
                "description": "ภาษีหัก ณ ที่จ่าย / Withholding tax",
                "qty": "1",
                "unit_price": _money(wht),
                "line_total": _money(wht),
            }
        ],
    }
    seller = _seller_block(cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id)
    buyer = _buyer_block(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        supplier_id=d.get("supplier_id"),
    )
    return render_invoice_pdf(doc, seller, buyer, page="A4", lang=lang)


def record_generated(cur, *, tenant_id, workspace_client_id, doc_id, kind) -> dict:
    """登记系统生成凭据附件(generated=true);幂等:同 doc 同 kind 复用既有行。"""
    if kind not in _GENERATED_KINDS:
        raise PosError("purchase.line_invalid", 422, detail="bad_kind")
    _assert_doc(cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, doc_id=doc_id)
    url = f"/api/purchase/docs/{doc_id}/document.pdf?kind={kind}"
    cur.execute(
        "SELECT id FROM purchase_attachments "
        "WHERE tenant_id = %s AND purchase_doc_id = %s AND kind = %s AND generated = TRUE",
        (tenant_id, doc_id, kind),
    )
    row = cur.fetchone()
    if row:
        return {"id": row["id"], "kind": kind, "url": url, "generated": True}
    cur.execute(
        "INSERT INTO purchase_attachments (tenant_id, purchase_doc_id, kind, url, generated) "
        "VALUES (%s, %s, %s, %s, TRUE) RETURNING id, kind, url, generated, created_at",
        (tenant_id, doc_id, kind, url),
    )
    return cur.fetchone()


def add_attachment(cur, *, tenant_id, workspace_client_id, doc_id, kind, url) -> dict:
    """挂上传附件(票图/付款凭证)· url 由前端经 /api/uploads 预上传得到。"""
    if kind not in _UPLOAD_KINDS:
        raise PosError("purchase.line_invalid", 422, detail="bad_kind")
    if not (url or "").strip():
        raise PosError("purchase.line_invalid", 422, detail="no_url")
    _assert_doc(cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, doc_id=doc_id)
    cur.execute(
        "INSERT INTO purchase_attachments (tenant_id, purchase_doc_id, kind, url, generated) "
        "VALUES (%s, %s, %s, %s, FALSE) RETURNING id, kind, url, generated, created_at",
        (tenant_id, doc_id, kind, url.strip()),
    )
    return cur.fetchone()


def delete_attachment(
    cur, *, tenant_id, workspace_client_id, attachment_id
) -> Optional[tuple[str, str]]:
    """删附件(限本套账内单据的附件)。返回该附件对应的落盘文件 ref(供路由层在事务提交后
    物理删除);非本系统 uploads 文件(生成件虚 URL / bill 的 OCR 落盘 ref)→ None,见
    services/purchase/attachment_files.resolve_upload_ref。"""
    cur.execute(
        "SELECT kind, url, generated FROM purchase_attachments "
        "WHERE tenant_id = %s AND id = %s AND purchase_doc_id IN ("
        "  SELECT id FROM purchase_docs "
        "  WHERE tenant_id = %s AND workspace_client_id = %s)",
        (tenant_id, attachment_id, tenant_id, workspace_client_id),
    )
    row = cur.fetchone()
    if row is None:
        raise PosError("purchase.unexpected", 404)
    ref = resolve_upload_ref(
        tenant_id=tenant_id, kind=row["kind"], url=row["url"], generated=row["generated"]
    )
    cur.execute(
        "DELETE FROM purchase_attachments WHERE tenant_id = %s AND id = %s",
        (tenant_id, attachment_id),
    )
    return ref


def _assert_doc(cur, *, tenant_id, workspace_client_id, doc_id) -> None:
    cur.execute(
        "SELECT 1 FROM purchase_docs "
        "WHERE tenant_id = %s AND workspace_client_id = %s AND id = %s",
        (tenant_id, workspace_client_id, doc_id),
    )
    if not cur.fetchone():
        raise PosError("purchase.unexpected", 404)


def get_generated_kind(kind: str) -> Optional[str]:
    """校验 document.pdf 的 kind 参数(只许系统生成两类)。"""
    return kind if kind in _GENERATED_KINDS else None
