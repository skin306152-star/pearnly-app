# -*- coding: utf-8 -*-
"""LINE 对话内改错 = 冲销原单 + 忠实克隆草稿 + 应用改动(改错闭环 · P2 · 绝不静默覆盖)。

支持:改金额(仅单行票)/ 改卖家 / 改日期 / 改科目;按「第 N 笔」(查明细列表序号)或「上一笔」
定位目标。大脑(line_agent.understand)抽出改什么字段→什么值,这层确定性执行:
  请确认 → 用户回「是」→ correct_doc(void 原单 + DB 级照搬克隆,多行/总额/票图/已结期红冲全保留)
  → 对克隆草稿 update_draft 应用改动 → 按 auto_book 决定过账。
金额/总额永不信 LLM:单行票改金额=设该行单价;多行票金额不在 LINE 改(不重算/不摊销/不猜行)→
引导网页明细页逐行确认。两轮确认复用 conversation.pending(missing=correct:<id>:<keys>),不新建表。
"""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from typing import Optional

from core import db
from services.expense import conversation
from services.expense.expense_draft import ExpenseDraft
from services.line_binding import line_client

_PREFIX = "correct:"
_YES = ("是", "对", "好", "确认", "ok", "yes", "ใช่", "ตกลง", "ถูก", "確認", "はい")


def _affirmative(text: str) -> bool:
    t = (text or "").strip().lower()
    return any(k in t for k in _YES)


def _find_last_posted(cur, *, tenant_id, ws):
    cur.execute(
        "SELECT id, grand_total FROM purchase_docs "
        "WHERE tenant_id = %s AND workspace_client_id = %s AND source = 'line' "
        "AND status = 'posted' ORDER BY created_at DESC LIMIT 1",
        (tenant_id, ws),
    )
    return cur.fetchone()


def _collect_changes(u: dict) -> dict:
    """大脑槽位 → 要改的字段(canonical)。amount/vendor_name/doc_date/category(科目依据=note)。

    科目只在「无金额/卖家/日期」时才从 note 取(「改成水电费」),避免把卖家/物品名误当科目。
    """
    changes: dict = {}
    amt = u.get("amount")
    if amt not in (None, "", 0):
        try:
            a = Decimal(str(amt))
            if a > 0:
                changes["amount"] = a
        except (InvalidOperation, ValueError):
            pass
    vendor = (u.get("vendor_name") or "").strip()
    if vendor:
        changes["vendor_name"] = vendor
    d = (u.get("date") or "").strip()
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", d):
        changes["doc_date"] = d
    note = (u.get("note") or "").strip()
    if note and not changes:
        changes["category"] = note
    return changes


def _summary(changes: dict) -> str:
    """改动摘要(确认卡用 · emoji 前缀免逐字段翻译标签)。"""
    parts = []
    if "amount" in changes:
        parts.append(f"฿{changes['amount']}")
    if "vendor_name" in changes:
        parts.append(f"🏪 {changes['vendor_name']}")
    if "doc_date" in changes:
        parts.append(f"📅 {changes['doc_date']}")
    if "category" in changes:
        parts.append(f"🏷️ {changes['category']}")
    return " · ".join(parts)


def _resolve_target(cur, *, line_user_id, text, tenant_id, ws):
    """定位要改的单:有序号「第 N 笔」→ 查明细列表第 N 项;否则「上一笔」LINE 已入账单。

    返回 (target_id, err_key, n)。err_key 非空表示无法定位(回该文案)。
    """
    n = None
    try:
        from services.expense import line_quick_entry as lqe

        n = lqe.parse_ordinal(text)
    except Exception:  # noqa: BLE001
        n = None
    if n:
        pend = conversation.peek_pending(cur, line_user_id=line_user_id)
        missing = str((pend or {}).get("missing") or "")
        if not missing.startswith("detail:"):
            return None, "exp_correct_no_list", n
        ids = [x for x in missing[len("detail:") :].split(",") if x]
        if 1 <= n <= len(ids):
            return ids[n - 1], None, n
        return None, "exp_correct_no_list", n
    row = _find_last_posted(cur, tenant_id=tenant_id, ws=ws)
    if not row:
        return None, "exp_correct_none", None
    return str(row["id"]), None, None


