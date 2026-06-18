# -*- coding: utf-8 -*-
"""LINE 对话内改错(改错闭环 · P1E-2 · 绝不静默覆盖)。

定位 引用卡片 > 第 N 笔 > 「上一笔」(绝不默认改最近一笔)。执行三档(_apply_or_confirm):草稿单非金额
字段直接改;已入账/改金额/多字段确认;多行金额引导详情页。_apply:草稿原地 update_draft、已入账
correct_doc(void+克隆,多行/票图/已结期红冲全保留)。会话态复用 conversation.pending,不新建表。
金额/税额/过账永不信 LLM。maybe_clarify_feedback:笼统「识别错了/ผิด」或引用点名字段 → 澄清/问新值,
绝不退化成 OCR 失败帮助。多轮态机在 line_correct_flow。
"""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from typing import Optional

from core import db
from services.expense import conversation
from services.expense.expense_draft import ExpenseDraft
from services.line_binding import line_client, line_reply

_PREFIX = "correct:"  # 待 是/否 确认(最终)
_CLAR_PREFIX = "correctclar:"  # 待用户选「改哪个字段」(多轮·correctclar:<ws>:<doc>)
_VAL_PREFIX = "correctval:"  # 待用户给「新值」(多轮·correctval:<ws>:<doc>:<field>)
_YES = ("是", "对", "好", "确认", "ok", "yes", "ใช่", "ตกลง", "ถูก", "確認", "はい")
# 否定词优先于肯定:治子串塌缩(「ไม่ใช่」含「ใช่」、「不对」含「对」)→ 否则把「不」当「是」照改账。
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
    """大脑槽位 → 要改字段(canonical)。科目只在无金额/卖家/日期时才从 note 取(避免误当科目)。"""
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


def _clear(tid, line_user_id) -> None:  # 清改错会话态(终态/直接执行前)
    with db.get_cursor_rls(tid, commit=True) as cur:
        conversation.clear_pending(cur, line_user_id=line_user_id)


def _field_old(detail: dict, key: str) -> str:
    """单字段旧值(确认文案「从 旧 改成 新」用)。取不到 → —。"""
    doc = detail.get("doc") or {}
    sup = detail.get("supplier") or {}
    val = {
        "amount": doc.get("grand_total"),
        "vendor_name": sup.get("name"),
        "doc_date": doc.get("doc_date"),
        "category": doc.get("category_name") or doc.get("category"),
    }.get(key)
    return str(val) if val not in (None, "") else "—"


def _apply_or_confirm(
    reply_token, bound_user, lang, tid, ws, doc_id, changes, *, quote_token="", line_user_id
) -> bool:
    """改错执行三档(产品原则):低风险(草稿 + 单个非金额字段)直接改回完成;高风险(已入账/改金额[税额
    重算]/多字段)出确认;多行金额 → 详情页。作废/不存在 → 诚实兜底。changes = 规范键 dict。"""
    from services.expense import line_correct_i18n as ci
    from services.purchase import docs as docs_svc

    def _say(body):
        line_reply.reply_text_context(
            reply_token, body, quote_token=quote_token, line_user_id=line_user_id, tenant_id=tid
        )

    with db.get_cursor_rls(tid) as cur:
        detail = docs_svc.get_doc(cur, tenant_id=tid, workspace_client_id=ws, doc_id=doc_id)
    status = (detail.get("doc") or {}).get("status") if detail else None
    if status not in ("posted", "draft"):
        _clear(tid, line_user_id)
        _say(line_client.t_line(lang, "exp_correct_none"))
        return True
    if "amount" in changes and len(detail.get("lines") or []) > 1:
        _clear(tid, line_user_id)
        _say(ci.t(ci.MULTILINE_EDIT, lang))
        return True
    changes_draft = ExpenseDraft(
        amount=changes.get("amount"),
        vendor_name=changes.get("vendor_name") or "",
        doc_date=changes.get("doc_date") or "",
        note=changes.get("category") or "",
    )
    keys = sorted(changes)
    # 高风险=已入账(void重建)/改金额(税额重算)/多字段;草稿单非金额=低风险直接改。
    high_risk = status == "posted" or "amount" in changes or len(changes) > 1
    if not high_risk:  # 低风险:直接执行,不二次确认
        with db.get_cursor_rls(tid, commit=True) as cur:
            conversation.clear_pending(cur, line_user_id=line_user_id)
            res = _apply(cur, bound_user, tid, ws, doc_id, changes_draft, keys)
        if not res:
            _say(line_client.t_line(lang, "exp_correct_none"))
            return True
        k = keys[0]
        _say(ci.t(ci.CHANGED_DONE, lang, field=ci.key_label(k, lang), new=changes[k]))
        return True
    with db.get_cursor_rls(tid, commit=True) as cur:
        conversation.save_pending(
            cur,
            line_user_id=line_user_id,
            tenant_id=tid,
            workspace_client_id=ws,
            draft=changes_draft,
            missing=f"{_PREFIX}{ws}:{doc_id}:{'|'.join(keys)}",
        )
    if len(changes) == 1:
        k = keys[0]
        _say(
            ci.t(
                ci.CONFIRM_FIELD_CHANGE,
                lang,
                field=ci.key_label(k, lang),
                old=_field_old(detail, k),
                new=changes[k],
            )
        )
    else:
        _say(ci.t(ci.CONFIRM_MULTI, lang, changes=_summary(changes)))
    return True


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
    """edit 意图(一次说清「X改成Y」)→ 收集改动 + 定位目标 → 委托 _apply_or_confirm(风险三档)。
    定位失败 → 提示 reply(绝不默认改最近一笔)。"""
    from services.line_binding import line_message_refs

    def _say(body):
        line_reply.reply_text_context(
            reply_token, body, quote_token=quote_token, line_user_id=line_user_id, tenant_id=tid
        )

    changes = _collect_changes(u)
    if not changes:
        _say(line_client.t_line(lang, "line_need_reply_record"))
        return True
    with db.get_cursor_rls(tid) as cur:
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
    return _apply_or_confirm(
        reply_token,
        bound_user,
        lang,
        tid,
        tgt["ws"],
        tgt["doc_id"],
        changes,
        quote_token=quote_token,
        line_user_id=line_user_id,
    )


