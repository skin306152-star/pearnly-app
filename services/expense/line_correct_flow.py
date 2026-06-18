# -*- coding: utf-8 -*-
"""LINE 改错多轮会话态机 + 澄清入口(P1E-2 收口)。

统一决策(产业级·学 Paypers 的稳不学它的慢):任何改错 pending 在身,新一句按优先级裁决——
取消(明确)> 删除(明确)> 点名字段(确认阶段切换 / 收值改口 / 待选答字段,带值即直接走风险三档)>
按阶段(confirm 是/否、收值、待选重问)。绝不在 active_doc_id 内退回「请长按回复/找不到记录」。

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
from services.line_binding import line_client, line_message_refs, line_reply

# 收新值时剥掉的前缀(命令词 + 连接词 + 字段名);标点已在入口 normalize_user_text 归一。
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
    "ชื่อร้าน",
    "ร้าน",  # 简写「ร้าน」须在「ร้านค้า/ชื่อร้าน」之后剥(长词先匹配·防剥成「ค้าเป็น…」)
    "ผู้ขาย",
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

_PREFIXES = (
    line_correct._PREFIX,
    line_correct._VAL_PREFIX,
    line_correct._CLAR_PREFIX,
    line_correct._ACTIVE_PREFIX,
)


def _say(reply_token, body, ctx):
    line_reply.reply_text_context(reply_token, body, **ctx)


# 明显新记账句的开头记账动词(P1E-3):即便在 active 续接态也打断 correction,放行记账解析。
_NEW_EXPENSE_LEAD = (
    "วันนี้ใช้จ่าย",
    "วันนี้จ่าย",
    "ใช้จ่าย",
    "ซื้อ",
    "จ่าย",
    "spent",
    "expense",
    "今天花",
    "今天买",
    "买了",
    "花了",
)


def _looks_like_new_expense(text: str) -> bool:
    """明显新记账意图?(多组 item+amount,或记账动词开头)。

    P1E-3:active 续接态遇此即放行给记账流(不被句中「ผู้ขาย/ร้าน」字段词误当卖家新值吞掉)。
    correction-like 单字段「X เป็น Y」不在此列(parse_multi <2 且非动词开头)→ 仍优先 correction。
    """
    s = (text or "").strip()
    low = s.lower()
    if any(low.startswith(p.lower()) for p in _NEW_EXPENSE_LEAD):
        return True
    return lqe.parse_multi(s) is not None


def is_correction_like(text: str) -> bool:
    """改错语义?(点名字段 / 编辑词 / 反馈词 / 取消 / 删除)。问句不算(交查账)。

    安全闸用:命中即绝不进 auto_book 记账(账务级红线·「ร้านค้าเป็น 7-11」不得新建 11 THB)。
    """
    if lqe.is_question(text):
        return False
    return bool(
        line_classify.detect_correction_field(text)
        or line_classify.is_correction_feedback(text)
        or lqe.is_edit_request(text)
        or line_classify.is_cancel_intent(text)
        or line_classify.is_delete_intent(text)
    )


def route(
    bound_user, reply_token, line_user_id, text, lang, tid, ws, quoted_message_id, ctx
) -> bool:
    """改错路由总入口(在记账/大脑之前):会话态续接 > 引用澄清/直接改 > 引用取消/删除。

    ★安全闸(账务红线):correction-like 文本绝不落记账。定位不到(无引用/无 active)→ 提示「回复要改
    的那条记录」并 return True 拦在记账之前,绝不新建支出。任一接管 → True;非 correction → False。
    """
    qt = ctx.get("quote_token", "")
    if try_correction_state(
        bound_user,
        reply_token,
        line_user_id,
        text,
        tid,
        ws,
        lang,
        quoted_message_id=quoted_message_id,
        quote_token=qt,
    ):
        return True
    if maybe_clarify_feedback(bound_user, reply_token, text, lang, ws, quoted_message_id, ctx):
        return True
    if try_void_quoted(
        bound_user, reply_token, text, lang, tid, ws, line_user_id, quoted_message_id, qt
    ):
        return True
    # 改错语义但没定位到记录 → 提示回复记录,绝不记账(账务红线)。但明显新记账句(多项/记账动词开头·
    # 即便含「ผู้ขาย」字段词)不算改错 → 放行记账流(P1E-3:不被安全闸误拦成「请回复记录」)。
    if is_correction_like(text) and not _looks_like_new_expense(text):
        _say(reply_token, line_client.t_line(lang, "line_need_reply_record"), ctx)
        return True
    return False


def try_correction_state(
    bound_user,
    reply_token,
    line_user_id,
    text,
    tid,
    ws,
    lang,
    *,
    quoted_message_id=None,
    quote_token="",
) -> bool:
    """改错会话态分发(最高优先):有 correct/correctval/correctclar/correctactive pending 才接管。

    correctactive=改完续接态:后续点名字段继续命中同一张(验收 #2);非改错形(新记账等)放行不劫持。
    引用了具体卡片(换单)→ 让位 maybe_clarify 用引用重新定位。
    """
    with db.get_cursor_rls(tid) as cur:
        pend = conversation.peek_pending(cur, line_user_id=line_user_id)
    missing = str((pend or {}).get("missing") or "")
    if not missing.startswith(_PREFIXES):
        return False
    ctx = dict(quote_token=quote_token, line_user_id=line_user_id, tenant_id=tid)
    reply_lang = line_classify.detect_text_lang(text) or lang
    p_ws, p_doc, p_field = _pend_target(missing)
    is_active = missing.startswith(line_correct._ACTIVE_PREFIX)
    field = line_classify.detect_correction_field(text)

    # 引用优先:active 完全让位;ask 阶段点名字段也让位(换单)→ 交 maybe_clarify 用引用定位。
    if quoted_message_id and (is_active or field):
        return False
    # P1E-3:active 续接态遇明显新记账句(多项/记账动词开头)→ 打断 correction,放行记账流
    # (新卡会重设 active)。即便句中含「ผู้ขาย 711」也不当 seller 新值吞掉。
    if is_active and _looks_like_new_expense(text):
        return False
    # 明确「取消/算了」→ 中止本次改错,不动单据(任何阶段·验收 #1/#7)。
    if line_classify.is_cancel_intent(text):
        line_correct._clear(tid, line_user_id)
        _say(reply_token, line_client.t_line(reply_lang, "exp_correct_cancel"), ctx)
        return True
    # 明确「删除/ลบ」→ 作废目标(草稿删 / 已入账 void·验收 #7)。
    if line_classify.is_delete_intent(text):
        return _delete_target(bound_user, reply_token, reply_lang, tid, p_ws, p_doc, ctx)
    # 点名字段(确认阶段切换 / 收值改口 / 待选答字段 / active 续接)→ 统一路由(给了值直走风险三档)。
    if field:
        return _route_field(bound_user, reply_token, text, lang, tid, p_ws, p_doc, field, ctx)
    # 无字段:按阶段处理。
    if is_active:
        return False  # 续接态收到非改错形(新记账/闲聊)→ 放行,不劫持
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
    if missing.startswith(line_correct._VAL_PREFIX):  # 等某字段新值 → 收值(无字段=纯值)
        return _route_field(bound_user, reply_token, text, lang, tid, p_ws, p_doc, p_field, ctx)
    # correctclar 没听出字段 → 重问列字段(不退回泛化指引·验收 #5/#7)。
    _say(reply_token, ci.t(ci.CLARIFY_FIELDS, reply_lang), ctx)
    return True


def maybe_clarify_feedback(bound_user, reply_token, text, lang, ws, quoted_message_id, ctx) -> bool:
    """引用卡片说「识别错了」或点名字段 → 接管(澄清/直接改),绝不退化成 OCR 失败重拍。

    点名字段 + 给了值 → 直接走风险三档(如「วันที่เป็น 2026/6/18」·验收 #3);点名没给值 → 问新值;
    笼统「识别错了」→ 列字段问改哪里(验收 #4)。没点字段的「改成X」(如「上一笔改成200」)→ 交大脑/
    edit 流定位目标。ctx 带 quote_token/line_user_id/tenant_id(回复带引用)。"""
    field = line_classify.detect_correction_field(text)
    triggered = line_classify.is_correction_feedback(text) or (bool(quoted_message_id) and field)
    if not triggered:
        return False
    if lqe.is_edit_request(text) and not field:
        return False  # 没点字段的「改成X」交 edit 流(大脑定位目标 + 抽字段)
    reply_lang = line_classify.detect_text_lang(text) or lang
    tid = ctx.get("tenant_id")
    luid = ctx.get("line_user_id")
    detail, doc_id, ws_eff = None, None, ws
    with db.get_cursor_rls(tid) as cur:
        tgt = line_message_refs.resolve_target(
            cur,
            tenant_id=tid,
            ws=ws,
            line_user_id=luid,
            quoted_message_id=quoted_message_id,
            text=text,
        )
        if not tgt.get("error"):
            doc_id, ws_eff = tgt["doc_id"], tgt["ws"]
            detail = line_correct.docs_svc.get_doc(
                cur, tenant_id=tid, workspace_client_id=ws_eff, doc_id=doc_id
            )
    # 引用解析失败 / 引用到已作废原单(刚被更正克隆)→ 跟随 active 续接到当前那张(验收:不掉「找不到」)。
    if not line_correct._is_live(detail):
        act = _active_doc(tid, luid)
        if act:
            ws_eff, doc_id = act
            with db.get_cursor_rls(tid) as cur:
                detail = line_correct.docs_svc.get_doc(
                    cur, tenant_id=tid, workspace_client_id=ws_eff, doc_id=doc_id
                )
    if not line_correct._is_live(detail):
        # 无引用且像一句新记账(有金额)→ 放行给记账流,不劫持「买错了 50」这类。
        if not quoted_message_id and lqe.parse_expense(text).has_amount():
            return False
        _say(reply_token, line_client.t_line(reply_lang, "line_need_reply_record"), ctx)
        return True
    return _route_field(
        bound_user, reply_token, text, lang, tid, ws_eff, doc_id, field, ctx, detail=detail
    )


def _active_doc(tid, line_user_id):
    """当前 active 续接态指向的 (ws, doc_id);无 active → None。"""
    with db.get_cursor_rls(tid) as cur:
        pend = conversation.peek_pending(cur, line_user_id=line_user_id)
    m = str((pend or {}).get("missing") or "")
    return _pend_target(m)[:2] if m.startswith(line_correct._ACTIVE_PREFIX) else None


def _route_field(bound_user, reply_token, text, lang, tid, ws, doc_id, field, ctx, *, detail=None):
    """统一字段处理(澄清入口/会话内共用):明细 → 详情页(行级);没点字段 → 列字段问;点了字段没值 →
    存待值态问值;给了值 → 交风险三档执行。付款方式可直接改(低风险展示属性·不动金额/税额)。

    全程锁定 active_doc_id(不重新猜)→ 同一会话内不会回「找不到记录」(验收 #5/#7)。
    """
    reply_lang = line_classify.detect_text_lang(text) or lang
    luid = ctx["line_user_id"]
    if not field:
        line_correct._save_state(tid, ws, doc_id, luid, f"{line_correct._CLAR_PREFIX}{ws}:{doc_id}")
        _say(reply_token, ci.t(ci.CLARIFY_FIELDS, reply_lang), ctx)
        return True
    multiline = bool(detail) and len(detail.get("lines") or []) > 1
    if field == "items" and detail is not None and not multiline:
        line_correct._set_active(tid, ws, doc_id, luid)  # 续接保留(验收 #6)
        _say(reply_token, ci.t(ci.DETAIL_INCOMPLETE, reply_lang), ctx)  # 单行也只能去详情核对
        return True
    if field == "items" or (field == "amount" and multiline):
        # 多行/明细行级 → 详情页(带真按钮·验收 #5);active 续接保留 15min,后续 seller/date 仍命中(#6)。
        line_correct._set_active(tid, ws, doc_id, luid)
        line_correct._say_detail(
            reply_token, doc_id, ws, reply_lang, luid, tid, ctx.get("quote_token", "")
        )
        return True
    value = _extract_value(text, field)
    if value in (None, ""):  # 点了字段没给值 → 存待值态,问新值(tier 1)
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
        detail=detail,
    )


def try_void_quoted(
    bound_user, reply_token, text, lang, tid, ws, line_user_id, quoted_message_id, quote_token=""
) -> bool:
    """引用某条 + 明确「取消/删除/ลบ」→ 短路径作废(草稿丢弃 / 已入账 void·复用 reply_undo·验收 #7)。
    无引用或非取消/删除意图 → False(交后续路由)。"""
    if not quoted_message_id or not (
        line_classify.is_cancel_intent(text) or line_classify.is_delete_intent(text)
    ):
        return False
    from services.line_binding import line_expense_qa

    line_expense_qa.reply_undo(
        bound_user,
        reply_token,
        lang,
        tid,
        ws,
        line_user_id,
        quoted_message_id,
        text,
        quote_token=quote_token,
    )
    return True


def _delete_target(bound_user, reply_token, lang, tid, ws, doc_id, ctx) -> bool:
    """改错会话内「删除/ลบ」→ 作废目标:草稿物理删 / 已入账 void(复用对账冲销)→ 回终态卡(验收 #4);
    已结期诚实引导。"""
    from core.pos_api import PosError
    from services.line_binding import line_card_actions
    from services.purchase import posting as posting_svc

    line_correct._clear(tid, ctx["line_user_id"])
    luid = ctx["line_user_id"]
    uid = str(bound_user["id"]) if bound_user.get("id") else None
    try:
        with db.get_cursor_rls(tid, commit=True) as cur:
            detail = line_correct.docs_svc.get_doc(
                cur, tenant_id=tid, workspace_client_id=ws, doc_id=doc_id
            )
            status = (detail.get("doc") or {}).get("status") if detail else None
            if status == "draft":
                amt = (detail.get("doc") or {}).get("grand_total")
                line_correct.docs_svc.delete_doc(
                    cur, tenant_id=tid, workspace_client_id=ws, doc_id=doc_id
                )
                line_card_actions.send_terminal(
                    reply_token,
                    state="discarded",
                    doc_id=doc_id,
                    ws=ws,
                    amount=amt,
                    lang=lang,
                    tid=tid,
                    luid=luid,
                )
                return True
            if status == "posted":
                res = posting_svc.void_doc(
                    cur, tenant_id=tid, workspace_client_id=ws, doc_id=doc_id, created_by=uid
                )
                amt = (res.get("doc") or {}).get("grand_total")
                line_card_actions.send_terminal(
                    reply_token,
                    state="voided",
                    doc_id=doc_id,
                    ws=ws,
                    amount=amt,
                    lang=lang,
                    tid=tid,
                    luid=luid,
                )
                return True
    except PosError as e:
        if (e.code or "") == "acct.period_closed":
            _say(reply_token, line_client.t_line(lang, "exp_correct_closed"), ctx)
            return True
        raise
    _say(reply_token, line_client.t_line(lang, "exp_correct_none"), ctx)
    return True


def _extract_value(text: str, field: str):
    """用户答 → 字段值:金额取数字;日期(相对/年首/ISO/DD-MM);付款方式归一码;卖家/分类剥前缀+否定填充。

    付款方式用归一表子串匹配(「改成现金」含「现金」→ cash),认不出 → None 再问。无 → None。
    """
    if field == "amount":
        amt = lqe.parse_expense(text).amount
        return amt if (amt and amt > Decimal("0")) else None
    if field == "date":
        return lqe._parse_date(text)  # 相对词/年首/ISO/DD-MM 全在共用解析器
    if field == "payment":
        return line_classify.normalize_payment_method(text) or None
    cleaned = _strip_prefix(text)
    return cleaned or None


def _strip_prefix(text: str) -> str:
    """剥命令+字段+连接前缀 + 否定/指代填充,留真实值。

    「แก้ร้านค้าเป็น 7-11」→「7-11」;「ผู้ขายไม่ใช่คนนี้/卖家不是这个」→「」(没给真值·调用方据此再问)。
    拉丁词须按词边界剥(后接字母不剥)→「to」不吃掉店名「tops」的前两字母(验收 #5)。
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
            t = tok.lower()
            if not low.startswith(t):
                continue
            rest = s[len(tok) :]
            if t.isascii() and t.isalpha() and rest[:1].isalpha():
                continue  # 拉丁词后紧跟字母 → 是值的一部分(「tops」≠「to」+「ps」)
            s, changed = rest.strip(), True
            break
    return s.strip(" :=")


def _pend_target(missing: str):
    """任意阶段 pending 的 (ws, doc_id, field)(三态前缀后都是 <ws>:<doc>[:<field/keys>])。
    field 仅 correctval 有意义,其余为附带值,调用方按需取。"""
    for pfx in _PREFIXES:
        if missing.startswith(pfx):
            body = missing[len(pfx) :]
            ws_s, _, rest = body.partition(":")
            doc_id, _, field = rest.partition(":")
            return _int(ws_s), doc_id, field
    return None, None, ""


def _int(s):
    try:
        return int(s)
    except (ValueError, TypeError):
        return s
