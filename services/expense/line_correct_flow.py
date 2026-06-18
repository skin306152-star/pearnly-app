# -*- coding: utf-8 -*-
"""LINE 改错多轮会话态机(P1E-2 二轮:字段澄清 → 收新值 → 确认)。

接住「问了改哪个字段 / 问了新值」之后用户的下一句,把改错对话续成闭环(此前无状态 → 答案丢失,
退回『请回复记录』)。优先级最高:active pending correction > 引用提醒 > 记账 > 大脑。

三个 pending 态(复用 conversation.line_pending_entry · 不新建表):
  correctclar:<ws>:<doc>          —— 已问「改哪个字段」,等用户答字段名
  correctval:<ws>:<doc>:<field>   —— 已问「新值是什么」,等用户给值
  correct:<ws>:<doc>:<keys>       —— 已出「改成X吗」,等 是/否(在 line_correct.try_confirm)
"""

from __future__ import annotations

from decimal import Decimal

from core import db
from services.expense import conversation, line_classify, line_correct
from services.expense import line_correct_i18n as ci
from services.expense import line_quick_entry as lqe
from services.expense.expense_draft import ExpenseDraft
from services.line_binding import line_client, line_reply

# 改错字段 → 草稿/keys 的规范名(detect_correction_field 的 seller/date → vendor_name/doc_date)。
_FIELD_KEY = {
    "amount": "amount",
    "date": "doc_date",
    "seller": "vendor_name",
    "category": "category",
}

# 收新值时剥掉的前缀(命令词 + 连接词);标点已在入口 normalize_user_text 归一。
_STRIP_TOKENS = (
    "แก้ไข",
    "แก้",
    "เปลี่ยนเป็น",
    "เปลี่ยน",
    "เป็น",
    "คือ",
    "改成",
    "改为",
    "改到",
    "改",
    "是",
    "为",
    "change to",
    "change",
    "to",
    "edit",
    "set",
    "ร้านค้า",
    "ผู้ขาย",
    "ชื่อร้าน",
    "วันที่",
    "จำนวนเงิน",
    "ยอดเงิน",
    "หมวดหมู่",
    "หมวด",
    "卖家",
    "商家",
    "店名",
    "供应商",
    "日期",
    "金额",
    "分类",
    "科目",
    "seller",
    "vendor",
    "shop",
    "date",
    "amount",
    "total",
    "category",
)


def try_correction_state(
    bound_user, reply_token, line_user_id, text, tid, ws, lang, *, quote_token=""
) -> bool:
    """改错会话态分发(最高优先):有 correct/correctval/correctclar pending 才接管,否则 False。"""
    with db.get_cursor_rls(tid) as cur:
        pend = conversation.peek_pending(cur, line_user_id=line_user_id)
    missing = str((pend or {}).get("missing") or "")
    if missing.startswith(line_correct._PREFIX):  # 最终 是/否
        return line_correct.try_confirm(
            bound_user, reply_token, line_user_id, text, tid, ws, lang, quote_token=quote_token
        )
    ctx = dict(quote_token=quote_token, line_user_id=line_user_id, tenant_id=tid)
    if missing.startswith(line_correct._VAL_PREFIX):
        return _handle_value(bound_user, reply_token, text, lang, tid, missing, ctx)
    if missing.startswith(line_correct._CLAR_PREFIX):
        return _handle_clarify_answer(reply_token, text, lang, tid, missing, ctx)
    return False


def _say(reply_token, body, ctx):
    line_reply.reply_text_context(reply_token, body, **ctx)


def _handle_clarify_answer(reply_token, text, lang, tid, missing, ctx) -> bool:
    """已问「改哪个字段」→ 用户答字段名:点名 → 转「问新值」;明细/付款/多行金额 → 引导详情页。"""
    reply_lang = line_classify.detect_text_lang(text) or lang
    ws, doc_id = _parse_clar(missing)
    field = line_classify.detect_correction_field(text)
    if not field:
        _say(reply_token, ci.t(ci.CLARIFY_FIELDS, reply_lang), ctx)  # 没听出字段 → 再问一次
        return True
    if field in ("items", "payment"):
        _clear(tid, ctx["line_user_id"])
        _say(reply_token, ci.t(ci.MULTILINE_EDIT, reply_lang), ctx)
        return True
    if field == "amount" and _is_multiline(tid, ws, doc_id):
        _clear(tid, ctx["line_user_id"])
        _say(reply_token, ci.t(ci.MULTILINE_EDIT, reply_lang), ctx)
        return True
    line_correct._save_state(
        tid, ws, doc_id, ctx["line_user_id"], f"{line_correct._VAL_PREFIX}{ws}:{doc_id}:{field}"
    )
    _say(reply_token, ci.t(ci.ASK_VALUE, reply_lang, field=ci.field_label(field, reply_lang)), ctx)
    return True


