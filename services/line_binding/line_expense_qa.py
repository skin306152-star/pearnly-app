# -*- coding: utf-8 -*-
"""LINE 文本路 · 查账/问答/撤销 回复(从 line_expense 抽出 · 控 <500)。

只读 QA + 撤销四件:本月汇总 / 本月明细 / 撤销上一笔 / 知识中心问答。
都是 DB 真查(绝不让模型编数字)+ line_i18n 模板回复。逻辑零改,纯搬家。
"""

from __future__ import annotations

import logging

from core import db
from services.line_binding import line_client

logger = logging.getLogger(__name__)


def reply_summary(reply_token, lang, tid, ws) -> None:
    """查账汇总(本月已入账 + 按分类拆解)· DB 真查,绝不让模型编数字。"""
    from services.expense import line_qa

    try:
        with db.get_cursor_rls(tid) as cur:
            s = line_qa.month_summary(cur, tenant_id=tid, workspace_client_id=ws)
    except Exception:
        logger.exception("[line] summary failed")
        line_client.reply_text(reply_token, line_client.t_line(lang, "exp_q_not_found"))
        return
    if s["count"] == 0:
        line_client.reply_text(reply_token, line_client.t_line(lang, "exp_sum_empty"))
        return
    uncat = line_client.t_line(lang, "exp_uncat")
    lines = [line_client.t_line(lang, "exp_sum_head", amount=s["total"], n=s["count"])]
    for c in s["by_category"][:6]:
        lines.append(f"• {c['name'] or uncat}: ฿{c['amount']} ({c['count']})")
    line_client.reply_text(reply_token, "\n".join(lines))


def reply_detail(reply_token, lang, tid, ws, line_user_id=None) -> None:
    """查明细(本月逐笔)· DB 真查 → 列表。存有序 doc_id 入会话态供「第 N 笔改成…」定位(P2)。"""
    from services.expense import line_qa

    try:
        with db.get_cursor_rls(tid) as cur:
            rows = line_qa.month_detail(cur, tenant_id=tid, workspace_client_id=ws, limit=10)
    except Exception:
        logger.exception("[line] detail failed")
        line_client.reply_text(reply_token, line_client.t_line(lang, "exp_q_not_found"))
        return
    if not rows:
        line_client.reply_text(reply_token, line_client.t_line(lang, "exp_sum_empty"))
        return
    uncat = line_client.t_line(lang, "exp_uncat")
    lines = [line_client.t_line(lang, "exp_detail_head", n=len(rows))]
    for i, r in enumerate(rows, 1):
        tail = f" · {r['vendor']}" if r["vendor"] else ""
        lines.append(f"{i}. {r['date']} {r['category'] or uncat} ฿{r['amount']}{tail}")
    if line_user_id:
        _remember_detail_order(tid, ws, line_user_id, [r["id"] for r in rows])
    line_client.reply_text(reply_token, "\n".join(lines))


def _remember_detail_order(tid, ws, line_user_id, ids) -> None:
    """把列表的 doc_id 顺序记进会话态(missing=detail:id1,id2,…),供下一句「第 N 笔改成…」定位。"""
    from services.expense import conversation
    from services.expense.expense_draft import ExpenseDraft

    try:
        with db.get_cursor_rls(tid, commit=True) as cur:
            conversation.save_pending(
                cur,
                line_user_id=line_user_id,
                tenant_id=tid,
                workspace_client_id=ws,
                draft=ExpenseDraft(),
                missing="detail:" + ",".join(ids),
            )
    except Exception:
        logger.warning("[line] remember detail order failed; 第N笔 定位将回落上一笔")


def reply_undo(bound_user, reply_token, lang, tid, ws) -> None:
    """撤销上一笔(LINE 记的、已入账正式单)· void_doc 冲销,不物理删。无 → 诚实告知。"""
    uid = str(bound_user["id"]) if bound_user.get("id") else None
    try:
        from services.purchase import posting as posting_svc

        with db.get_cursor_rls(tid, commit=True) as cur:
            cur.execute(
                "SELECT id, grand_total FROM purchase_docs "
                "WHERE tenant_id = %s AND workspace_client_id = %s AND source = 'line' "
                "AND status = 'posted' ORDER BY created_at DESC LIMIT 1",
                (tid, ws),
            )
            row = cur.fetchone()
            if not row:
                line_client.reply_text(reply_token, line_client.t_line(lang, "exp_undo_none"))
                return
            res = posting_svc.void_doc(
                cur, tenant_id=tid, workspace_client_id=ws, doc_id=str(row["id"]), created_by=uid
            )
            amt = (res.get("doc") or {}).get("grand_total") or row["grand_total"]
        line_client.reply_text(reply_token, line_client.t_line(lang, "exp_undo_done", amount=amt))
    except Exception:
        logger.exception("[line] undo failed")
        line_client.reply_text(reply_token, line_client.t_line(lang, "exp_undo_none"))


def reply_question(reply_token, lang, tid, question) -> None:
    """问答 · 知识中心带出处;查不到诚实兜底 + 指路(绝不编造)。"""
    from services.expense import line_qa

    try:
        with db.get_cursor_rls(tid) as cur:
            res = line_qa.knowledge_answer(cur, tenant_id=tid, question=question)
    except Exception:
        logger.exception("[line] question failed")
        res = None
    if not res:
        line_client.reply_text(reply_token, line_client.t_line(lang, "exp_q_not_found"))
        return
    src = ", ".join(res["citations"]) if res.get("citations") else ""
    body = res["answer"]
    if src:
        body += "\n\n" + line_client.t_line(lang, "exp_q_source", src=src)
    line_client.reply_text(reply_token, body)
