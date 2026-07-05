# -*- coding: utf-8 -*-
"""知识库问答 confirm-first(W3-4)—— 计费型问答的「先确认再扣费」落地。

每答一次扣 ฿0.50(与网页 /api/knowledge/ask 同一拍板 2026-06-05 · 同一钱路径
contract.charge_credits → deduct_thb),自动触发会烧用户钱 → 大脑只许发确认卡,
用户点「ยืนยัน」才检索+生成+扣费。镜像 push_confirm 三层套路:一次性 nonce
(防双击/重放)→ 确认后 ack → 后台执行 → 结果 push 送达(失败诚实)。
no_answer 不扣费(与网页同口径:没答上来不收钱)。
"""

from __future__ import annotations

import json
import logging
import threading

from core import db
from services.agent import agent_i18n

logger = logging.getLogger(__name__)

REF_KIND = "agent_kb"
NONCE_TTL_HOURS = 1
# ฿0.50/答(satang)· 与 routes/knowledge_ask_routes._RAG_ANSWER_SATANG 同一拍板同一数;
# 网页/LINE 各留一份是层向约束(services 不许 import routes),改价两处一起改。
_RAG_ANSWER_SATANG = 50

_BTN_OK = {"th": "ยืนยันถาม", "zh": "确认提问", "en": "Confirm", "ja": "質問する"}
_BTN_NO = {"th": "ยกเลิก", "zh": "取消", "en": "Cancel", "ja": "キャンセル"}
# LINE 专用过程文案 inline(与 push_confirm._ACK 同先例:确认卡流程不进 copy_map 四语键)。
_CARD = {
    "th": "คำถามนี้จะใช้สิทธิ์ตอบจากฐานความรู้ 1 ครั้ง (฿0.50)\n“{q}”\nยืนยันไหมคะ?",
    "zh": "这个问题要用 1 次知识库问答额度(฿0.50)\n「{q}」\n继续吗?",
    "en": "This will use 1 knowledge answer credit (฿0.50)\n“{q}”\nProceed?",
    "ja": "この質問はナレッジ回答枠を1回使います(฿0.50)\n「{q}」\nよろしいですか?",
}
_ACK = {
    "th": "⏳ รับคำยืนยันแล้วค่ะ กำลังค้นหาคำตอบจากฐานความรู้ เดี๋ยวส่งให้นะคะ",
    "zh": "⏳ 已确认,正在从知识库找答案…马上回报。",
    "en": "⏳ Confirmed — searching the knowledge base, answer coming shortly.",
    "ja": "⏳ 確認しました。ナレッジベースを検索中です。まもなくお答えします。",
}
_NO_ANSWER = {
    "th": "ยังไม่พบข้อมูลเรื่องนี้ในฐานความรู้ค่ะ (ครั้งนี้ไม่คิดค่าใช้จ่าย) ลองอัปโหลดเอกสารที่เกี่ยวข้องเข้าฐานความรู้ก่อนนะคะ",
    "zh": "知识库里还没有这方面的资料(本次不收费)。可以先在网页端把相关文件传进知识库。",
    "en": "No source in the knowledge base covers this yet (not charged). Try uploading related documents first.",
    "ja": "ナレッジベースにこの件の資料がまだありません(今回は課金されません)。関連資料をアップロードしてみてください。",
}
_NO_BALANCE = {
    "th": "ยอดเงินคงเหลือไม่พอสำหรับการถามฐานความรู้ (฿0.50/ครั้ง) เติมเงินก่อนนะคะ",
    "zh": "余额不足以使用知识库问答(฿0.50/次),请先充值。",
    "en": "Balance too low for a knowledge answer (฿0.50 each) — please top up first.",
    "ja": "残高が不足しています(1回 ฿0.50)。先にチャージしてください。",
}
_FAIL = {
    "th": "❌ ค้นหาคำตอบไม่สำเร็จค่ะ ลองใหม่อีกครั้งนะคะ (ครั้งนี้ไม่คิดค่าใช้จ่าย)",
    "zh": "❌ 检索失败,这次没收费,请稍后再试。",
    "en": "❌ Answer lookup failed — not charged, please try again.",
    "ja": "❌ 検索に失敗しました。課金されていません。もう一度お試しください。",
}
_SOURCES = {
    "th": "อ้างอิง {n} แหล่ง",
    "zh": "引用 {n} 个来源",
    "en": "{n} sources cited",
    "ja": "出典 {n} 件",
}


def _t(table: dict, lang: str) -> str:
    return table.get(lang, table["en"])


