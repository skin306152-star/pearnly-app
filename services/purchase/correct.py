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


def clone_as_draft(
    cur, *, tenant_id, workspace_client_id, doc_id, created_by, audit_key="corrected_from"
) -> Optional[dict]:
    """精确复制一张单为新草稿。原单不存在 → None。

    逐列照搬已存储值(不重算·不碰金标 totals 口径)+ 全明细 + bill 票图(证据保留),并改写:
    status=draft · approval_status 复位 'none' · paid 清零(列默认)· dedupe_key 置空
    (uq_purchase_docs_dedupe 不排除 void · 原单仍占键 · 复制会撞唯一约束)· ocr_raw 记审计链
    (audit_key=corrected_from 更正 / restored_from 恢复)。生成件(替代收据/扣缴凭证)不复制
    (属原单·按需在新单重生成)。
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
            COALESCE(ocr_raw, '{}'::jsonb) || jsonb_build_object(%s, %s::text),
            NULL, 'draft', amount_override, %s
        FROM purchase_docs
        WHERE tenant_id = %s AND workspace_client_id = %s AND id = %s
        RETURNING id
        """,
        (audit_key, doc_id, created_by, tenant_id, workspace_client_id, doc_id),
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


def find_active_restored_child(cur, *, tenant_id, workspace_client_id, doc_id):
    """该单是否已被恢复过(有活的 restored_from 子单)→ 返回 row{id,grand_total};无 → None。"""
    cur.execute(
        "SELECT id, grand_total FROM purchase_docs "
        "WHERE tenant_id = %s AND workspace_client_id = %s "
        "AND ocr_raw->>'restored_from' = %s AND status IN ('draft', 'posted') "
        "ORDER BY created_at DESC LIMIT 1",
        (tenant_id, workspace_client_id, str(doc_id)),
    )
    return cur.fetchone()


def discard_doc(cur, *, tenant_id, workspace_client_id, doc_id) -> None:
    """草稿软删:仅 draft → status='discarded' + 释放 dedupe_key(指纹·非金额/明细·留库可恢复)。

    ★软删后对所有活跃口径隐形(查明细/汇总/总额/查重/批量撤候选/网页列表均排除 discarded)——删了的
    绝不还在账上。物理 delete_doc 保留(数据迁移等)但 LINE 四处删一律走此软删。非 draft → not_draft 409。
    """
    cur.execute(
        "UPDATE purchase_docs SET status = 'discarded', dedupe_key = NULL, updated_at = now() "
        "WHERE tenant_id = %s AND workspace_client_id = %s AND id = %s AND status = 'draft'",
        (tenant_id, workspace_client_id, doc_id),
    )
    if cur.rowcount == 0:
        raise PosError("purchase.not_draft", 409)


def restore_doc(cur, *, tenant_id, workspace_client_id, doc_id, created_by) -> dict:
    """恢复死单:已撤销(void)→ 克隆重过账成新 posted(restored_from 审计·原死单不动);草稿软删
    (discarded)→ 原地翻回 draft(数据完整·不重过账·不重算金额)。返回其一:
      {"gone": True}        查不到(旧物理删)→ 数据已不在,不可恢复
      {"not_deleted": True} 活单(draft/posted)→ 没删没撤,无需恢复
      {"already": row}      void 已恢复过(有活 restored_from 子单)→ 幂等不重建
      {"restored": detail}  恢复成功(新 posted / 翻回 draft)
    已结期:void 恢复重过账 post_doc 抛 acct.period_closed → 整事务回滚,不留半张(诚实·不破账)。
    """
    orig = docs_svc.get_doc(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, doc_id=doc_id
    )
    if orig is None:
        return {"gone": True}
    status = (orig.get("doc") or {}).get("status")
    if status == "discarded":  # 草稿软删 → 原地翻回 draft(数据原样·不动金额/明细)
        cur.execute(
            "UPDATE purchase_docs SET status = 'draft', updated_at = now() "
            "WHERE tenant_id = %s AND workspace_client_id = %s AND id = %s AND status = 'discarded'",
            (tenant_id, workspace_client_id, doc_id),
        )
        return {
            "restored": docs_svc.get_doc(
                cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, doc_id=doc_id
            )
        }
    if status != "void":
        return {"not_deleted": True}
    existing = find_active_restored_child(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, doc_id=doc_id
    )
    if existing:
        return {"already": existing}
    draft = clone_as_draft(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        doc_id=doc_id,
        created_by=created_by,
        audit_key="restored_from",
    )
    if draft is None:
        raise PosError("purchase.unexpected", 404)
    new_id = str((draft.get("doc") or {})["id"])
    posting_svc.post_doc(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        doc_id=new_id,
        auto_stock_in=False,
        created_by=created_by,
    )
    return {
        "restored": docs_svc.get_doc(
            cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, doc_id=new_id
        )
    }