def maybe_clarify_feedback(reply_token, text, lang, ws, quoted_message_id, ctx) -> bool:
    """采购改错澄清入口 = 命中「识别错了/ผิด」或引用卡片点名字段 → 本层接管,绝不退化成 OCR 失败重拍
    (优先级高于闲聊/OCR 帮助/能力问答)。点名字段 → 问新值并存会话态(correctval);笼统 → 列字段问改哪里
    并存 correctclar(下一句由 line_correct_flow 续接);明细/付款 → 详情页;没解析到记录 → 引导回复那条。
    具体「改成X」(is_edit)交 request_correct。ctx 带 quote_token/line_user_id/tenant_id(回复带引用)。"""
    from services.expense import line_classify
    from services.expense import line_correct_i18n as ci
    from services.expense import line_quick_entry as lqe

    # 触发:① 反馈词「识别错了/不对/wrong/ผิด」,或 ② 引用了卡片且点名了字段(如「ผู้ขายไม่ใช่คนนี้」)。
    # 后者让「卖家不是这个」这类在记账/收入识别(「ผู้ขาย」含「ขาย」)之前先被改错澄清接住。
    # 具体「改成X」(is_edit_request)交 edit 流(request_correct)·此处只澄清不改账。
    field = line_classify.detect_correction_field(text)
    triggered = line_classify.is_correction_feedback(text) or (bool(quoted_message_id) and field)
    if not triggered or lqe.is_edit_request(text):
        return False

    reply_lang = line_classify.detect_text_lang(text) or lang
    tid = ctx.get("tenant_id")

    def _say(body):
        line_reply.reply_text_context(reply_token, body, **ctx)

    from services.line_binding import line_message_refs
    from services.purchase import docs as docs_svc

    line_user_id = ctx.get("line_user_id")
    detail, doc_id, ws_eff = None, None, ws
    with db.get_cursor_rls(tid) as cur:
        tgt = line_message_refs.resolve_target(
            cur,
            tenant_id=tid,
            ws=ws,
            line_user_id=line_user_id,
            quoted_message_id=quoted_message_id,
            text=text,
        )
        if not tgt.get("error"):
            doc_id, ws_eff = tgt["doc_id"], tgt["ws"]
            detail = docs_svc.get_doc(cur, tenant_id=tid, workspace_client_id=ws_eff, doc_id=doc_id)

    if not detail:
        # 无引用且像一句新记账(有金额)→ 放行给记账流,不劫持「买错了 50」这类。
        if not quoted_message_id and lqe.parse_expense(text).has_amount():
            return False
        _say(line_client.t_line(reply_lang, "line_need_reply_record"))
        return True

    multiline = len(detail.get("lines") or []) > 1
    if field == "items" and not multiline:
        _say(ci.t(ci.DETAIL_INCOMPLETE, reply_lang))  # 笼统「明细错了」(单行也只能去详情核对)
    elif field == "items" or (field == "amount" and multiline):
        # 多行/明细行级改(总额或某行)→ 详情页(说明原因·非「明细可能不完整」OCR 文案·验收 #3/#4)
        _say(ci.t(ci.MULTILINE_EDIT, reply_lang))
    elif field == "payment":
        _say(line_client.t_line(reply_lang, "line_web_handoff"))
    elif field in ("amount", "date", "seller", "category"):
        # 点名了可改字段但没给值 → 存「待该字段新值」会话态,问新值(下一句直接答即可·验收 #3/#5)。
        _save_state(tid, ws_eff, doc_id, line_user_id, f"{_VAL_PREFIX}{ws_eff}:{doc_id}:{field}")
        _say(ci.t(ci.ASK_VALUE, reply_lang, field=ci.field_label(field, reply_lang)))
    else:
        # 没点名字段 → 存「待选字段」会话态,列字段问改哪里(下一句答字段名即可续接·验收 #7)。
        _save_state(tid, ws_eff, doc_id, line_user_id, f"{_CLAR_PREFIX}{ws_eff}:{doc_id}")
        _say(ci.t(ci.CLARIFY_FIELDS, reply_lang))
    return True