def request_correct(bound_user, reply_token, line_user_id, text, u, lang, tid, ws) -> bool:
    """edit 意图 → 收集改动 + 定位目标 + 单/多行规则 → 存待确认 + 回确认。无法处理时诚实兜底。"""
    changes = _collect_changes(u)
    if not changes:
        line_client.reply_text(reply_token, line_client.t_line(lang, "exp_edit_web"))
        return True
    from services.purchase import docs as docs_svc

    with db.get_cursor_rls(tid, commit=True) as cur:
        target_id, err_key, n = _resolve_target(
            cur, line_user_id=line_user_id, text=text, tenant_id=tid, ws=ws
        )
        if err_key:
            line_client.reply_text(reply_token, line_client.t_line(lang, err_key, n=n))
            return True
        detail = docs_svc.get_doc(cur, tenant_id=tid, workspace_client_id=ws, doc_id=target_id)
        if not detail or (detail.get("doc") or {}).get("status") != "posted":
            line_client.reply_text(reply_token, line_client.t_line(lang, "exp_correct_none"))
            return True
        if "amount" in changes and len(detail.get("lines") or []) > 1:
            # 多行票金额:不在 LINE 改(不重算/不摊销/不猜行)→ 引导网页明细逐行确认。
            line_client.reply_text(
                reply_token, line_client.t_line(lang, "exp_correct_multiline_amount")
            )
            return True
        changes_draft = ExpenseDraft(
            amount=changes.get("amount"),
            vendor_name=changes.get("vendor_name") or "",
            doc_date=changes.get("doc_date") or "",
            note=changes.get("category") or "",
        )
        conversation.save_pending(
            cur,
            line_user_id=line_user_id,
            tenant_id=tid,
            workspace_client_id=ws,
            draft=changes_draft,
            missing=f"{_PREFIX}{target_id}:{'|'.join(sorted(changes))}",
        )
        old_total = (detail.get("doc") or {}).get("grand_total")
    if set(changes) == {"amount"}:
        line_client.reply_text(
            reply_token,
            line_client.t_line(lang, "exp_correct_confirm", old=old_total, new=changes["amount"]),
        )
    else:
        line_client.reply_text(
            reply_token, line_client.t_line(lang, "exp_correct_confirm2", changes=_summary(changes))
        )
    return True


def try_confirm(bound_user, reply_token, line_user_id, text, tid, ws, lang) -> bool:
    """有待确认更正 + 这句肯定 → 执行;否定/其他 → 取消。非更正 pending → False(不干预补金额流)。"""
    from core.pos_api import PosError

    with db.get_cursor_rls(tid) as cur:
        pend = conversation.peek_pending(cur, line_user_id=line_user_id)
    if not pend or not str(pend.get("missing") or "").startswith(_PREFIX):
        return False
    if not _affirmative(text):
        with db.get_cursor_rls(tid, commit=True) as cur:
            conversation.clear_pending(cur, line_user_id=line_user_id)
        line_client.reply_text(reply_token, line_client.t_line(lang, "exp_correct_cancel"))
        return True
    orig_id, keys = _parse_missing(pend["missing"])
    changes_draft = pend["draft"]
    try:
        with db.get_cursor_rls(tid, commit=True) as cur:
            conversation.clear_pending(cur, line_user_id=line_user_id)
            res = _apply(cur, bound_user, tid, ws, orig_id, changes_draft, keys)
    except PosError as e:
        if (e.code or "") == "acct.period_closed":
            line_client.reply_text(reply_token, line_client.t_line(lang, "exp_correct_closed"))
            return True
        raise
    if not res:
        line_client.reply_text(reply_token, line_client.t_line(lang, "exp_correct_none"))
        return True
    key = "exp_correct_posted" if res["posted"] else "exp_correct_draft"
    line_client.reply_text(reply_token, line_client.t_line(lang, key, new=res["total"]))
    return True


def _parse_missing(missing: str):
    body = str(missing)[len(_PREFIX) :]
    orig_id, _, keys = body.partition(":")
    return orig_id, [k for k in keys.split("|") if k]


def _apply(cur, bound_user, tid, ws, orig_id, changes_draft, keys) -> Optional[dict]:
    """冲销原单 + 忠实克隆草稿 + 应用改动 + auto_book 决定过账。原单非 posted → None(诚实)。"""
    from services.purchase import correct as correct_svc
    from services.purchase import docs as docs_svc
    from services.purchase import posting as posting_svc
    from services.purchase import settings as settings_svc

    detail = docs_svc.get_doc(cur, tenant_id=tid, workspace_client_id=ws, doc_id=orig_id)
    if not detail or (detail.get("doc") or {}).get("status") != "posted":
        return None
    uid = str(bound_user["id"]) if bound_user.get("id") else None
    clone = correct_svc.correct_doc(
        cur, tenant_id=tid, workspace_client_id=ws, doc_id=orig_id, created_by=uid
    )
    new_id = str(clone["doc"]["id"])
    data = _detail_to_data(clone)
    _apply_changes(cur, data, changes_draft, keys, tid, ws, bound_user)
    cfg = settings_svc.get_settings(cur, tenant_id=tid, workspace_client_id=ws)
    res = docs_svc.update_draft(
        cur,
        tenant_id=tid,
        workspace_client_id=ws,
        created_by=uid,
        doc_id=new_id,
        data=data,
        settings=cfg,
    )
    total = (res.get("doc") or {}).get("grand_total")
    if cfg.get("auto_book"):
        posting_svc.post_doc(
            cur,
            tenant_id=tid,
            workspace_client_id=ws,
            doc_id=new_id,
            auto_stock_in=False,
            created_by=uid,
        )
        return {"new_id": new_id, "posted": True, "total": total}
    return {"new_id": new_id, "posted": False, "total": total}


def _detail_to_data(detail: dict) -> dict:
    """get_doc 详情 → update_draft 入参(忠实:保多行 + 总额相关列原样,只待 _apply_changes 改指定字段)。"""
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


def _apply_changes(cur, data, changes_draft, keys, tid, ws, bound_user) -> None:
    """把改动落到克隆草稿 data。金额仅单行(多行已在 request 阶段拦),不让代码/LLM 重算多行明细。"""
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
