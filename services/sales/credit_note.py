# -*- coding: utf-8 -*-
"""红冲 / 补开(PO-5 · docs/sales-module/docs/13)。

- 调减(退货/折让/开错调低)→ 红冲 ใบลดหนี้ credit_note(RD §86/10)
- 调增(补收/开错调高)→ 补开 ใบเพิ่มหนี้ debit_note(RD §86/9)

两者都引用一张**已开出**的原始发票,自身也是正式单据:复用 sales_documents
(doc_type=credit_note/debit_note · references_document_id 指原单),走独立连号序列
并直接开出(留痕)。金额复用 document.compute_totals。
"""

from __future__ import annotations

from datetime import date
from typing import Optional

from services.sales import archive
from services.sales import document as doc_svc
from services.sales import numbering

NOTE_TYPES = ("credit_note", "debit_note")
_NOTE_PREFIX = {"credit_note": "CN", "debit_note": "DN"}


def create_note(
    cur,
    *,
    tenant_id: str,
    created_by: Optional[str],
    original_id,
    note_type: str,
    reason: Optional[str],
    lines: list,
    vat_rate,
    wht_rate,
    prefix: Optional[str],
    reset: str,
    on: date,
) -> tuple[Optional[dict], Optional[str]]:
    """建并开出一张红冲/补开单。返回 (note, error_code)。

    原单必须存在且已开出(草稿/作废不能冲)。错误码:bad_note_type / original_not_found
    / original_not_issued。
    """
    if note_type not in NOTE_TYPES:
        return None, "bad_note_type"
    cur.execute(
        "SELECT status, price_includes_vat, seller_workspace_client_id "
        "FROM sales_documents WHERE tenant_id=%s AND id=%s",
        (tenant_id, original_id),
    )
    row = cur.fetchone()
    if not row:
        return None, "original_not_found"
    if row["status"] != doc_svc.STATUS_ISSUED:
        return None, "original_not_issued"

    t = doc_svc.compute_totals(
        lines, vat_rate=vat_rate, wht_rate=wht_rate, price_includes_vat=row["price_includes_vat"]
    )
    use_prefix = prefix or _NOTE_PREFIX[note_type]
    # PO-7b:红冲/补开是原票的法律延续,继承原单卖方主体 → 同主体号段连续 + 归属同套账。
    ws = doc_svc.workspace_for_numbering(cur, tenant_id, row)
    doc_number, _ = numbering.allocate(
        cur,
        tenant_id=tenant_id,
        doc_type=note_type,
        prefix=use_prefix,
        reset=reset,
        on=on,
        workspace_client_id=ws,
    )
    # 买方/卖方信息从原单继承冻结快照(docs/16 §A):红冲/补开是原票的法律延续,
    # 双方信息须与原单一致,且原单开出时已冻结,这里 verbatim 带过来。
    # seller_workspace_client_id 同样继承(PO-7a 隔离:notes 不能留 NULL 跨套账泄漏)。
    cur.execute(
        "INSERT INTO sales_documents (tenant_id, doc_type, doc_number, client_id, issue_date, "
        "status, currency, subtotal, discount_total, vat_rate, vat_amount, wht_rate, wht_amount, "
        "grand_total, price_includes_vat, issued_at, created_by, references_document_id, "
        "reference_reason, seller_workspace_client_id, parties_snapshot, buyer_type, buyer_name, "
        "buyer_address, buyer_tax_id, buyer_branch_type, buyer_branch_no) "
        "SELECT %s, %s, %s, client_id, %s, 'issued', currency, %s, %s, %s, %s, %s, %s, "
        "price_includes_vat, now(), %s, id, %s, %s, parties_snapshot, buyer_type, buyer_name, "
        "buyer_address, buyer_tax_id, buyer_branch_type, buyer_branch_no FROM sales_documents "
        "WHERE tenant_id=%s AND id=%s RETURNING id",
        (
            tenant_id,
            note_type,
            doc_number,
            on,
            t["subtotal"],
            t["discount_total"],
            t["vat_rate"],
            t["vat_amount"],
            t["wht_rate"],
            t["wht_amount"],
            t["grand_total"],
            created_by,
            reason,
            ws,
            tenant_id,
            original_id,
        ),
    )
    note_id = cur.fetchone()["id"]
    doc_svc._replace_lines(cur, tenant_id, note_id, t["lines"])
    note = doc_svc.get_document(cur, tenant_id=tenant_id, doc_id=note_id)
    # 红冲/补开也是正式票,同样留存档哈希(§E3);双方从继承的冻结快照渲染。
    archive.store_archival_hash(cur, tenant_id, note_id, note, note.get("parties_snapshot") or {})
    return note, None
