# -*- coding: utf-8 -*-
"""报价单 → 发票转换(L3 · docs/16 §L3)。

`quotation` doc_type 已有,缺一键转开票。把报价单的双方 + 明细复制成一张目标类型**草稿**,
`references_document_id` 指原报价单;报价单本身不变。转出的新票按自己类型,**开出时**才取
连号(报价单不占发票号)。薄派生层,复用 document 的列定义/明细写入/取详情。
"""

from __future__ import annotations

from typing import Optional

from services.sales import document as doc_svc

# 报价单可转成的目标单据类型。
CONVERT_TARGETS = ("tax_invoice", "tax_invoice_receipt", "receipt")


def convert_quotation(
    cur, *, tenant_id: str, created_by: Optional[str], quote_id, target_doc_type: str
) -> tuple[Optional[dict], Optional[str]]:
    """复制报价单成目标类型草稿。返回 (draft, error_code)。

    错误码:bad_target_type / original_not_found / not_a_quotation。
    """
    if target_doc_type not in CONVERT_TARGETS:
        return None, "bad_target_type"
    quote = doc_svc.get_document(cur, tenant_id=tenant_id, doc_id=quote_id)
    if not quote:
        return None, "original_not_found"
    if quote.get("doc_type") != "quotation":
        return None, "not_a_quotation"
    cur.execute(
        "INSERT INTO sales_documents (tenant_id, doc_type, client_id, seller_workspace_client_id, "
        "status, currency, subtotal, discount_total, header_discount_amount, header_discount_pct, "
        "price_includes_vat, vat_rate, vat_amount, wht_rate, wht_amount, grand_total, "
        "buyer_type, buyer_name, buyer_address, buyer_tax_id, buyer_branch_type, buyer_branch_no, "
        "due_date, payment_terms, created_by, references_document_id, reference_reason) "
        "SELECT %s, %s, client_id, seller_workspace_client_id, 'draft', currency, subtotal, "
        "discount_total, header_discount_amount, header_discount_pct, price_includes_vat, "
        "vat_rate, vat_amount, wht_rate, wht_amount, grand_total, buyer_type, buyer_name, "
        "buyer_address, buyer_tax_id, buyer_branch_type, buyer_branch_no, due_date, payment_terms, "
        "%s, id, %s FROM sales_documents WHERE tenant_id=%s AND id=%s RETURNING id",
        (tenant_id, target_doc_type, created_by, "converted_from_quotation", tenant_id, quote_id),
    )
    new_id = cur.fetchone()["id"]
    doc_svc._replace_lines(cur, tenant_id, new_id, quote["lines"])
    return doc_svc.get_document(cur, tenant_id=tenant_id, doc_id=new_id), None
