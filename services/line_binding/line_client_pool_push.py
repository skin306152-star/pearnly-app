# -*- coding: utf-8 -*-
"""LINE 待问客户池 · 攒批推送(D2 方案 §3 / §7.2 S4)。

STAGED 问题不自动推;会计对某客户点「推这批」才把该客户全部 STAGED 合成一条
LINE 消息一次性发出(照 Keeper「打扰控制」,方案 §3.1 拍板)。一条消息最多列
5 条(LINE 可读性 + 答题不压垮客户),多余留 STAGED 等下一批。

发送顺序拍板「先发后置态」:push_text_context 先送达,确认成功才把这批
staged→pending(mark_sent 落 batch_id/sent_at)。理由——若反过来先置 pending
再发,进程在两步之间中断会把「客户压根没收到」的行标成 pending:催办 tick 会
去催一个从未问过的问题、客户池 UI 也会撒谎「已发·等回复」,这是更贵的假成功。
先发后置态时若中断,残留 staged 顶多让会计重按一次「推这批」,客户收到重复
一条消息——烦但不撒谎,可恢复。mark_sent 逐行落定途中若部分行成功、部分行因
数据库抖动失败,已落定的行原路 transition 回 staged,保批状态原子(要么整批
pending 要么整批 staged),不留半吊子。
"""

from __future__ import annotations

import logging
import uuid

from services.line_binding import client_pool_vocab as vocab
from services.line_binding import line_client_contact
from services.line_binding import line_client_pool_store as store

logger = logging.getLogger(__name__)

MAX_QUESTIONS_PER_BATCH = 5

_COPY_GREETING = {
    "th": "สวัสดีค่ะ 👋 มีรายการที่ขอรบกวนช่วยยืนยัน {n} รายการนะคะ",
    "zh": "你好,有 {n} 条想请你确认一下。",
    "en": "Hi! I have {n} item(s) I'd like you to confirm.",
    "ja": "こんにちは。確認していただきたい項目が{n}件あります。",
}

_COPY_Q_DIRECTION = {
    "th": "{i}) บิล {supplier} เลขที่ {invno} — ใบนี้เป็นรายจ่าย(ซื้อ)หรือรายรับ(ขาย)ของร้านคะ?",
    "zh": "{i}) 单据 {supplier} 编号 {invno} —— 这张是买入(รายจ่าย)还是卖出(รายรับ)?",
    "en": "{i}) {supplier} invoice {invno} — is this a purchase or a sale?",
    "ja": "{i}) {supplier} 請求書番号{invno} — これは仕入(購入)ですか、売上(販売)ですか?",
}

_COPY_Q_AMOUNT = {
    "th": "{i}) ยอด {amount} บาท ถูกต้องไหมคะ ถ้าไม่ถูกบอกยอดที่ถูกได้เลยค่ะ",
    "zh": "{i}) 金额 {amount} 泰铢对吗?不对的话请告诉我正确金额。",
    "en": "{i}) Is the amount {amount} correct? If not, please tell me the right amount.",
    "ja": "{i}) 金額{amount}バーツで合っていますか?違う場合は正しい金額を教えてください。",
}

_COPY_Q_DROP = {
    "th": (
        "{i}) บิล {supplier} ใบนี้เดือนนี้ยังใช้อยู่ไหมคะ "
        "ถ้าไม่ใช่เดือนนี้ / ซ้ำ / ไม่ต้องใช้ บอกได้เลยค่ะ"
    ),
    "zh": "{i}) 单据 {supplier} 这个月还算数吗?如果不是这个月/重复/不用了,请告诉我。",
    "en": (
        "{i}) Does the {supplier} bill still belong to this month? "
        "Let me know if it's not this month / a duplicate / not needed."
    ),
    "ja": "{i}) {supplier}の請求書は今月分で合っていますか?違う場合はお知らせください。",
}

_COPY_Q_FREEFORM = {
    "th": "{i}) {note}",
    "zh": "{i}) {note}",
    "en": "{i}) {note}",
    "ja": "{i}) {note}",
}

_COPY_ANSWER_HINT = {
    "th": 'ตอบกลับตามหมายเลขได้เลยนะคะ เช่น "1 ซื้อ" 🙏',
    "zh": '请照编号回复,例如 "1 买入" 🙏',
    "en": 'Reply with the number, e.g. "1 purchase" 🙏',
    "ja": "番号で返信してください。例:「1 購入」🙏",
}

_COPY_REMAINING = {
    "th": "ตอบชุดนี้เสร็จแล้ว เดี๋ยวส่งอีก {n} รายการที่เหลือให้นะคะ",
    "zh": "这批答完之后,我再发剩下的 {n} 条给你。",
    "en": "Once you're done with this batch, I'll send the remaining {n}.",
    "ja": "この分にご回答いただいたら、残り{n}件をお送りします。",
}

# 问题类型 → 文案表分派(vocab 是唯一事实源,零臆造新类型 · 方案 §4.1/C4 血泪)。
_QUESTION_COPY = {
    vocab.QUESTION_DIRECTION: _COPY_Q_DIRECTION,
    vocab.QUESTION_AMOUNT: _COPY_Q_AMOUNT,
    vocab.QUESTION_DROP: _COPY_Q_DROP,
    vocab.QUESTION_FREEFORM: _COPY_Q_FREEFORM,
}


