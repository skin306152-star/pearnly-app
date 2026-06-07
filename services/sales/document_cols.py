# -*- coding: utf-8 -*-
"""sales_documents / sales_document_lines 的 SELECT 列清单(从 document.py 拆出 · 控行数)。

纯字符串常量 · 无逻辑 · 无依赖。get_document / list_documents / finalize_issue 复用。
"""

from __future__ import annotations

_DOC_COLS = (
    "id, tenant_id, doc_type, doc_number, client_id, seller_workspace_client_id, issue_date, "
    "status, currency, subtotal, discount_total, vat_rate, vat_amount, wht_rate, wht_amount, "
    "grand_total, "
    "header_discount_amount, header_discount_pct, price_includes_vat, copies_layout, "
    "paper_size, doc_language, "
    "buyer_type, buyer_name, buyer_address, buyer_tax_id, buyer_branch_type, buyer_branch_no, "
    "parties_snapshot, payment_status, paid_amount, payment_method, payment_date, "
    "due_date, payment_terms, approved_by, approved_at, rejected_reason, "
    "pdf_sha256, pdf_url, "
    "issued_at, created_by, references_document_id, reference_reason, created_at, updated_at"
)
_LINE_COLS = (
    "id, document_id, line_no, product_id, description, qty, unit_price, "
    "discount, discount_pct, vat_applicable, line_total"
)
