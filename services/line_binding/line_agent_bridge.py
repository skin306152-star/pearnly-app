# -*- coding: utf-8 -*-
"""对话 Agent 插座 ↔ LINE 入口的桥(WP5)。

line_expense.handle_expense_text 为灰度用户在关键词分支「之前」调 try_agent_turn(前门倒置):
模型自己判意图——查询/闲聊自己组织人话回复(接管本轮),超范围/闸关的写意图 → defer,
调用方逐字节落回旧 understand()+_dispatch_agent()。能力只增不减,旧路一行不改。

write_sink 是写工具的唯一落地口:loop 提议 + 接地通过后,这里分发到现有确定性执行
(记账 _do_record / 多笔 do_record_multi / 撤销 reply_undo / 改错 request_correct),
定位、风险确认、幂等全在那些既有流程里,大脑没有任何直接写库的手。
"""

from __future__ import annotations

import logging

from services.agent.loop import TurnResult  # 前门结论类型(reply/card_sent/defer_*/crash)

logger = logging.getLogger(__name__)

__all__ = [
    "TurnResult",
    "frontdoor_enabled",
    "write_enabled",
    "m3_enabled",
    "push_enabled",
    "try_agent_turn",
]


def _uid(bound_user):
    return str(bound_user["id"]) if bound_user.get("id") else None


def frontdoor_enabled(bound_user) -> bool:
    """前门倒置总闸。关 → 老确定性路一行不变。"""
    from core import feature_flags

    return feature_flags.agent_enabled_for(_uid(bound_user))


def write_enabled(bound_user) -> bool:
    """写工具子闸。关 → 记账走旧乐观路,现状不变。"""
    from core import feature_flags

    return feature_flags.agent_write_enabled_for(_uid(bound_user))


def m3_enabled(bound_user) -> bool:
    """M3 全家桶子闸(撤销/改错 + 多笔直分发)。关 → defer 交旧路,现状不变。"""
    from core import feature_flags

    return feature_flags.agent_m3_enabled_for(_uid(bound_user))


def push_enabled(bound_user) -> bool:
    """推 ERP 子闸(confirm-first 不可逆写)。默认关。"""
    from core import feature_flags

    return feature_flags.agent_push_enabled_for(_uid(bound_user))


def image_enabled(bound_user) -> bool:
    """图片意图子闸(LI)。关 → 发图走现状管线逐字节不变。"""
    from core import feature_flags

    return feature_flags.agent_image_enabled_for(_uid(bound_user))


# 计划已存的回执(LINE 专用过程文案 · 与 push_confirm._ACK 同先例留 inline)。
_PLAN_ACK = {
    "th": "รับทราบค่ะ ส่งรูป/ไฟล์มาได้เลย เดี๋ยวจัดการตามนั้นให้",
    "zh": "记下了,把图发来我就照这个办。",
    "en": "Got it — send the photo/file and I'll handle it that way.",
    "ja": "承知しました。写真を送っていただければ、その通りに処理します。",
}
# 计划回执的回溯提示:刚处理过一张图时,明说计划只管「下一张」并给回溯说法,
# 治图文同发 race 输掉后意图错配到之后那张图(用户以为说的是刚才那张)。
_PLAN_RETRO_HINT = {
    "th": " (ใช้กับรูปใบถัดไปนะคะ ถ้าหมายถึงใบเมื่อกี้ พิมพ์ว่า「ส่งใบเมื่อกี้เข้า ERP」ได้เลย)",
    "zh": "(这只管下一张图;如果你说的是刚才那张,直接说「把刚才那张推进ERP」就行。)",
    "en": ' (This applies to the NEXT photo — if you meant the one just now, say "push the last one to ERP".)',
    "ja": "(これは次の写真に適用されます。先ほどの伝票のことでしたら「さっきの伝票をERPへ」とお送りください。)",
}


def _make_write_sink(
    bound_user, text, lang, tid, ws, line_user_id, reply_token, quote_token, quoted_message_id, book
):
    """写工具落地分发。返回 sink(ctx, tool, data, say) -> TurnResult kind | None。
    book=line_expense._do_record(入口注入·避免循环 import);其余执行流按需惰性 import。
    """
    if not (book and reply_token):
        return None

    def sink(_ctx, tool, data, say=""):
        data = data or {}
        if tool == "record_expense":
            draft = data.get("draft")
            if draft is None:
                return None
            book(
                bound_user,
                reply_token,
                draft.raw_text or text,
                tid,
                ws,
                draft,
                False,
                quote_token,
                lang,
                line_user_id,
                ack_text=say,
            )
            return "card_sent"
        if tool == "record_multi":
            from services.line_binding import line_expense_multi

            items = data.get("items")  # loop 预判解析结果透传,免二次解析
            if not items:  # 透传缺失 → 不硬拆,交 crash 安全兜底
                return None
            line_expense_multi.do_record_multi(
                bound_user, reply_token, text, tid, ws, items, quote_token, lang, line_user_id
            )
            return "card_sent"
        if tool == "undo_entry":
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
            return "card_sent"
        if tool == "push_to_erp":
            from services.agent import push_confirm

            sent = push_confirm.send_confirm_card(
                bound_user,
                reply_token,
                data.get("push") or {},
                lang,
                tid,
                ws,
                line_user_id,
                quote_token=quote_token,
            )
            return "card_sent" if sent else None
        if tool == "recon_intake_start":
            from services.agent import recon_intake

            intake = data.get("intake") or {}
            recon_intake.start(
                bound_user,
                tid,
                line_user_id,
                lang,
                kind=intake.get("kind") or "bank",
                gl_account=intake.get("gl_account"),
            )
            return "card_sent"
        if tool == "plan_incoming_doc":
            from services.line_binding import line_intent_store, line_reply

            plan = data.get("plan")
            if plan is None or not tid:
                return None
            line_intent_store.set_intent(
                tid, line_user_id, plan, workspace_client_id=plan.get("book_to_id") or ws
            )
            ack = say or _PLAN_ACK.get(lang, _PLAN_ACK["en"])
            if (_ctx.anchors or {}).get("last_image_doc_id"):
                ack += _PLAN_RETRO_HINT.get(lang, _PLAN_RETRO_HINT["en"])
            line_reply.reply_text_context(
                reply_token,
                ack,
                line_user_id=line_user_id,
                tenant_id=tid,
                quote_token=quote_token,
            )
            return "card_sent"
        if tool == "edit_entry":
            from services.expense import line_correct

            line_correct.request_correct(
                bound_user,
                reply_token,
                line_user_id,
                text,
                data.get("u") or {},
                quoted_message_id,
                lang,
                tid,
                ws,
                quote_token=quote_token,
            )
            return "card_sent"
        return None  # 未知写工具 = manifest/sink 不同步 → loop 归 crash

    return sink


