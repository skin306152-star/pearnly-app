# -*- coding: utf-8 -*-
"""推 ERP confirm-first(设计 §6.2)—— 唯一「先确认再执行」的写工具落地。

推错要去 ERP 里删,不可逆 → 三层幂等:一次性 nonce(防双击/重放,1 小时过期)→
has_recent_successful_push(防跨会话重推)→ erp_push_logs 唯一状态源(铁律 #12)。
执行编排逐行镜像 routes/erp_push_log_routes.py 手动推送权威范式,trigger="line_agent"
留审计;services/erp 只调用、绝不修改。推送本体阻塞(网络/重试)→ 确认后先回执
「正在推送」,执行进后台线程,结果经 LINE push 消息送达(失败诚实,绝不谎报成功)。
"""

from __future__ import annotations

import json
import logging
import threading

from core import db
from services.agent import agent_i18n, copy_map

logger = logging.getLogger(__name__)

REF_KIND = "agent_push"
NONCE_TTL_HOURS = 1  # 推送确认卡不该隔夜有效(默认 72h 是记账卡口径)

_BTN_OK = {"th": "ยืนยันส่ง", "zh": "确认推送", "en": "Confirm", "ja": "送信する"}
_BTN_NO = {"th": "ยกเลิก", "zh": "取消", "en": "Cancel", "ja": "キャンセル"}
_ACK = {
    "th": "กำลังส่งเข้า ERP ให้อยู่ค่ะ เดี๋ยวแจ้งผลนะคะ",
    "zh": "正在推送到 ERP,稍后告诉你结果。",
    "en": "Pushing to ERP now — I'll let you know the result.",
    "ja": "ERP へ送信しています。結果をお知らせしますね。",
}
# 成功/重复走现成 agent.ok.push / agent.ok.push_dup 四语键(为 M3 预登记·两侧 parity 已守);
# ACK/FAIL 是 LINE 专用过程文案(M5 网页 Agent 不复用确认卡流程)→ 留 inline,与安全兜底同先例。
_FAIL = {
    "th": "ส่งเข้า ERP ไม่สำเร็จค่ะ: {reason} · ดูรายละเอียดที่หน้าประวัติการส่งได้เลย",
    "zh": "推送失败:{reason}·可到推送日志页看详情。",
    "en": "Push failed: {reason} · see the push log page for details.",
    "ja": "送信に失敗しました:{reason} · 送信ログページをご確認ください。",
}


def _t(table: dict, lang: str) -> str:
    return table.get(lang, table["en"])


def _slot(v) -> str:
    """空值展示成 -(占位串编码/消毒交 copy_map._render,单一实现)。"""
    return "-" if v in (None, "") else str(v)


def send_confirm_card(
    bound_user, reply_token, push: dict, lang, tid, ws, line_user_id, quote_token=""
) -> bool:
    """接地通过的推送提案 → 铸一次性 nonce + 出确认卡。【不执行任何推送】。
    出不了卡(nonce 铸造失败等)返回 False → loop 归 crash 安全兜底。"""
    from services.line_binding import line_action_nonce, line_postback, line_reply

    try:
        ref = json.dumps(
            {
                "kind": REF_KIND,
                "history_id": str(push["history_id"]),
                "endpoint_id": str(push["endpoint_id"]),
            }
        )
        with db.get_cursor_rls(tid, commit=True) as cur:
            token = line_action_nonce.mint(
                cur,
                tenant_id=tid,
                workspace_client_id=ws,
                action_ref=ref,
                user_id=str(bound_user.get("id") or ""),
                ttl_hours=NONCE_TTL_HOURS,
            )
        if not token:
            return False
        body = agent_i18n.render(
            copy_map._render(
                "agent.confirm.push",
                invoice_no=_slot(push.get("invoice_no")),
                amount=_slot(push.get("amount")),
                endpoint=_slot(push.get("endpoint_name")),
            ),
            lang,
        )
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
                        "data": line_postback.agent_push_confirm_data(token),
                    },
                    {
                        "type": "postback",
                        "label": _t(_BTN_NO, lang)[:20],
                        "data": line_postback.agent_push_cancel_data(token),
                    },
                ],
            },
        }
        line_reply.reply_messages_context(
            reply_token, [msg], line_user_id=line_user_id, tenant_id=tid, quote_token=quote_token
        )
        return True
    except Exception:
        logger.warning("[agent push] confirm card failed", exc_info=True)
        return False


