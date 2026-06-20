# -*- coding: utf-8 -*-
"""LINE 改错的「详情 ↔ update_draft 入参」转换 + 字段落地(从 line_correct 拆出 · 纯数据变换)。

忠实搬运总额相关列(qty/单价/折扣/税率/多行原样·总额不漂),只把用户指定的字段改到克隆草稿。
金额仅作用单行(多行已在更上层拦),绝不让代码/LLM 重算多行明细。
"""

from __future__ import annotations

import logging
from typing import Optional

from services.expense.expense_draft import ExpenseDraft

logger = logging.getLogger(__name__)


def detail_to_data(detail: dict) -> dict:
    """get_doc 详情 → update_draft 入参(保多行 + 总额相关列原样)。"""
    doc = detail.get("doc") or {}
    sup = detail.get("supplier") or {}
    return {
        "doc_kind": doc.get("doc_kind") or "expense",
        "doc_no": doc.get("doc_no"),
        "doc_date": doc.get("doc_date"),
        "has_vat": doc.get("has_vat"),
        "currency": doc.get("currency") or "THB",
        "fx_rate": doc.get("fx_rate") or 1,
        "category_id": doc.get("category_id"),
        "requester": doc.get("requester"),
        "due_date": doc.get("due_date"),
        "payment_status": doc.get("payment_status") or "unpaid",
        "payment_method": doc.get("payment_method"),
        "amount_override": doc.get("amount_override"),
        "discount_total": doc.get("discount_total") or 0,
        "rounding": doc.get("rounding") or 0,
        "supplier": {
            "name": sup.get("name") or "",
            "tax_id": sup.get("tax_id"),
            "branch_type": sup.get("branch_type"),
            "branch_no": sup.get("branch_no"),
            "address": sup.get("address"),
            "phone": sup.get("phone"),
        },
        "lines": [_clone_line(ln) for ln in detail.get("lines") or []],
    }


def _clone_line(ln: dict) -> dict:
    """purchase_lines 行 → update_draft 行入参(qty/单价/折扣/税率原样 · 总额不漂)。"""
    return {
        "item_type": ln.get("item_type") or "goods",
        "product_id": ln.get("product_id"),
        "description": ln.get("description") or "",
        "qty": ln.get("qty"),
        "unit": ln.get("unit"),
        "unit_price": ln.get("unit_price"),
        "discount": ln.get("discount"),
        "vat_rate": ln.get("vat_rate"),
        "vat_applicable": ln.get("vat_applicable"),
        "wht_rate": ln.get("wht_rate"),
        "category_id": ln.get("category_id"),
        "subcategory_id": ln.get("subcategory_id"),
        "batch_no": ln.get("batch_no"),
        "expiry_date": ln.get("expiry_date"),
    }


def apply_changes(cur, data, changes_draft, keys, tid, ws, bound_user) -> Optional[str]:
    """把改动落到克隆草稿 data。金额仅单行(多行已在更上层拦)。

    返回诚实提示标记:分类用词真对不上任何准确科目、落到「其他」时返回 "cat_fallback_other"(调用方据此
    提示用户「先记其他·可改」并不学这条);其余 → None。"""
    notice = None
    if "vendor_name" in keys:
        data["supplier"] = {"name": changes_draft.vendor_name or "", "tax_id": None}
    if "doc_date" in keys:
        data["doc_date"] = changes_draft.doc_date
    if "category" in keys:
        cid, sid, matched = _resolve_category(cur, changes_draft.note or "", tid, ws, bound_user)
        data["category_id"] = cid
        for ln in data["lines"]:
            ln["category_id"] = cid
            ln["subcategory_id"] = sid
        if not matched:
            notice = "cat_fallback_other"
        # 不在此自动学(Phase B-1):改完追发「仅这次/这家/这套账」按钮,由用户显式确认是否沉淀成规则
        # (line_learn.offer/handle_postback)。网页改草稿仍走 learn_from_doc_edit 自动学(另一 surface)。
    if "payment_method" in keys:
        data["payment_method"] = changes_draft.payment_method or None
    if "amount" in keys:
        data["amount_override"] = None
        if data["lines"]:
            data["lines"][0]["unit_price"] = str(changes_draft.amount)
            data["lines"][0]["qty"] = "1"
    return notice


