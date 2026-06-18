# -*- coding: utf-8 -*-
"""LINE 改错的「详情 ↔ update_draft 入参」转换 + 字段落地(从 line_correct 拆出 · 纯数据变换)。

忠实搬运总额相关列(qty/单价/折扣/税率/多行原样·总额不漂),只把用户指定的字段改到克隆草稿。
金额仅作用单行(多行已在更上层拦),绝不让代码/LLM 重算多行明细。
"""

from __future__ import annotations

from services.expense.expense_draft import ExpenseDraft


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


def apply_changes(cur, data, changes_draft, keys, tid, ws, bound_user) -> None:
    """把改动落到克隆草稿 data。金额仅单行(多行已在更上层拦)。"""
    if "vendor_name" in keys:
        data["supplier"] = {"name": changes_draft.vendor_name or "", "tax_id": None}
    if "doc_date" in keys:
        data["doc_date"] = changes_draft.doc_date
    if "category" in keys:
        cid, sid = _resolve_category(cur, changes_draft.note or "", tid, ws, bound_user)
        data["category_id"] = cid
        for ln in data["lines"]:
            ln["category_id"] = cid
            ln["subcategory_id"] = sid
    if "payment_method" in keys:
        data["payment_method"] = changes_draft.payment_method or None
    if "amount" in keys:
        data["amount_override"] = None
        if data["lines"]:
            data["lines"][0]["unit_price"] = str(changes_draft.amount)
            data["lines"][0]["qty"] = "1"


def _resolve_category(cur, text, tid, ws, bound_user):
    """新科目文本(「水电费」)→ 在本套账真实树里解析 (category_id, subcategory_id)(复用记账归类口径)。"""
    from services.expense import line_l2
    from services.line_binding import line_expense
    from services.purchase import categories as cat_svc

    tree = cat_svc.get_tree(cur, tenant_id=tid, workspace_client_id=ws)
    tmp = ExpenseDraft(note=text)
    api_key = line_l2.resolve_api_key(bound_user)
    line_expense._fill_category(cur, tmp, text, tree, tid, ws, api_key)
    return tmp.category_id, tmp.subcategory_id
