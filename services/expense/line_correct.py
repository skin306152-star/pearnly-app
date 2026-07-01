# -*- coding: utf-8 -*-
"""LINE 对话内改错(改错闭环 · P1E-2 · 绝不静默覆盖)。

定位 引用卡片 > 第 N 笔(绝不默认改最近一笔)。执行三档(_apply_or_confirm):草稿单非金额字段直接改;
已入账/改金额/多字段确认;多行金额引导详情页。_apply:草稿原地 update_draft、已入账 correct_doc(void
+克隆,多行/票图/已结期红冲保留)。会话态复用 conversation.pending,不新建表。金额/税额/过账永不信 LLM。
多轮态机在 line_correct_flow。
"""

from __future__ import annotations

import logging
import re
from decimal import Decimal, InvalidOperation
from typing import Optional

from core import db
from services.expense import conversation, line_classify
from services.expense import line_correct_data as lcd
from services.expense import line_correct_i18n as ci
from services.expense.expense_draft import ExpenseDraft
from services.line_binding import line_client, line_message_refs, line_reply
from services.purchase import docs as docs_svc

logger = logging.getLogger(__name__)


def _after_category_change(tid, ws, line_user_id, lang, res) -> None:
    """分类落地后:对到准确科目 → 追发学习按钮(沉淀习惯);落「其他」兜底 → 诚实提示(先记其他·可改,
    不学这条兜底)。两者均 best-effort,绝不拖垮改错主流程。"""
    if res.get("cat_notice"):
        try:
            line_client.push_messages(
                line_user_id, [{"type": "text", "text": ci.t(ci.CAT_FALLBACK_OTHER, lang)}]
            )
        except Exception:  # noqa: BLE001
            logger.warning("[line correct] cat-fallback notice push failed", exc_info=True)
        return
    from services.expense import line_learn

    line_learn.offer(tid, ws, line_user_id, lang, doc_id=res["new_id"])


_PREFIX = "correct:"  # 待 是/否 确认(最终)
_CLAR_PREFIX = "correctclar:"  # 待用户选「改哪个字段」(多轮·correctclar:<ws>:<doc>)
_VAL_PREFIX = "correctval:"  # 待用户给「新值」(多轮·correctval:<ws>:<doc>:<field>)
_ACTIVE_PREFIX = "correctactive:"  # 改完续接态(active_doc_id·后续字段编辑继续命中同一张·验收 #2)
_YES = ("是", "对", "好", "确认", "ok", "yes", "ใช่", "ยืนยัน", "ตกลง", "ถูก", "確認", "はい")
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


def _collect_changes(u: dict, text: str = "") -> dict:
    """大脑槽位 → 要改字段(canonical)。科目只在无金额/卖家/日期时从 note 取;付款方式不在槽位,
    仅当原文点名付款方式才归一(挡正常记账文本里的裸 cash/qr 误判)。"""
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
    if text and line_classify.detect_correction_field(text) == "payment":
        pm = line_classify.normalize_payment_method(text)
        if pm:
            changes["payment_method"] = pm
    note = (u.get("note") or "").strip()
    if note and not changes:
        changes["category"] = note
    return changes


def _summary(changes: dict, lang: str) -> str:
    """改动摘要(确认卡用 · emoji 前缀免逐字段翻译标签)。付款方式码本地化成人话。"""
    parts = []
    if "amount" in changes:
        parts.append(f"฿{changes['amount']}")
    if "vendor_name" in changes:
        parts.append(f"🏪 {changes['vendor_name']}")
    if "doc_date" in changes:
        parts.append(f"📅 {changes['doc_date']}")
    if "category" in changes:
        parts.append(f"🏷️ {changes['category']}")
    if "payment_method" in changes:
        parts.append(f"💳 {ci.pay_label(changes['payment_method'], lang)}")
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


def _say_detail(reply_token, doc_id, ws, lang, line_user_id, tid, quote_token="") -> None:
    """多行/明细需详情页 → 文案 + 「打开详情」真按钮(复用 line_card_actions·验收 #5)。"""
    from services.line_binding import line_card_actions

    line_card_actions.send_detail_link(
        reply_token,
        ci.t(ci.MULTILINE_EDIT, lang),
        doc_id=doc_id,
        ws=ws,
        lang=lang,
        tid=tid,
        luid=line_user_id,
        quote_token=quote_token,
    )


def _set_active(tid, ws, doc_id, line_user_id, *, cur=None) -> None:
    """改完续接 active_doc_id(TTL 默认 15min):后续字段编辑无需再引用即命中同一张(验收 #2)。
    cur 传入则复用调用方的提交游标(免再开一次连接)。"""

    def _save(c):
        conversation.save_pending(
            c,
            line_user_id=line_user_id,
            tenant_id=tid,
            workspace_client_id=ws,
            draft=ExpenseDraft(),
            missing=f"{_ACTIVE_PREFIX}{ws}:{doc_id}",
        )

    if cur is not None:
        _save(cur)
        return
    with db.get_cursor_rls(tid, commit=True) as c:
        _save(c)