def send_confirm_card(bound_user, reply_token, question, lang, tid, line_user_id, quote_token=""):
    """问题 → 铸一次性 nonce + 出确认卡。【不检索不扣费】。出不了卡返回 False。"""
    from services.line_binding import line_action_nonce, line_postback, line_reply

    q = (question or "").strip()
    if not (q and tid and line_user_id):
        return False
    try:
        ref = json.dumps({"kind": REF_KIND, "q": q[:400]}, ensure_ascii=False)
        with db.get_cursor_rls(tid, commit=True) as cur:
            token = line_action_nonce.mint(
                cur,
                tenant_id=tid,
                workspace_client_id=None,
                action_ref=ref,
                user_id=str(bound_user.get("id") or ""),
                ttl_hours=NONCE_TTL_HOURS,
            )
        if not token:
            return False
        body = _t(_CARD, lang).format(q=q[:80])
        msg = {
            "type": "template",
            "altText": body[:160] or "Pearnly",
            "template": {
                "type": "buttons",
                "text": body[:160],
                "actions": [
                    {
                        "type": "postback",
                        "label": _t(_BTN_OK, lang)[:20],
                        "data": line_postback.agent_kb_confirm_data(token),
                    },
                    {
                        "type": "postback",
                        "label": _t(_BTN_NO, lang)[:20],
                        "data": line_postback.agent_kb_cancel_data(token),
                    },
                ],
            },
        }
        line_reply.reply_messages_context(
            reply_token, [msg], line_user_id=line_user_id, tenant_id=tid, quote_token=quote_token
        )
        return True
    except Exception:
        logger.warning("[agent kb] confirm card failed", exc_info=True)
        return False


def _parse_ref(raw):
    try:
        ref = json.loads(raw or "")
        if ref.get("kind") == REF_KIND and (ref.get("q") or "").strip():
            return ref
    except (ValueError, TypeError):
        pass
    return None


def handle_postback(bound_user, reply_token, action, token, lang, *, runner=None) -> None:
    """确认卡按钮回调。nonce 原子消费(幂等);确认 → 余额前置检查 → ack → 后台检索+扣费。"""
    from services.line_binding import line_client, line_postback, line_reply

    tid = str(bound_user["tenant_id"]) if bound_user.get("tenant_id") else None
    luid = bound_user.get("line_user_id") or ""

    def _say(text):
        line_reply.reply_text_context(reply_token, text, line_user_id=luid, tenant_id=tid)

    if not (tid and token):
        _say(line_client.t_line(lang, "card_action_stale"))
        return
    from services.line_binding import line_action_nonce as nonce

    with db.get_cursor_rls(tid, commit=True) as cur:
        res = nonce.consume(cur, tenant_id=tid, token=token)
    if res["status"] == "expired":
        _say(line_client.t_line(lang, "card_action_expired"))
        return
    # used/stale:问答无"已答过可复述"语义,双击一律按失效卡(与 push_confirm 的 used 分支
    # 有意分叉:推 ERP 能查是否推成功来复述,检索答案不可回放 → 两处骨架像但此处不可合并)。
    if res["status"] != "ok":
        _say(line_client.t_line(lang, "card_action_stale"))
        return
    ref = _parse_ref(res.get("action_ref"))
    if ref is None:
        _say(line_client.t_line(lang, "card_action_stale"))
        return
    if action == line_postback.ACTION_AGENT_KB_CANCEL:
        _say(agent_i18n.render("agent.confirm.cancelled", lang))
        return
    uid = str(bound_user.get("id") or "")
    try:  # 余额前置:不足在花模型钱之前拦(豁免账号放行);查询异常容忍不阻断
        bill = db.get_billing_status_combined(uid, tid)
        if not bill.get("is_exempt") and float(bill.get("balance_thb", 0)) < 0.5:
            _say(_t(_NO_BALANCE, lang))
            return
    except Exception:
        pass
    _say(_t(_ACK, lang))
    run = runner or (lambda fn: threading.Thread(target=fn, daemon=True).start())
    run(lambda: _execute_and_notify(bound_user, tid, ref["q"], lang, luid))


def _execute_and_notify(user, tid, question, lang, line_user_id) -> None:
    """后台检索+生成+落库+扣费,结果 push。任何异常给一句诚实失败,绝不静默、绝不白扣。"""
    from services.line_binding import line_reply

    try:
        text = _answer(user, tid, question, lang)
    except Exception:
        logger.exception("[agent kb] execute failed")
        text = _t(_FAIL, lang)
    try:
        line_reply.push_text_context(line_user_id, text, tenant_id=tid)
    except Exception:
        logger.warning("[agent kb] result notify failed", exc_info=True)


def _answer(user, tid, question, lang) -> str:
    """检索→生成→落库→(答上了才)扣费。可见范围与网页同口径(get_visible_client_ids_for_user)。"""
    from services.knowledge import ask, contract, dal, embedding, search

    scope = db.get_visible_client_ids_for_user(user)
    query_vector = embedding.embed_texts([question], is_query=True)[0]
    with db.get_cursor_rls(tid) as cur:
        hits = search.search_chunks(
            cur,
            tenant_id=tid,
            accessible_ids=scope,
            query_vector=query_vector,
            limit=search.DEFAULT_TOP_K,
        )
    result = ask.answer_question(question, hits)
    with db.get_cursor_rls(tid, commit=True) as cur:
        answer = dal.create_answer(
            cur,
            tenant_id=tid,
            workspace_client_id=None,
            question=question,
            answer=result.answer,
            citations=result.citations,
            model=result.model,
            no_answer=result.no_answer,
            created_by=str(user.get("id") or ""),
        )
    if result.no_answer:
        return _t(_NO_ANSWER, lang)
    contract.charge_credits(
        tid,
        "rag_answer",
        _RAG_ANSWER_SATANG,
        {"answer_id": answer.id, "user_id": str(user.get("id") or ""), "channel": "line_agent"},
    )
    tail = _t(_SOURCES, lang).format(n=len(result.citations)) if result.citations else ""
    return result.answer + (f"\n\n{tail}" if tail else "")
