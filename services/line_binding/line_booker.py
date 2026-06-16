# -*- coding: utf-8 -*-
"""LINE 入账编排共享口(/simplify #10)。

文本单笔(line_expense._do_record)、文本多项(line_expense_multi)、图片(line_ingest)三路
此前各写一份「book_by_confidence → nonce.mint」和一份 ack-key 表。收成一处:行为不变,
只去重复(改后复验归类/总额不变)。
"""

from __future__ import annotations

# 回执文案 key:状态 → line_i18n 键(原散在 3 处,完全相同)。
_ACK_KEYS = {"posted": "exp_ack_posted", "dup": "exp_ack_dup"}


def ack_key(state: str) -> str:
    """入账状态 → 引用回执的 i18n 文案 key(posted/dup/其余=confirm)。"""
    return _ACK_KEYS.get(state, "exp_ack_confirm")


def _find_dup_doc(cur, tenant_id, workspace_client_id, data):
    """撞 dup_invoice 后取已有单(与 create_doc 同口径算 dedupe_key)。LINE 路无 amount_override,
    故 grand_total 直接 compute_purchase_totals(lines) 即等于 create_doc 的 _effective_calc。"""
    from services.purchase import docs as docs_svc
    from services.purchase import totals as totals_svc

    calc = totals_svc.compute_purchase_totals(data.get("lines") or [])
    supplier = data.get("supplier")
    supplier_tax = supplier.get("tax_id") if isinstance(supplier, dict) else None
    dkey = totals_svc.dedupe_key(
        supplier_tax=supplier_tax, doc_no=data.get("doc_no"), grand_total=calc["grand_total"]
    )
    if not dkey:
        return None
    return docs_svc.find_by_dedupe(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, dedupe_key=dkey
    )


def book_and_mint(
    cur, *, tenant_id, workspace_client_id, data, settings, verdict, created_by
) -> tuple[str, str, str]:
    """建草稿 → 按置信过账(book_by_confidence)→ 为卡片动作铸 nonce token。

    返回 (doc_id, state, token)。三路共用同一编排(消除各写一份)。行为与原逐路实现等价。
    重复票:create_doc 撞 dedupe_block 抛 dup_invoice → 不重复入账,指向已有单 → state='dup'
    出「可能重复」卡(治原图片路回落纯文字/静默丢 · spec §1 dup 卡此前不可达)。
    """
    from core.pos_api import PosError
    from services.line_binding import line_action_nonce as nonce
    from services.purchase import confidence_post

    try:
        doc_id, state = confidence_post.book_by_confidence(
            cur,
            tenant_id=tenant_id,
            workspace_client_id=workspace_client_id,
            data=data,
            settings=settings,
            verdict=verdict,
            created_by=created_by,
        )
    except PosError as e:
        if (e.code or "") != "purchase.dup_invoice":
            raise
        existing = _find_dup_doc(cur, tenant_id, workspace_client_id, data)
        doc_id, state = (str(existing["id"]) if existing else ""), "dup"
    token = (
        nonce.mint(
            cur,
            tenant_id=tenant_id,
            workspace_client_id=workspace_client_id,
            action_ref=doc_id,
            user_id=created_by,
        )
        if doc_id
        else ""
    )
    return doc_id, state, token