def _is_live(detail) -> bool:
    """单据存在且可改(草稿/已入账)。void/不存在 → False。"""
    return bool(detail) and (detail.get("doc") or {}).get("status") in ("posted", "draft")


def _current(detail: dict, key: str):
    """字段当前值(规范键 → detail 里的原始值)。_is_noop / _field_old 共用唯一映射(防漂移)。"""
    doc = detail.get("doc") or {}
    sup = detail.get("supplier") or {}
    return {
        "amount": doc.get("grand_total"),
        "vendor_name": sup.get("name"),
        "doc_date": doc.get("doc_date"),
        "category": doc.get("category_name") or doc.get("category"),
        "payment_method": doc.get("payment_method"),
    }.get(key)


def _is_noop(detail: dict, key: str, new) -> bool:
    """目标值已等于当前值?(验收 #3:no-op 不 void/不重建/不写审计)。category 名↔id 不比,放行。"""
    cur = _current(detail, key)
    if key == "amount":
        try:
            return Decimal(str(new)) == Decimal(str(cur or 0))
        except (InvalidOperation, ValueError):
            return False
    if key in ("doc_date", "vendor_name", "payment_method"):
        return str(new or "") == str(cur or "")
    return False


def _field_old(detail: dict, key: str, lang: str) -> str:
    """单字段旧值(确认文案「从 旧 改成 新」用)。付款方式码本地化成人话。取不到 → —。"""
    val = _current(detail, key)
    return ci.disp(key, val, lang) if val not in (None, "") else "—"