def _save_state(tid, ws, doc_id, line_user_id, missing: str) -> None:
    """存改错多轮会话态(待选字段 correctclar / 待新值 correctval)。draft 占位空·目标编码进 missing。"""
    with db.get_cursor_rls(tid, commit=True) as cur:
        conversation.save_pending(
            cur,
            line_user_id=line_user_id,
            tenant_id=tid,
            workspace_client_id=ws,
            draft=ExpenseDraft(),
            missing=missing,
        )


def try_confirm(
    bound_user, reply_token, line_user_id, text, tid, ws, lang, *, quote_token=""
) -> bool:
    """有待确认更正(correct:)+ 这句肯定 → 执行;否定 → 取消。非更正 pending → False。回复带引用。"""
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
    if res["posted"]:
        _say(line_client.t_line(lang, "exp_correct_posted", new=res["total"]))
    elif res.get("mode") == "draft_inplace":
        from services.expense import line_correct_i18n as ci

        _say(ci.t(ci.DRAFT_EDITED, lang, new=res["total"]))  # 草稿原地改·不提「冲销原单」
    else:
        _say(line_client.t_line(lang, "exp_correct_draft", new=res["total"]))
    return True


def _parse_missing(missing: str):
    """correct:<ws>:<doc_id>:<keys> → (ws:int, doc_id, [keys])。ws 编码进 missing 支持跨套账旧单。"""
    body = str(missing)[len(_PREFIX) :]
    ws_s, _, rest = body.partition(":")
    orig_id, _, keys = rest.partition(":")
    try:
        ws = int(ws_s)
    except (ValueError, TypeError):
        ws = ws_s
    return ws, orig_id, [k for k in keys.split("|") if k]


def _apply(cur, bound_user, tid, ws, orig_id, changes_draft, keys) -> Optional[dict]:
    """应用改动:已入账 → void 原单 + 克隆草稿 + 改 + auto_book 过账;草稿 → 原地改(不冲销)。
    返回 {new_id, posted, total, mode}(mode 供回执选措辞);作废/不存在 → None。"""
    from services.purchase import correct as correct_svc
    from services.purchase import docs as docs_svc
    from services.purchase import posting as posting_svc
    from services.purchase import settings as settings_svc

    detail = docs_svc.get_doc(cur, tenant_id=tid, workspace_client_id=ws, doc_id=orig_id)
    status = (detail.get("doc") or {}).get("status") if detail else None
    if status not in ("posted", "draft"):
        return None
    uid = str(bound_user["id"]) if bound_user.get("id") else None
    if status == "posted":
        clone = correct_svc.correct_doc(
            cur, tenant_id=tid, workspace_client_id=ws, doc_id=orig_id, created_by=uid
        )
        edit_id = str(clone["doc"]["id"])
        data = _detail_to_data(clone)
        mode = "posted_reclone"
    else:  # 草稿:原地改(无需冲销·update_draft 直接重算重写行)
        edit_id = str(orig_id)
        data = _detail_to_data(detail)
        mode = "draft_inplace"
    _apply_changes(cur, data, changes_draft, keys, tid, ws, bound_user)
    cfg = settings_svc.get_settings(cur, tenant_id=tid, workspace_client_id=ws)
    res = docs_svc.update_draft(
        cur,
        tenant_id=tid,
        workspace_client_id=ws,
        created_by=uid,
        doc_id=edit_id,
        data=data,
        settings=cfg,
    )
    total = (res.get("doc") or {}).get("grand_total")
    # 草稿原地改:保持草稿(待用户卡片确认),不自动过账;已入账更正:按 auto_book 决定是否重新过账。
    if status == "posted" and cfg.get("auto_book"):
        posting_svc.post_doc(
            cur,
            tenant_id=tid,
            workspace_client_id=ws,
            doc_id=edit_id,
            auto_stock_in=False,
            created_by=uid,
        )
        return {"new_id": edit_id, "posted": True, "total": total, "mode": mode}
    return {"new_id": edit_id, "posted": False, "total": total, "mode": mode}


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
