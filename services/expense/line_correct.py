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
from services.line_binding import line_client, line_reply

_PREFIX = "correct:"
_YES = ("是", "对", "好", "确认", "ok", "yes", "ใช่", "ตกลง", "ถูก", "確認", "はい")
# 否定词优先于肯定:治子串塌缩——泰文「ไม่ใช่(不是)」含「ใช่(是)」、中文「不对」含「对」、
# 「不是」含「是」。漏了这条会把用户的「不」当成「是」照改账(真实事故:用户回 ไม่ใช่ 仍被改)。
_NO = (
    "不",
    "别",
    "取消",
    "no",
    "not",
    "wrong",
    "cancel",
    "ไม่",
    "ยกเลิก",
    "ผิด",
    "いいえ",
    "ない",
    "違",
    "キャンセル",
)


def _affirmative(text: str) -> bool:
    t = (text or "").strip().lower()
    if not t or any(n in t for n in _NO):
        return False
    return any(k in t for k in _YES)


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


# 定位失败 → 文案 key(高风险动作对象不明确不执行,提示 reply,绝不默认改最近一笔)。
_ERR_KEY = {
    "ambiguous": "line_need_reply_record",
    "ref_not_found": "guide_detail_list",
    "none": "exp_correct_none",
}


def request_correct(
    bound_user,
    reply_token,
    line_user_id,
    text,
    u,
    quoted_message_id,
    lang,
    tid,
    ws,
    *,
    quote_token="",
) -> bool:
    """edit 意图 → 收集改动 + 定位目标(引用>第N笔>明确上一笔)+ 单/多行规则 → 存待确认 + 回确认。

    确认/失败/引导回复引用用户触发改错的那条消息(quoteToken·展示);业务定位仍走 quotedMessageId。
    """
    from services.line_binding import line_message_refs
    from services.purchase import docs as docs_svc

    def _say(body):
        line_reply.reply_text_context(
            reply_token, body, quote_token=quote_token, line_user_id=line_user_id, tenant_id=tid
        )

    changes = _collect_changes(u)
    if not changes:
        _say(line_client.t_line(lang, "line_need_reply_record"))
        return True

    with db.get_cursor_rls(tid, commit=True) as cur:
        tgt = line_message_refs.resolve_target(
            cur,
            tenant_id=tid,
            ws=ws,
            line_user_id=line_user_id,
            quoted_message_id=quoted_message_id,
            text=text,
        )
        if tgt["error"]:
            _say(line_client.t_line(lang, _ERR_KEY[tgt["error"]]))
            return True
        target_id, ws_eff = tgt["doc_id"], tgt["ws"]
        detail = docs_svc.get_doc(cur, tenant_id=tid, workspace_client_id=ws_eff, doc_id=target_id)
        if not detail or (detail.get("doc") or {}).get("status") != "posted":
            _say(line_client.t_line(lang, "exp_correct_none"))
            return True
        if "amount" in changes and len(detail.get("lines") or []) > 1:
            # 多行票金额:不在 LINE 改(不重算/不摊销/不猜行)→ 引导到详情页逐行确认。
            _say(line_client.t_line(lang, "line_web_handoff"))
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
            workspace_client_id=ws_eff,
            draft=changes_draft,
            missing=f"{_PREFIX}{ws_eff}:{target_id}:{'|'.join(sorted(changes))}",
        )
        old_total = (detail.get("doc") or {}).get("grand_total")
    if set(changes) == {"amount"}:
        _say(line_client.t_line(lang, "exp_correct_confirm", old=old_total, new=changes["amount"]))
    else:
        _say(line_client.t_line(lang, "exp_correct_confirm2", changes=_summary(changes)))
    return True


