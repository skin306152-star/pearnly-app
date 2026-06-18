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
from services.line_binding import line_reply

# 字段→规范键映射唯一源在 line_correct_i18n.FIELD_TO_KEY(此处复用·不再各维护一份)。
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

# 否定/指代填充(剥前缀后若只剩这些 → 没给真值,该问而非误当新卖家)。「ไม่ใช่」须在「ไม่」前。
_NEG_FILLER = (
    "ไม่ใช่",
    "ไม่ถูก",
    "ไม่",
    "คนนี้",
    "อันนี้",
    "ตัวนี้",
    "นี้",
    "不是",
    "不对",
    "这个",
    "那个",
    "错了",
    "错",
)


def try_correction_state(
    bound_user, reply_token, line_user_id, text, tid, ws, lang, *, quote_token=""
) -> bool:
    """改错会话态分发(最高优先):有 correct/correctval/correctclar pending 才接管,否则 False。"""
    with db.get_cursor_rls(tid) as cur:
        pend = conversation.peek_pending(cur, line_user_id=line_user_id)
    missing = str((pend or {}).get("missing") or "")
    if missing.startswith(line_correct._PREFIX):  # 最终 是/否(复用已 peek 的 pend·免重读)
        return line_correct.try_confirm(
            bound_user,
            reply_token,
            line_user_id,
            text,
            tid,
            ws,
            lang,
            quote_token=quote_token,
            pend=pend,
        )
    ctx = dict(quote_token=quote_token, line_user_id=line_user_id, tenant_id=tid)
    if missing.startswith(line_correct._VAL_PREFIX):
        return _handle_value(bound_user, reply_token, text, lang, tid, missing, ctx)
    if missing.startswith(line_correct._CLAR_PREFIX):
        return _handle_clarify_answer(bound_user, reply_token, text, lang, tid, missing, ctx)
    return False


def _say(reply_token, body, ctx):
    line_reply.reply_text_context(reply_token, body, **ctx)


def _handle_clarify_answer(bound_user, reply_token, text, lang, tid, missing, ctx) -> bool:
    """已问「改哪个字段」→ 用户答字段名(可同句带值):点名 → 走统一字段处理;没听出 → 再问一次。"""
    ws, doc_id = _parse_clar(missing)
    field = line_classify.detect_correction_field(text)
    if not field:
        _say(
            reply_token, ci.t(ci.CLARIFY_FIELDS, line_classify.detect_text_lang(text) or lang), ctx
        )
        return True
    return _route_field(bound_user, reply_token, text, lang, tid, ws, doc_id, field, ctx)


def _handle_value(bound_user, reply_token, text, lang, tid, missing, ctx) -> bool:
    """已问某字段「新值」→ 收值。若用户改口说另一个字段(带不带值)→ 切到该字段,不再纠结旧字段(#3)。"""
    ws, doc_id, field = _parse_val(missing)
    named = line_classify.detect_correction_field(text)
    if named and named != field:
        field = named  # 字段切换:同一张单内换字段,active_doc_id 不变
    return _route_field(bound_user, reply_token, text, lang, tid, ws, doc_id, field, ctx)


def _route_field(bound_user, reply_token, text, lang, tid, ws, doc_id, field, ctx) -> bool:
    """统一字段处理(澄清/切换/收值共用):明细/付款 → 详情页;没值 → 存态问值;有值 → 交风险三档执行。

    全程锁定 active_doc_id(从 pending 传入·不重新猜)→ 同一会话内不会回「找不到记录」(#5/#7)。
    有值后的「直接执行 / 确认 / 多行详情页」三档判定统一在 line_correct._apply_or_confirm。
    """
    reply_lang = line_classify.detect_text_lang(text) or lang
    luid = ctx["line_user_id"]
    if field in ("items", "payment"):
        line_correct._clear(tid, luid)
        _say(reply_token, ci.t(ci.MULTILINE_EDIT, reply_lang), ctx)
        return True
    value = _extract_value(text, field)
    if value in (None, ""):  # 只点了字段没给值 → 存「待该字段值」态,问新值(tier 1)
        line_correct._save_state(
            tid, ws, doc_id, luid, f"{line_correct._VAL_PREFIX}{ws}:{doc_id}:{field}"
        )
        _say(
            reply_token,
            ci.t(ci.ASK_VALUE, reply_lang, field=ci.field_label(field, reply_lang)),
            ctx,
        )
        return True
    return line_correct._apply_or_confirm(
        reply_token,
        bound_user,
        reply_lang,
        tid,
        ws,
        doc_id,
        {ci.FIELD_TO_KEY[field]: value},
        quote_token=ctx.get("quote_token", ""),
        line_user_id=luid,
    )


def _extract_value(text: str, field: str):
    """用户答 → 字段值:金额取数字;日期(相对/年首/ISO/DD-MM);卖家/分类剥前缀+否定填充。无 → None。"""
    if field == "amount":
        amt = lqe.parse_expense(text).amount
        return amt if (amt and amt > Decimal("0")) else None
    if field == "date":
        return lqe._parse_date(text)  # 相对词/年首/ISO/DD-MM 全在共用解析器
    cleaned = _strip_prefix(text)
    return cleaned or None


def _strip_prefix(text: str) -> str:
    """剥命令+字段+连接前缀 + 否定/指代填充,留真实值。

    「แก้ร้านค้าเป็น 7-11」→「7-11」;「ผู้ขายไม่ใช่คนนี้/卖家不是这个」→「」(没给真值·调用方据此再问)。
    """
    s = (text or "").strip()
    changed = True
    while changed:
        changed = False
        s2 = s.lstrip(" :=-")
        if s2 != s:
            s, changed = s2, True
        low = s.lower()
        for tok in _STRIP_TOKENS + _NEG_FILLER:
            if low.startswith(tok.lower()):
                s, changed = s[len(tok) :].strip(), True
                break
    return s.strip(" :=")


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