def learn_category(cur, *, tid, ws, supplier, cid, sid) -> None:
    """用户改分类 → 记住 本单 卖家/税号 → 科目(下次同商户票优先沿用)。空分类/无卖家 → no-op。

    键:税号(tax:<税号>)+ 归一卖家名(seller:<归一名>),复用 expense_learned 表前缀键,
    `_smart_category` 据此精确命中(优先级最高,规则/LLM 不能覆盖)。
    """
    if not cid:
        return
    # 学习是附带收益:任何失败(树查不到/cursor 异常)都只能跳过,绝不能拖垮改错/保存主流程。
    try:
        from services.expense import conversation, merchant
        from services.purchase import categories as cat_svc

        name = (supplier or {}).get("name") or ""
        tax = str((supplier or {}).get("tax_id") or "").strip()
        cat_name = sub_name = ""
        for p in cat_svc.get_tree(cur, tenant_id=tid, workspace_client_id=ws):
            if p.get("id") == cid:
                cat_name = p.get("name") or ""
                for c in p.get("children") or []:
                    if c.get("id") == sid:
                        sub_name = c.get("name") or ""
                break
        keys = []
        if tax:
            keys.append(f"tax:{tax}")
        nv = merchant.canonical_merchant(name, tax)
        if nv:
            keys.append(f"seller:{nv}")
        for key in keys:
            conversation.learn(
                cur,
                tenant_id=tid,
                workspace_client_id=ws,
                keyword=key,
                category_id=cid,
                subcategory_id=sid,
                category_name=cat_name,
                subcategory_name=sub_name,
            )
    except Exception as e:  # noqa: BLE001
        logger.warning("[learn_category] skipped: %s", str(e)[:160])


def learn_from_doc_edit(cur, tid, ws, data, lines) -> None:
    """网页详情改草稿保存 → 按本单 卖家/税号 记住头部科目(与 LINE 改错同口径 · UPSERT 幂等)。"""
    cid = (data or {}).get("category_id")
    if not cid:
        return
    sid = next(
        (ln.get("subcategory_id") for ln in (lines or []) if ln.get("category_id") == cid),
        None,
    )
    learn_category(cur, tid=tid, ws=ws, supplier=(data or {}).get("supplier"), cid=cid, sid=sid)


def _resolve_category(cur, text, tid, ws, bound_user):
    """用户改/教分类用词(「商品」「油费」「水电费」)→ 本套账真实树 (category_id, subcategory_id, matched)。

    ① 跨语言确定性同义层(category_ai.match_user_category:商品→ซื้อสินค้า·油费→ค่าน้ำมันเชื้อเพลิง·
       餐饮→ค่าอาหาร)——治中文词对不上泰文叶子落「其他」。② 记账归类口径(_fill_category:学习/关键词/
       LLM 从真树挑)。③ 都对不上 → 显式落「其他」叶子(matched=False·调用方诚实提示·不静默留空)。
    """
    from services.expense import category_ai, line_l2
    from services.line_binding import line_expense
    from services.purchase import categories as cat_svc

    tree = cat_svc.get_tree(cur, tenant_id=tid, workspace_client_id=ws)
    cid, sid = category_ai.match_user_category(text, tree)
    if cid:
        return cid, sid, True
    tmp = ExpenseDraft(note=text)
    api_key = line_l2.resolve_api_key(bound_user)
    line_expense._fill_category(cur, tmp, text, tree, tid, ws, api_key)
    if tmp.category_id:
        return tmp.category_id, tmp.subcategory_id, True
    ocid, osid = category_ai.other_category(tree)
    return ocid, osid, False