def _parse_ref(raw) -> dict | None:
    try:
        ref = json.loads(raw or "")
        if ref.get("kind") == REF_KIND and ref.get("history_id") and ref.get("endpoint_id"):
            return ref
    except (ValueError, TypeError):
        pass
    return None


def handle_postback(bound_user, reply_token, action, token, lang, *, runner=None) -> None:
    """确认卡按钮回调。nonce 原子消费(层 1 幂等);确认 → 权限复核 → ack → 后台执行。
    runner 注入是给测试的(默认后台线程,不阻塞 webhook 事件循环)。"""
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
    if res["status"] == "used":
        # 双击/重放:已推成功就诚实说推过了,否则按失效卡处理(不二次推送)。
        ref = _parse_ref(res.get("action_ref"))
        if ref and db.has_recent_successful_push(
            ref["history_id"], ref["endpoint_id"], str(bound_user.get("id") or "")
        ):
            ep = db.get_erp_endpoint(str(bound_user.get("id") or ""), ref["endpoint_id"]) or {}
            _say(_dup_text(ep.get("name"), None, lang))
            return
        res = {"status": "stale"}
    ref = _parse_ref(res.get("action_ref")) if res["status"] == "ok" else None
    if ref is None:  # missing/伪造/坏 ref 统一失效口径
        _say(line_client.t_line(lang, "card_action_stale"))
        return
    if action == line_postback.ACTION_AGENT_PUSH_CANCEL:
        _say(agent_i18n.render("agent.confirm.cancelled", lang))
        return
    from core.route_helpers import _plan_permissions

    if not _plan_permissions((bound_user or {}).get("plan")).get("can_push_erp"):
        _say(agent_i18n.render("agent.failure.forbidden", lang))
        return
    _say(_t(_ACK, lang))
    run = runner or (lambda fn: threading.Thread(target=fn, daemon=True).start())
    run(
        lambda: _execute_and_notify(
            bound_user, tid, ref["history_id"], ref["endpoint_id"], lang, luid
        )
    )


def _execute_and_notify(user, tid, history_id, endpoint_id, lang, line_user_id) -> None:
    """后台执行 + 结果 push 消息。任何异常都给用户一句诚实失败,绝不静默。"""
    from services.line_binding import line_reply

    try:
        out = _execute_push(user, tid, history_id, endpoint_id)
        text = _result_text(out, lang)
    except Exception:
        logger.exception("[agent push] execute failed history=%s", str(history_id)[:8])
        text = agent_i18n.render("agent.failure.unknown", lang)
    try:
        line_reply.push_text_context(line_user_id, text, tenant_id=tid)
    except Exception:
        logger.warning("[agent push] result notify failed", exc_info=True)


