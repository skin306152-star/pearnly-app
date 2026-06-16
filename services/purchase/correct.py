# -*- coding: utf-8 -*-
"""进项已入账单「更正」= 作废原单(下游完整对冲)+ 精确复制成可改新草稿(docs/purchasing/03)。

posted 是真写进账簿的复式分录,绝不原地改(会断审计链)。更正 = void_doc(完整反冲账本/税表/
库存/付款)+ clone_as_draft(逐列照搬整单为新草稿)→ 用户改完再入账(三步诚实·永不死路)。
已结账/已申报期 void 抛 acct.period_closed → 整事务回滚,原单不动。
"""

from __future__ import annotations

from typing import Optional

from core.pos_api import PosError
from services.purchase import docs as docs_svc
from services.purchase import posting as posting_svc


def correct_doc(cur, *, tenant_id, workspace_client_id, doc_id, created_by) -> dict:
    """作废原单 + 克隆可改新草稿(同一事务·原子)。非 posted → void_doc 抛 only_posted_voidable。"""
    posting_svc.void_doc(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        doc_id=doc_id,
        created_by=created_by,
    )
    draft = clone_as_draft(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        doc_id=doc_id,
        created_by=created_by,
    )
    if draft is None:
        raise PosError("purchase.unexpected", 404)
    return draft


def clone_as_draft(cur, *, tenant_id, workspace_client_id, doc_id, created_by) -> Optional[dict]:
    """精确复制一张单为新草稿。原单不存在 → None。

    逐列照搬已存储值(不重算·不碰金标 totals 口径)+ 全明细 + bill 票图(证据保留),并改写:
    status=draft · approval_status 复位 'none' · paid 清零(列默认)· dedupe_key 置空
    (uq_purchase_docs_dedupe 不排除 void · 原单仍占键 · 复制会撞唯一约束)· ocr_raw 记
    corrected_from 审计链。生成件(替代收据/扣缴凭证)不复制(属原单·按需在新单重生成)。
    """
    cur.execute(
        """
        INSERT INTO purchase_docs
            (tenant_id, workspace_client_id, doc_kind, supplier_id, doc_no, doc_date, has_vat,
             currency, fx_rate, subtotal, discount_total, vat_amount, wht_amount, rounding,
             grand_total, net_payable, category_id, requester, requester_user_id, approval_status,
             payment_status, due_date, source, ocr_raw, dedupe_key, status, amount_override,
             created_by)
        SELECT
            tenant_id, workspace_client_id, doc_kind, supplier_id, doc_no, doc_date, has_vat,
            currency, fx_rate, subtotal, discount_total, vat_amount, wht_amount, rounding,
            grand_total, net_payable, category_id, requester, requester_user_id, 'none',
            payment_status, due_date, source,
            COALESCE(ocr_raw, '{}'::jsonb) || jsonb_build_object('corrected_from', %s::text),
            NULL, 'draft', amount_override, %s
        FROM purchase_docs
        WHERE tenant_id = %s AND workspace_client_id = %s AND id = %s
        RETURNING id
        """,
        (doc_id, created_by, tenant_id, workspace_client_id, doc_id),
    )
    row = cur.fetchone()
    if row is None:
        return None
    new_id = row["id"]
    cur.execute(
        """
        INSERT INTO purchase_lines
            (tenant_id, purchase_doc_id, line_no, item_type, product_id, description,
             qty, unit, unit_price, discount, line_total, vat_rate, vat_applicable,
             wht_rate, category_id, subcategory_id, batch_no, expiry_date)
        SELECT tenant_id, %s, line_no, item_type, product_id, description,
            qty, unit, unit_price, discount, line_total, vat_rate, vat_applicable,
            wht_rate, category_id, subcategory_id, batch_no, expiry_date
        FROM purchase_lines
        WHERE tenant_id = %s AND purchase_doc_id = %s
        """,
        (new_id, tenant_id, doc_id),
    )
    cur.execute(
        "INSERT INTO purchase_attachments (tenant_id, purchase_doc_id, kind, url, generated) "
        "SELECT tenant_id, %s, kind, url, generated FROM purchase_attachments "
        "WHERE tenant_id = %s AND purchase_doc_id = %s AND kind = 'bill'",
        (new_id, tenant_id, doc_id),
    )
    return docs_svc.get_doc(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, doc_id=new_id
    )
