# -*- coding: utf-8 -*-
"""无引用智能解析(LINE 06 · Slice 4 · Confidence-Based Intent Routing)。

没引用一张卡时,删/撤/改要落到哪一笔?
  · 目标明确(唯一近单 / 焦点 / 上一笔 / 第N笔)→ 既有路径执行(本模块不碰)。
  · 目标不明(≥2 近单 + 指示代词「那个 / อันนั้น / that one」)→ 列候选追问,绝不猜着删。
  · 追问后答「第二张 / 7-11」→ 继承上次动作执行;答不上号 / 新句子 → 丢 pending 当新输入。

铁律:破坏性动作(删/撤)目标不明永远列候选,绝不执行。优先级 引用 > 批量 > 候选/焦点 > 记账
—— detect_ambiguous_target 显式排除批量 / 上一笔 / 第N笔,故本模块放在批量之前调用也不抢它们。
pending 复用 conversation.line_pending_entry(missing 前缀 pick:),不新建表。
"""

from __future__ import annotations

import re
from decimal import Decimal

from core import db
from services.expense import conversation, line_classify
from services.expense import line_correct_i18n as ci
from services.expense import line_quick_entry as lqe
from services.expense.expense_draft import ExpenseDraft
from services.line_binding import line_message_refs

_PICK_PREFIX = "pick:"
_LIST_CAP = 5
_MIN_SELLER = 2  # 卖家名答案至少 2 字符才匹配(防单字符误命中候选)

# 指示代词(指向某张卡却不明确是哪张)→ 触发列候选;裸命令(取消/删除·无指代)走焦点,不进本模块。
_DEMONSTRATIVE = (
    "那个",
    "那笔",
    "那张",
    "那条",
    "那一笔",
    "那一张",
    "哪个",
    "哪笔",
    "哪张",
    "哪条",
    "哪一",
    "อันนั้น",
    "อันไหน",
    "รายการนั้น",
    "รายการไหน",
    "ตัวนั้น",
    "ตัวไหน",
    "that one",
    "which one",
    "that",
    "which",
)
# 删/撤动词(比 line_classify 宽:含裸「删/撤」·有指代词守门故不会误伤正常句)。
_DELETE_VERBS = (
    "删",
    "删除",
    "删掉",
    "删了",
    "撤",
    "撤销",
    "撤掉",
    "取消",
    "ลบ",
    "ยกเลิก",
    "ถอน",
    "delete",
    "remove",
    "cancel",
)
# 答候选时的序号:parse_ordinal 只认「第N」,这里补泰语「อันที่N」与裸数字/字母。
_TH_ORDINAL_RE = re.compile(r"(?:อันที่|ลำดับที่|ตัวที่|รายการที่)\s*([0-9๐-๙]+)")
_TH_DIGITS = str.maketrans("๐๑๒๓๔๕๖๗๘๙", "0123456789")
_NOISE_RE = re.compile(
    "|".join(re.escape(w) for w in _DELETE_VERBS + _DEMONSTRATIVE), re.IGNORECASE
)


def route(bound_user, reply_token, line_user_id, text, lang, tid, ws, ctx) -> bool:
    """无引用智能解析入口(改错路由内·批量之前调):
    ① 有 pick pending 且本句是答案 → 继承执行;非答案 → 丢 pending,落回正常流。
    ② 目标不明(删/撤/改 + 指示代词)→ 列候选(≥2)/ 唯一近单直接执行 / 无近单诚实告知。
    接管返回 True;否则 False(交批量/焦点/记账)。"""
    with db.get_cursor_rls(tid) as cur:
        pend = conversation.peek_pending(cur, line_user_id=line_user_id)
    missing = str((pend or {}).get("missing") or "")
    if missing.startswith(_PICK_PREFIX):
        action, field, value, ids = _parse_pick(missing)
        did = _match_pick(text, tid, ws, ids)
        # 清 pick pending 必须在执行【之前】(edit 确认会新设 correct: 态,不能被这里反清掉);
        # 没对上号也清(丢 pending 当新输入)。引用某卡作答 → flow 有引用走强锚定(Slice3),不到这。
        with db.get_cursor_rls(tid, commit=True) as cur:
            conversation.clear_pending(cur, line_user_id=line_user_id)
        if did:
            reply_lang = line_classify.detect_text_lang(text) or lang
            return _exec(
                bound_user,
                reply_token,
                line_user_id,
                reply_lang,
                tid,
                ws,
                ctx,
                action,
                field,
                value,
                did,
            )
    return _maybe_list_candidates(bound_user, reply_token, line_user_id, text, lang, tid, ws, ctx)