def _handle_value(bound_user, reply_token, text, lang, tid, missing, ctx) -> bool:
    """已问「新值」→ 用户给值:解析出值 → 出「把{字段}从旧改成新吗?」确认;解析不出 → 再问一次。"""
    reply_lang = line_classify.detect_text_lang(text) or lang
    ws, doc_id, field = _parse_val(missing)
    value = _extract_value(text, field)
    if value in (None, ""):
        _say(
            reply_token,
            ci.t(ci.ASK_VALUE, reply_lang, field=ci.field_label(field, reply_lang)),
            ctx,
        )
        return True
    from services.purchase import docs as docs_svc

    with db.get_cursor_rls(tid) as cur:
        detail = docs_svc.get_doc(cur, tenant_id=tid, workspace_client_id=ws, doc_id=doc_id)
    if not detail:
        _clear(tid, ctx["line_user_id"])
        _say(reply_token, line_client.t_line(reply_lang, "exp_correct_none"), ctx)
        return True
    if field == "amount" and len(detail.get("lines") or []) > 1:
        _clear(tid, ctx["line_user_id"])
        _say(reply_token, ci.t(ci.MULTILINE_EDIT, reply_lang), ctx)
        return True
    key = _FIELD_KEY[field]
    changes_draft = ExpenseDraft(
        amount=value if field == "amount" else None,
        vendor_name=value if field == "seller" else "",
        doc_date=value if field == "date" else "",
        note=value if field == "category" else "",
    )
    # 存最终 是/否 待确认态(带新值 draft);用户回「是」→ line_correct.try_confirm → _apply。
    with db.get_cursor_rls(tid, commit=True) as cur:
        conversation.save_pending(
            cur,
            line_user_id=ctx["line_user_id"],
            tenant_id=tid,
            workspace_client_id=ws,
            draft=changes_draft,
            missing=f"{line_correct._PREFIX}{ws}:{doc_id}:{key}",
        )
    old = _old_value(detail, field)
    _say(
        reply_token,
        ci.t(
            ci.CONFIRM_FIELD_CHANGE,
            reply_lang,
            field=ci.field_label(field, reply_lang),
            old=old,
            new=value,
        ),
        ctx,
    )
    return True


def _extract_value(text: str, field: str):
    """用户答 → 字段值:金额取数字;日期相对/绝对解析;卖家/分类剥前缀取剩余文本。解析不出 → None。"""
    if field == "amount":
        amt = lqe.parse_expense(text).amount
        return amt if (amt and amt > Decimal("0")) else None
    if field == "date":
        return lqe._parse_date(text)
    cleaned = _strip_prefix(text)
    return cleaned or None


def _strip_prefix(text: str) -> str:
    """剥掉「改/แก้...เป็น/卖家/:」等命令+字段+连接前缀,留真实值(「แก้ร้านค้าเป็น 7-11」→「7-11」)。"""
    s = (text or "").strip()
    changed = True
    while changed:
        changed = False
        s2 = s.lstrip(" :=-")
        if s2 != s:
            s, changed = s2, True
        low = s.lower()
        for tok in _STRIP_TOKENS:
            if low.startswith(tok.lower()):
                s, changed = s[len(tok) :].strip(), True
                break
    return s.strip(" :=")


def _old_value(detail: dict, field: str) -> str:
    doc = detail.get("doc") or {}
    sup = detail.get("supplier") or {}
    val = {
        "amount": doc.get("grand_total"),
        "seller": sup.get("name"),
        "date": doc.get("doc_date"),
        "category": doc.get("category_name") or doc.get("category"),
    }.get(field)
    return str(val) if val not in (None, "") else "—"


def _is_multiline(tid, ws, doc_id) -> bool:
    from services.purchase import docs as docs_svc

    with db.get_cursor_rls(tid) as cur:
        detail = docs_svc.get_doc(cur, tenant_id=tid, workspace_client_id=ws, doc_id=doc_id)
    return bool(detail) and len(detail.get("lines") or []) > 1


def _clear(tid, line_user_id) -> None:
    with db.get_cursor_rls(tid, commit=True) as cur:
        conversation.clear_pending(cur, line_user_id=line_user_id)


def _parse_clar(missing: str):
    body = missing[len(line_correct._CLAR_PREFIX) :]
    ws_s, _, doc_id = body.partition(":")
    return _int(ws_s), doc_id


def _parse_val(missing: str):
    body = missing[len(line_correct._VAL_PREFIX) :]
    ws_s, _, rest = body.partition(":")
    doc_id, _, field = rest.partition(":")
    return _int(ws_s), doc_id, field


def _int(s):
    try:
        return int(s)
    except (ValueError, TypeError):
        return s