def _execute_push(user, tid, history_id, endpoint_id) -> dict:
    """真实推送编排 —— 镜像 routes/erp_push_log_routes.py:34-162(唯一权威范式)。
    层 2 幂等:已成功推过 → skipped_dup 日志 + 不重推;层 3:erp_push_logs 唯一状态源。"""
    from services.erp import erp_push as _erp

    uid = str(user["id"])
    history = db.get_ocr_history_detail(uid, history_id, tenant_id=tid)
    if not history:
        return {"kind": "failure", "code": "history_not_found"}
    endpoint = db.get_erp_endpoint(uid, endpoint_id)
    if not endpoint or not endpoint.get("enabled", True):
        return {"kind": "failure", "code": "no_endpoint"}

    existing = db.has_recent_successful_push(history_id, endpoint["id"], uid)
    if existing:
        db.insert_push_log(
            user_id=uid,
            endpoint_id=endpoint["id"],
            history_id=history_id,
            invoice_no=history.get("invoice_no"),
            seller_name=history.get("seller_name"),
            total_amount=history.get("total_amount"),
            status="skipped_dup",
            http_status=200,
            request_body={
                "adapter": endpoint.get("adapter"),
                "skipped_reason": "already_success",
                "prior_log_id": str(existing.get("id")),
            },
            response_body=existing.get("response_body"),
            error_msg=None,
            attempt=1,
            elapsed_ms=0,
            trigger="line_agent",
        )
        return {
            "kind": "dup",
            "endpoint": endpoint.get("name") or "ERP",
            "invoice_no": history.get("invoice_no"),
        }

    result = _erp.push_to_endpoint(endpoint, history)
    final_status = db.classify_push_status(result["success"], result.get("error_msg"))
    log_id = db.insert_push_log(
        user_id=uid,
        endpoint_id=endpoint["id"],
        history_id=history_id,
        invoice_no=history.get("invoice_no"),
        seller_name=history.get("seller_name"),
        total_amount=history.get("total_amount"),
        status=final_status,
        http_status=result.get("http_status"),
        request_body=result.get("request_body"),
        response_body=result.get("response_body"),
        error_msg=result.get("error_msg"),
        attempt=1,
        elapsed_ms=result.get("elapsed_ms", 0),
        trigger="line_agent",
    )
    db.update_endpoint_stats(endpoint["id"], db.counts_as_endpoint_success(final_status))
    db.update_history_push_status(history_id, final_status)
    if final_status == "failed" and log_id and not db.is_user_data_error(result.get("error_msg")):
        first_delay = db.get_erp_retry_delay_sec(0)
        if first_delay is not None:
            db.schedule_log_retry(str(log_id), first_delay)

    ep_name = endpoint.get("name") or "ERP"
    inv = history.get("invoice_no")
    if final_status == "skipped_dup":
        return {"kind": "dup", "endpoint": ep_name, "invoice_no": inv}
    if db.counts_as_endpoint_success(final_status):
        return {"kind": "ok", "endpoint": ep_name, "invoice_no": inv}
    return {"kind": "failure", "code": "push_failed", "error": result.get("error_msg") or ""}


def _ok_text(endpoint, invoice_no, lang) -> str:
    line = copy_map._render(
        "agent.ok.push", endpoint=_slot(endpoint or "ERP"), bill_no=_slot(invoice_no)
    )
    return agent_i18n.render(line, lang)


def _dup_text(endpoint, invoice_no, lang) -> str:
    line = copy_map._render(
        "agent.ok.push_dup", endpoint=_slot(endpoint or "ERP"), bill_no=_slot(invoice_no)
    )
    return agent_i18n.render(line, lang)


def _result_text(out: dict, lang: str) -> str:
    if out["kind"] == "ok":
        return _ok_text(out.get("endpoint"), out.get("invoice_no"), lang)
    if out["kind"] == "dup":
        return _dup_text(out.get("endpoint"), out.get("invoice_no"), lang)
    code = out.get("code")
    if code == "history_not_found":
        return agent_i18n.render("agent.failure.history_not_found", lang)
    if code == "no_endpoint":
        return agent_i18n.render("agent.failure.no_endpoint", lang)
    reason = _friendly_reason(out.get("error") or "", lang)
    return _t(_FAIL, lang).format(reason=reason)


def _friendly_reason(error_msg: str, lang: str) -> str:
    """失败码人话化:复用推送日志同一套 friendly 目录,未命中给截断原文(诚实优先)。"""
    try:
        from services.erp import push_log_friendly

        hit = push_log_friendly.friendly_any(error_msg)
        if hit:
            return hit.get(lang) or hit.get("en") or ""
    except Exception:
        logger.warning("[agent push] friendly reason failed", exc_info=True)
    return (error_msg or "unknown")[:120]