def detect_ambiguous_target(text: str):
    """删/撤/改 + 指示代词 + 非批量/非上一笔/非第N → (action, field, value);否则 None。

    edit 只在能确定性抽出 (字段, 值) 时触发:金额(数字位置无关)/ 日期。卖家/分类的尾随值
    确定性抽取不可靠 → 不在此触发(落回「回复记录」安全兜底),避免猜错对象。
    """
    from services.expense import line_bulk_undo

    if line_bulk_undo.detect_bulk_undo(text):  # 批量优先
        return None
    if line_message_refs.mentions_last(text) or lqe.parse_ordinal(text):  # 上一笔/第N 已有路径
        return None
    if not _contains_any(text, _DEMONSTRATIVE):  # 无指代 → 裸命令走焦点,不列候选
        return None
    if _contains_any(text, _DELETE_VERBS):
        return ("delete", "", "")
    if lqe.is_edit_request(text):
        amt = lqe.parse_expense(text).amount
        if amt and amt > Decimal("0"):
            return ("edit", "amount", str(amt))
        if line_classify.detect_correction_field(text) == "date":
            d = lqe._parse_date(text)
            if d:
                return ("edit", "date", d)
    return None


def _maybe_list_candidates(bound_user, reply_token, line_user_id, text, lang, tid, ws, ctx) -> bool:
    parsed = detect_ambiguous_target(text)
    if not parsed:
        return False
    action, field, value = parsed
    reply_lang = line_classify.detect_text_lang(text) or lang
    from services.purchase import line_docs

    with db.get_cursor_rls(tid) as cur:
        docs = line_docs.find_recent_line_docs(
            cur, tenant_id=tid, workspace_client_id=ws, limit=_LIST_CAP
        )
    if not docs:
        _say(reply_token, ci.t(ci.PICK_NONE, reply_lang), ctx)
        return True
    if len(docs) == 1:  # 唯一近单 → 直接执行,不啰嗦列候选
        return _exec(
            bound_user,
            reply_token,
            line_user_id,
            reply_lang,
            tid,
            ws,
            ctx,
            action,
            field,
            value,
            str(docs[0]["id"]),
        )
    ids = [str(d["id"]) for d in docs]
    with db.get_cursor_rls(tid, commit=True) as cur:
        conversation.save_pending(
            cur,
            line_user_id=line_user_id,
            tenant_id=tid,
            workspace_client_id=ws,
            draft=ExpenseDraft(),
            missing=f"{_PICK_PREFIX}{action}:{field}:{value}:{','.join(ids)}",
        )
    _say(reply_token, _candidate_text(docs, reply_lang), ctx)
    return True


def _match_pick(text: str, tid, ws, ids):
    """本句是否是对候选的答案 → 命中的 doc_id;不是答案 → None(调用方据此丢 pending)。

    序号(第二张/อันที่2/2/B)优先;否则严格「答案 ⊂ 卖家名」匹配(「咖啡70」不会误吞卖家「咖啡」)。
    引用某卡作答 → flow 有引用走强锚定(Slice 3),根本不进本模块,故此处只管无引用答案。
    """
    if not ids:
        return None
    n = _pick_ordinal(text)
    if n and 1 <= n <= len(ids):
        return ids[n - 1]
    return _match_seller(tid, ws, ids, text)