def try_agent_turn(
    bound_user,
    text,
    lang,
    tid,
    ws,
    line_user_id,
    history,
    *,
    reply_token=None,
    quote_token=None,
    quoted_message_id=None,
    book=None,
) -> TurnResult:
    """钥匙闸 + agent 循环 → TurnResult。故障/未启用一律归 crash(入口走安全兜底,绝不掉旧路地雷)。

    reply_token/quote_token/book=入口的出卡料;写开启时写工具经 write_sink 落现有确定性执行。
    lang 保留兼容:回复语言由模型按用户最新消息自适应,不再套模板。
    """
    import time

    from core import feature_flags

    uid = str(bound_user["id"]) if bound_user.get("id") else None
    if not feature_flags.agent_enabled_for(uid):
        return TurnResult("crash")
    started = time.monotonic()

    def _audit(kind, *, trace_id=None, tool_trace=None, degraded=""):
        """轮级审计留痕(best-effort 双保险:审计绝不挡对话)。"""
        try:
            from services.agent import turn_log

            turn_log.record(
                tenant_id=tid,
                user_id=uid,
                line_user_id=line_user_id,
                trace_id=trace_id,
                lang=lang,
                user_text=text,
                result_kind=kind,
                tool_trace=tool_trace,
                elapsed_ms=int((time.monotonic() - started) * 1000),
                degraded=degraded,
            )
        except Exception:
            logger.warning("[line agent] audit failed", exc_info=True)

    # M3 确认握手 · resume 闸:15 分钟内有待确认推送卡 + 文本是确认/取消词 → 与点按钮
    # 同效(消费同一 nonce,后到的撞 used 幂等)。闸关/无卡/非确认词/故障 → 正常对话轮。
    from services.agent import confirm_machine

    if confirm_machine.try_resume(
        bound_user, reply_token, text, lang, tenant_id=tid, line_user_id=line_user_id
    ):
        _audit("card_sent", tool_trace=[{"tool": "confirm_resume", "ok": True}])
        return TurnResult("card_sent")  # handle_postback 已回话,入口别再出声
    # 对账收件:活跃收件缺科目号且这句像编码 → 收下(别的话不吃,收件不打断正常对话)。
    from services.agent import recon_intake

    if recon_intake.try_text(bound_user, text, lang, tid, line_user_id):
        _audit("card_sent", tool_trace=[{"tool": "recon_intake_text", "ok": True}])
        return TurnResult("card_sent")
    try:
        from services.agent import loop
        from services.agent.contracts import AgentContext

        # 跨轮锚点(agent_anchor_memory):闸开才 load/采集/落库,关 = 锚点全程不流动。
        anchors_on = feature_flags.agent_anchor_enabled_for(uid) and bool(tid and line_user_id)
        loaded_anchors = {}
        if anchors_on:
            from services.line_binding import line_anchor_store

            loaded_anchors = line_anchor_store.get_anchors(tid, line_user_id)
        ctx = AgentContext(
            user=bound_user,
            tenant_id=tid,
            workspace_client_id=ws,
            line_user_id=line_user_id,
            quoted_message_id=quoted_message_id,
            anchors=dict(loaded_anchors),
            anchors_enabled=anchors_on,
        )
        sink = None
        if feature_flags.agent_write_enabled_for(uid):
            sink = _make_write_sink(
                bound_user,
                text,
                lang,
                tid,
                ws,
                line_user_id,
                reply_token,
                quote_token,
                quoted_message_id,
                book,
            )
        res = loop.handle_turn(
            text,
            ctx,
            history=history,
            allow_write=sink is not None,
            allow_m3=sink is not None and m3_enabled(bound_user),
            allow_push=sink is not None and push_enabled(bound_user),
            allow_image=sink is not None and image_enabled(bound_user),
            allow_compound=sink is not None and feature_flags.agent_compound_enabled_for(uid),
            write_sink=sink,
        )
        if anchors_on and ctx.anchors != loaded_anchors:
            line_anchor_store.set_anchors(tid, line_user_id, ctx.anchors)
        _audit(res.kind, trace_id=ctx.trace_id, tool_trace=ctx.tool_trace, degraded=ctx.degraded)
        return res
    except Exception:
        # 任何异常 → crash(铁律:Agent 不许把错误抛给用户);入口安全兜底,带 uid + 栈便于排障。
        logger.warning("[line agent] turn failed; safe fallback (uid=%s)", uid, exc_info=True)
        _audit("crash")
        return TurnResult("crash")