def _lang_copy(table: dict, lang: str) -> str:
    """th 兜底(客户侧默认泰语,取不到目标语言不炸,方案 §3.3)。"""
    return table.get(lang) or table["th"]


def _render_question_line(index: int, question: dict, lang: str) -> str:
    """单条问题渲染成人话一行。question_payload 里的票号/供应商/金额原样嵌入,
    不翻译(方案 §3.2)。未知 question_type 保守回落 freeform 模板,不炸。"""
    payload = question.get("question_payload") or {}
    template = _lang_copy(_QUESTION_COPY.get(question["question_type"], _COPY_Q_FREEFORM), lang)
    return template.format(
        i=index,
        supplier=payload.get("supplier", ""),
        invno=payload.get("invno", ""),
        amount=payload.get("amount", ""),
        note=payload.get("note", ""),
    )


def _render_batch_message(questions: list, remaining: int, lang: str) -> str:
    """问候 + 逐条编号问题 + 答法提示(+ 有剩余时附「还有 X 条」),方案 §3.2 模板。"""
    lines = [_lang_copy(_COPY_GREETING, lang).format(n=len(questions)), ""]
    for idx, q in enumerate(questions, start=1):
        lines.append(_render_question_line(idx, q, lang))
    lines.append("")
    lines.append(_lang_copy(_COPY_ANSWER_HINT, lang))
    if remaining > 0:
        lines.append(_lang_copy(_COPY_REMAINING, lang).format(n=remaining))
    return "\n".join(lines)


def _resolve_lang(contact: dict, tenant_id) -> str:
    """语言取 contact.preferred_lang;可选用 card_lang 贴近该 LINE 号最近实际对话
    语言(与 proactive._copy_for 同一增强)。增强路径 fail-open——查不到/异常一律
    回落 preferred_lang,文案层故障绝不许挡推送(方案 §3.3)。"""
    preferred = contact.get("preferred_lang") or "th"
    try:
        from services.expense import line_lang

        return line_lang.card_lang(contact["line_user_id"], tenant_id, preferred)
    except Exception:
        return preferred


def _push(line_user_id: str, text: str, tenant_id) -> bool:
    """薄封装 line_reply.push_text_context——异常按失败处理,不让底层异常穿透
    成未捕获 500(推送失败是四态之一,不是 bug,方案 §6.2)。"""
    from services.line_binding import line_reply

    try:
        return line_reply.push_text_context(line_user_id, text, tenant_id=tenant_id) is not False
    except Exception:
        logger.warning("[line_client_pool_push] push_text_context raised", exc_info=True)
        return False


def push_batch_for_client(tenant_id, workspace_client_id, actor: str) -> dict:
    """会计点「推这批给 XX 客户」(方案 §3.1)。

    取该客户全部 STAGED(oldest first)、最多前 5 条合成一条 LINE 消息推送;
    闸关 / 无 STAGED / 未连 LINE / 推送失败,四态结构化返回,零假成功。
    成功时返回的 batch_id/question_ids 供调用方(S8 UI/审计)回显。
    """
    from core import feature_flags

    if not feature_flags.pearnly_ai_client_pool_enabled_for(str(tenant_id)):
        return {"ok": False, "reason": "disabled"}

    staged = store.list_for_client(tenant_id, workspace_client_id, statuses=(vocab.STAGED,))
    if not staged:
        return {"ok": False, "reason": "no_staged"}

    contact = line_client_contact.get_contact(tenant_id, workspace_client_id)
    if not contact:
        return {"ok": False, "reason": "not_bound"}

    batch = staged[:MAX_QUESTIONS_PER_BATCH]
    remainder = staged[MAX_QUESTIONS_PER_BATCH:]
    lang = _resolve_lang(contact, tenant_id)
    text = _render_batch_message(batch, len(remainder), lang)

    if not _push(contact["line_user_id"], text, tenant_id):
        return {"ok": False, "reason": "push_failed"}

    batch_id = uuid.uuid4()
    marked = []
    try:
        for question in batch:
            marked.append(store.mark_sent(tenant_id, question["id"], batch_id))
    except Exception:
        logger.warning(
            "[line_client_pool_push] mark_sent failed mid-batch; rolling back to staged",
            exc_info=True,
        )
        for done in marked:
            try:
                store.transition(tenant_id, done["id"], vocab.STAGED)
            except Exception:
                logger.warning(
                    "[line_client_pool_push] rollback to staged failed for question_id=%s",
                    done.get("id"),
                    exc_info=True,
                )
        return {"ok": False, "reason": "state_update_failed"}

    logger.info(
        "[line_client_pool_push] batch sent tenant=%s client=%s actor=%s batch_id=%s n=%d",
        tenant_id,
        workspace_client_id,
        actor,
        batch_id,
        len(marked),
    )
    return {
        "ok": True,
        "batch_id": str(batch_id),
        "sent_count": len(marked),
        "remaining_count": len(remainder),
        "question_ids": [m["id"] for m in marked],
    }