def maybe_clarify_feedback(reply_token, text, lang, ws, quoted_message_id, ctx) -> bool:
    """采购改错澄清(P1E-2)= 命中「识别错了/不对/wrong/ผิด」且非具体「改成X」→ 本层接管,绝不当
    OCR 失败让重拍。优先级高于通用闲聊 / OCR 失败帮助 / 能力问答。按情形回(语言随输入):

      引用解析到采购单 + 点名「明细」或复杂多行金额 → 引导详情页核对(验收 #4)
      引用解析到采购单 + 点名「付款方式」→ 详情页改(LINE 不改付款)
      引用解析到采购单 + 点名金额/日期/卖家/分类 → 问新值(验收 #3)
      引用解析到采购单 + 没点名字段 → 列可改字段问改哪里(验收 #1)
      没解析到记录 → 引导回复要改的那条记录(验收 #5);仅当无引用且像新记账(有金额)才放行记账流。

    具体「改成X」交 edit 流(request_correct)·此处只澄清不改账。ctx 带 quote_token/line_user_id/
    tenant_id → 所有回复带引用,让用户知道在回应哪条。
    """
    from services.expense import line_classify
    from services.expense import line_correct_i18n as ci
    from services.expense import line_quick_entry as lqe

    if not (line_classify.is_correction_feedback(text) and not lqe.is_edit_request(text)):
        return False

    reply_lang = line_classify.detect_text_lang(text) or lang
    tid = ctx.get("tenant_id")

    def _say(body):
        line_reply.reply_text_context(reply_token, body, **ctx)

    from services.line_binding import line_message_refs
    from services.purchase import docs as docs_svc

    detail = None
    with db.get_cursor_rls(tid) as cur:
        tgt = line_message_refs.resolve_target(
            cur,
            tenant_id=tid,
            ws=ws,
            line_user_id=ctx.get("line_user_id"),
            quoted_message_id=quoted_message_id,
            text=text,
        )
        if not tgt.get("error"):
            detail = docs_svc.get_doc(
                cur, tenant_id=tid, workspace_client_id=tgt["ws"], doc_id=tgt["doc_id"]
            )

    if not detail:
        # 无引用且像一句新记账(有金额)→ 放行给记账流,不劫持「买错了 50」这类。
        if not quoted_message_id and lqe.parse_expense(text).has_amount():
            return False
        _say(line_client.t_line(reply_lang, "line_need_reply_record"))
        return True

    field = line_classify.detect_correction_field(text)
    multiline = len(detail.get("lines") or []) > 1
    if field == "items" or (field == "amount" and multiline):
        _say(ci.t(ci.DETAIL_INCOMPLETE, reply_lang))
    elif field == "payment":
        _say(line_client.t_line(reply_lang, "line_web_handoff"))
    elif field in ("amount", "date", "seller", "category"):
        _say(ci.t(ci.ASK_VALUE, reply_lang, field=ci.field_label(field, reply_lang)))
    else:
        _say(ci.t(ci.CLARIFY_FIELDS, reply_lang))
    return True


def try_confirm(
    bound_user, reply_token, line_user_id, text, tid, ws, lang, *, quote_token=""
) -> bool:
    """有待确认更正 + 这句肯定 → 执行;否定/其他 → 取消。非更正 pending → False(不干预补金额流)。

    回复引用用户确认/否定的那条消息(quoteToken)。"""
    from core.pos_api import PosError

    def _say(body):
        line_reply.reply_text_context(
            reply_token, body, quote_token=quote_token, line_user_id=line_user_id, tenant_id=tid
        )

    with db.get_cursor_rls(tid) as cur:
        pend = conversation.peek_pending(cur, line_user_id=line_user_id)
    if not pend or not str(pend.get("missing") or "").startswith(_PREFIX):
        return False
    if not _affirmative(text):
        with db.get_cursor_rls(tid, commit=True) as cur:
            conversation.clear_pending(cur, line_user_id=line_user_id)
        _say(line_client.t_line(lang, "exp_correct_cancel"))
        return True
    ws_eff, orig_id, keys = _parse_missing(pend["missing"])
    changes_draft = pend["draft"]
    try:
        with db.get_cursor_rls(tid, commit=True) as cur:
            conversation.clear_pending(cur, line_user_id=line_user_id)
            res = _apply(cur, bound_user, tid, ws_eff, orig_id, changes_draft, keys)
    except PosError as e:
        if (e.code or "") == "acct.period_closed":
            _say(line_client.t_line(lang, "exp_correct_closed"))
            return True
        raise
    if not res:
        _say(line_client.t_line(lang, "exp_correct_none"))
        return True
    key = "exp_correct_posted" if res["posted"] else "exp_correct_draft"
    _say(line_client.t_line(lang, key, new=res["total"]))
    return True


def _parse_missing(missing: str):
    """correct:<ws>:<doc_id>:<keys> → (ws:int, doc_id, [keys])。ws 编码进 missing,确认时按目标
    单所在套账操作(支持引用跨套账的旧单)。"""
    body = str(missing)[len(_PREFIX) :]
    ws_s, _, rest = body.partition(":")
    orig_id, _, keys = rest.partition(":")
    try:
        ws = int(ws_s)
    except (ValueError, TypeError):
        ws = ws_s
    return ws, orig_id, [k for k in keys.split("|") if k]


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
