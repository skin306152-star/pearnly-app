# -*- coding: utf-8 -*-
"""LINE 更正已入账记录 = 冲销原单 + 按新值重建草稿(PO-13 · 绝不静默覆盖)。

「上一笔改成 550」(大脑判 edit + 抽出 amount)→ 找该用户最近一笔 LINE 已入账单 →
回原摘要请确认 → 用户回「是」→ void_doc 冲销 + create_doc 按新金额复制成新草稿 →
按 auto_book(已定决策 1)决定是否过账。新单 ocr_raw.corrected_from 记原单 id(审计链),
原单 status=void 可查。两轮确认复用 conversation pending(missing=correct:<id>:<amount>),不新建表。
"""

from __future__ import annotations

from decimal import Decimal
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


def request_correct(bound_user, reply_token, line_user_id, new_amount, lang, tid, ws) -> bool:
    """edit + 有新金额 → 找上一笔已入账单,回摘要请确认(存 pending)。无单 → 诚实告知。"""
    with db.get_cursor_rls(tid, commit=True) as cur:
        row = _find_last_posted(cur, tenant_id=tid, ws=ws)
        if not row:
            line_client.reply_text(reply_token, line_client.t_line(lang, "exp_correct_none"))
            return True
        conversation.save_pending(
            cur,
            line_user_id=line_user_id,
            tenant_id=tid,
            workspace_client_id=ws,
            draft=ExpenseDraft(amount=Decimal(str(new_amount))),
            missing=f"{_PREFIX}{row['id']}:{new_amount}",
        )
        old = row["grand_total"]
    line_client.reply_text(
        reply_token, line_client.t_line(lang, "exp_correct_confirm", old=old, new=new_amount)
    )
    return True


def try_confirm(bound_user, reply_token, line_user_id, text, tid, ws, lang) -> bool:
    """有待确认更正 + 这句肯定 → 执行;否定/其他 → 取消。非更正 pending → False(不干预补金额流)。"""
    with db.get_cursor_rls(tid) as cur:
        pend = conversation.peek_pending(cur, line_user_id=line_user_id)
    if not pend or not str(pend.get("missing") or "").startswith(_PREFIX):
        return False
    if not _affirmative(text):
        with db.get_cursor_rls(tid, commit=True) as cur:
            conversation.clear_pending(cur, line_user_id=line_user_id)
        line_client.reply_text(reply_token, line_client.t_line(lang, "exp_correct_cancel"))
        return True
    orig_id, new_amount = _parse(pend["missing"])
    with db.get_cursor_rls(tid, commit=True) as cur:
        conversation.clear_pending(cur, line_user_id=line_user_id)
        res = _apply(cur, bound_user, tid, ws, orig_id, new_amount)
    if not res:
        line_client.reply_text(reply_token, line_client.t_line(lang, "exp_correct_none"))
        return True
    key = "exp_correct_posted" if res["posted"] else "exp_correct_draft"
    line_client.reply_text(reply_token, line_client.t_line(lang, key, new=new_amount))
    return True


def _parse(missing: str):
    orig_id, _, amt = str(missing)[len(_PREFIX) :].partition(":")
    return orig_id, amt


def _apply(cur, bound_user, tid, ws, orig_id, new_amount) -> Optional[dict]:
    """冲销原单 + 按新金额复制新草稿 + auto_book 决定过账。原单已非 posted → None(诚实)。"""
    from services.purchase import docs as docs_svc, posting as posting_svc
    from services.purchase import settings as settings_svc

    detail = docs_svc.get_doc(cur, tenant_id=tid, workspace_client_id=ws, doc_id=orig_id)
    if not detail or (detail.get("doc") or {}).get("status") != "posted":
        return None
    uid = str(bound_user["id"]) if bound_user.get("id") else None
    posting_svc.void_doc(cur, tenant_id=tid, workspace_client_id=ws, doc_id=orig_id, created_by=uid)
    cfg = settings_svc.get_settings(cur, tenant_id=tid, workspace_client_id=ws)
    created = docs_svc.create_doc(
        cur,
        tenant_id=tid,
        workspace_client_id=ws,
        created_by=uid,
        data=_corrected_data(detail, new_amount, orig_id),
        settings=cfg,
        status="draft",
    )
    new_id = str(created["doc"]["id"])
    if cfg.get("auto_book"):
        posting_svc.post_doc(
            cur,
            tenant_id=tid,
            workspace_client_id=ws,
            doc_id=new_id,
            auto_stock_in=False,
            created_by=uid,
        )
        return {"new_id": new_id, "posted": True}
    return {"new_id": new_id, "posted": False}


def _corrected_data(detail, new_amount, orig_id) -> dict:
    """复制原单(供应商/分类/类型/日期)+ 改单行金额(LINE 费用单单行)+ 记 corrected_from 审计链。"""
    doc = detail.get("doc") or {}
    sup = detail.get("supplier") or {}
    lines = detail.get("lines") or []
    desc = (lines[0].get("description") if lines else "") or "LINE บันทึก"
    return {
        "doc_kind": doc.get("doc_kind") or "expense",
        "source": "line",
        "doc_date": doc.get("doc_date"),
        "category_id": doc.get("category_id"),
        "payment_status": doc.get("payment_status") or "unpaid",
        "supplier": {"name": sup.get("name") or "", "tax_id": sup.get("tax_id")},
        "ocr_raw": {"corrected_from": orig_id},
        "lines": [
            {
                "item_type": "goods",
                "description": desc,
                "qty": "1",
                "unit_price": str(new_amount),
                "vat_rate": 0,
                "wht_rate": 0,
                "category_id": doc.get("category_id"),
            }
        ],
    }