def _exec(
    bound_user, reply_token, line_user_id, lang, tid, ws, ctx, action, field, value, doc_id
) -> bool:
    """候选选定 = 等价「引用了那张」→ 复用既有执行核:删→_undo_resolved(草稿软删/已入账冲销·可恢复),
    改→_apply_or_confirm(风险三档)。"""
    qt = ctx.get("quote_token", "")
    if action == "delete":
        from services.line_binding import line_expense_qa

        line_expense_qa._undo_resolved(
            bound_user, reply_token, lang, tid, ws, doc_id, line_user_id, qt
        )
        return True
    from services.expense import line_correct

    key = ci.FIELD_TO_KEY.get(field)
    if not key:
        return False
    val = Decimal(value) if field == "amount" else value
    return line_correct._apply_or_confirm(
        reply_token,
        bound_user,
        lang,
        tid,
        ws,
        doc_id,
        {key: val},
        quote_token=qt,
        line_user_id=line_user_id,
    )


def _candidate_text(docs, lang: str) -> str:
    """候选列表文案:抬头 + 逐张「序号. 日期 · 卖家 · ฿额」(格式无关语言·抬头走 i18n)。"""
    lines = [ci.t(ci.PICK_WHICH, lang)]
    for i, d in enumerate(docs, 1):
        date = str(d.get("doc_date") or "").strip()
        vendor = str(d.get("supplier_name") or "").strip()
        head = " · ".join(p for p in (date, vendor) if p)
        amt = ci.money(d.get("grand_total"))
        lines.append(f"{i}. {head} · ฿{amt}" if head else f"{i}. ฿{amt}")
    return "\n".join(lines)


def _pick_ordinal(text: str):
    """答候选的序号:第N / รายการที่N / #N(parse_ordinal)→ อันที่N → 裸数字 → 字母 A–E。无 → None。"""
    n = lqe.parse_ordinal(text)
    if n:
        return n
    m = _TH_ORDINAL_RE.search(text or "")
    if m:
        return int(m.group(1).translate(_TH_DIGITS))
    s = (text or "").strip().translate(_TH_DIGITS)
    if s.isdigit():
        return int(s)
    if len(s) == 1 and s.upper() in "ABCDE":
        return ord(s.upper()) - ord("A") + 1
    return None


def _match_seller(tid, ws, ids, text: str):
    """答案是卖家名 → 命中的候选 doc_id(保候选顺序·最近优先)。严格「答案 ⊂ 卖家名」:
    「7-11」匹配卖家「…7-11…」,但「咖啡70」不会误命中卖家「咖啡」。无 → None。"""
    ans = _NOISE_RE.sub("", text or "").strip(" :=-,").lower()
    if len(ans) < _MIN_SELLER:
        return None
    from services.purchase import line_docs

    with db.get_cursor_rls(tid) as cur:
        rows = line_docs.find_line_docs_by_ids(cur, tenant_id=tid, workspace_client_id=ws, ids=ids)
    by_id = {str(r["id"]): str(r.get("supplier_name") or "").lower() for r in rows}
    for did in ids:
        seller = by_id.get(did, "")
        if seller and ans in seller:
            return did
    return None


def _parse_pick(missing: str):
    """pick:<action>:<field>:<value>:<id1,id2,…> → (action, field, value, [ids])。
    value 可含冒号(末段始终是逗号分隔的 ids·按最后一个冒号切)。"""
    body = missing[len(_PICK_PREFIX) :]
    action, _, rest = body.partition(":")
    field, _, rest2 = rest.partition(":")
    value, _, ids_str = rest2.rpartition(":")
    return action, field, value, [x for x in ids_str.split(",") if x]


def _contains_any(text: str, tokens) -> bool:
    low = (text or "").lower()
    return any(t.lower() in low for t in tokens)


def _say(reply_token, body, ctx) -> None:
    from services.line_binding import line_reply

    line_reply.reply_text_context(reply_token, body, **ctx)