def _apply_or_confirm(
    reply_token,
    bound_user,
    lang,
    tid,
    ws,
    doc_id,
    changes,
    *,
    quote_token="",
    line_user_id,
    detail=None,
    notice="",
) -> bool:
    """改错执行三档(产品原则):低风险(草稿 + 单个非金额字段)直接改回完成;高风险(已入账/改金额[税额
    重算]/多字段)出确认;多行金额 → 详情页。作废/不存在 → 诚实兜底。changes = 规范键 dict。
    detail 可由调用方(已定位)传入免重 fetch。notice 非空 → 作前缀并进同一条回复(SUPERSEDED 提示·
    reply_token 单次性故不能另发)。"""

    def _say(body):
        line_reply.reply_text_context(
            reply_token,
            f"{notice}\n{body}" if notice else body,
            quote_token=quote_token,
            line_user_id=line_user_id,
            tenant_id=tid,
        )

    if detail is None:
        with db.get_cursor_rls(tid) as cur:
            detail = docs_svc.get_doc(cur, tenant_id=tid, workspace_client_id=ws, doc_id=doc_id)
    if not _is_live(detail):
        _clear(tid, line_user_id)
        _say(line_client.t_line(lang, "exp_correct_none"))
        return True
    # no-op:目标值已等于当前值 → 不 void/不重建/不写审计,诚实告知,续 active(验收 #3)。
    noop = {k: v for k, v in changes.items() if _is_noop(detail, k, v)}
    changes = {k: v for k, v in changes.items() if k not in noop}
    if not changes:
        _set_active(tid, ws, doc_id, line_user_id)
        k, v = next(iter(noop.items()))
        _say(ci.t(ci.CHANGED_NOOP, lang, field=ci.key_label(k, lang), value=ci.disp(k, v, lang)))
        return True
    if "amount" in changes and len(detail.get("lines") or []) > 1:
        _set_active(tid, ws, doc_id, line_user_id)  # 续接保留(验收 #6)·后续 seller/date 仍命中
        _say_detail(reply_token, doc_id, ws, lang, line_user_id, tid, quote_token)
        return True
    changes_draft = ExpenseDraft(
        amount=changes.get("amount"),
        vendor_name=changes.get("vendor_name") or "",
        doc_date=changes.get("doc_date") or "",
        note=changes.get("category") or "",
        payment_method=changes.get("payment_method") or "",
    )
    keys = sorted(changes)
    # 高风险=改金额(税额重算)/多字段 → 确认;低风险(单个 date/seller/category/payment)直接改,
    # 即便已入账也直执行(void+克隆+重过账·可撤销·验收 #1)。
    high_risk = "amount" in changes or len(changes) > 1
    if not high_risk:  # 低风险:直接执行,不二次确认
        sent = False
        with db.get_cursor_rls(tid, commit=True) as cur:
            res = _apply(cur, bound_user, tid, ws, doc_id, changes_draft, keys, detail=detail)
            if res:  # 续接同一张(验收 #2)·复用同一提交免再开游标
                _set_active(tid, ws, res["new_id"], line_user_id, cur=cur)
                # Req5:改完重发当前状态卡(posted/草稿),让改动在卡上可见,而非「已更新 X→Y」纯文字。
                from services.line_binding import line_card_actions

                sent = line_card_actions.send_state_card_reply(
                    cur,
                    reply_token,
                    doc_id=res["new_id"],
                    ws=ws,
                    lang=lang,
                    tid=tid,
                    luid=line_user_id,
                )
        if not res:
            _say(line_client.t_line(lang, "exp_correct_none"))
            return True
        if not sent:  # 卡发送失败兜底:仍给文字确认(诚实·不静默)
            k = keys[0]
            fl, nv = ci.key_label(k, lang), ci.disp(k, changes[k], lang)
            _say(ci.t(ci.CHANGED_DONE, lang, field=fl, new=nv))
        if "category" in changes:  # 分类落地后:准确科目→学习按钮;落「其他」→诚实提示(不学兜底)
            _after_category_change(tid, ws, line_user_id, lang, res)
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
                old=_field_old(detail, k, lang),
                new=ci.disp(k, changes[k], lang),
            )
        )
    else:
        _say(ci.t(ci.CONFIRM_MULTI, lang, changes=_summary(changes, lang)))
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

    def _say(body):
        line_reply.reply_text_context(
            reply_token, body, quote_token=quote_token, line_user_id=line_user_id, tenant_id=tid
        )

    changes = _collect_changes(u, text)
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
    bound_user, reply_token, line_user_id, text, tid, ws, lang, *, quote_token="", pend=None
) -> bool:
    """有待确认更正(correct:)+ 肯定 → 执行;否定 → 取消;非更正 pending → False。pend 可由调用方传入免重读。"""
    from core.pos_api import PosError

    def _say(body):
        line_reply.reply_text_context(
            reply_token, body, quote_token=quote_token, line_user_id=line_user_id, tenant_id=tid
        )

    if pend is None:
        with db.get_cursor_rls(tid) as cur:
            pend = conversation.peek_pending(cur, line_user_id=line_user_id)
    if not pend or not str(pend.get("missing") or "").startswith(_PREFIX):
        return False
    if not _affirmative(text):
        # 明确「否」(不/ไม่/no/取消)→ 取消;既非是也非否(误触/无关)→ 重问,不静默取消、不串旧动作。
        low = (text or "").lower()
        if not (any(n in low for n in _NO) or line_classify.is_cancel_intent(text)):
            _say(ci.t(ci.CONFIRM_REPROMPT, lang))
            return True
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
            if res:  # 续接同一张(验收 #2)·复用同一提交免再开游标
                _set_active(tid, ws_eff, res["new_id"], line_user_id, cur=cur)
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
        _say(ci.t(ci.DRAFT_EDITED, lang, new=res["total"]))  # 草稿原地改·不提「冲销原单」
    else:
        _say(line_client.t_line(lang, "exp_correct_draft", new=res["total"]))
    if "category" in keys:  # 确认型改动含分类:准确科目→学习按钮;落「其他」→诚实提示(不学兜底)
        _after_category_change(tid, ws_eff, line_user_id, lang, res)
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


def _apply(cur, bound_user, tid, ws, orig_id, changes_draft, keys, detail=None) -> Optional[dict]:
    """应用改动:已入账 → void+克隆+改+auto_book 过账;草稿 → 原地改。detail 可传入免重 fetch。作废/无 → None。"""
    from services.purchase import correct as correct_svc
    from services.purchase import posting as posting_svc
    from services.purchase import settings as settings_svc

    detail = detail or docs_svc.get_doc(cur, tenant_id=tid, workspace_client_id=ws, doc_id=orig_id)
    status = (detail.get("doc") or {}).get("status") if detail else None
    if status not in ("posted", "draft"):
        return None
    uid = str(bound_user["id"]) if bound_user.get("id") else None
    if status == "posted":
        clone = correct_svc.correct_doc(
            cur, tenant_id=tid, workspace_client_id=ws, doc_id=orig_id, created_by=uid
        )
        edit_id = str(clone["doc"]["id"])
        data = lcd.detail_to_data(clone)
        mode = "posted_reclone"
    else:  # 草稿:原地改(无需冲销·update_draft 直接重算重写行)
        edit_id = str(orig_id)
        data = lcd.detail_to_data(detail)
        mode = "draft_inplace"
    cat_notice = lcd.apply_changes(cur, data, changes_draft, keys, tid, ws, bound_user)
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
    out = {"new_id": edit_id, "total": total, "mode": mode, "cat_notice": cat_notice}
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
        return {**out, "posted": True}
    return {**out, "posted": False}
