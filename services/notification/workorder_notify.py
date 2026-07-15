# -*- coding: utf-8 -*-
"""工单跑批收尾通知会计(IN-0c):跑完/卡住/缺料时给发起跑批的会计推一条 LINE,治
「跑批 20 分钟会计关页走人,不知道啥时候好」。挂 runner.advance() 收尾,故障必须与跑批
结果隔离——本模块唯一入口 notify_run_outcome 自身吞掉一切异常,调用方(runner)再包一层
try/except 双保险(同 brain_shadow 佐证层规格,零主路径连坐)。

通知对象 = 该次 run_requested 的 actor(发起人);reaper 收尸自动续跑(actor=system:reaper)
与 LINE 客户答题自驱回写(actor=line_client:xxx)都不是人类会计发起,不产生通知对象,静默
跳过。去重台账走 notification_logs(复用不建表),event_ref = "{work_order_id}:{run_event_id}"
令同一次 run 恰发一条、重跑(新 run_event_id)可再发。消息不带金额/税号数字(LINE 是外部
通道):卡住原因只给「哪一步 + 缺料/异常」两个词,不带 handler 内部具体差异文案(reconcile
的 stuck reasons 里就嵌过借贷差额,那类字符串不许流出这条通道)。
"""

from __future__ import annotations

import logging
from typing import Optional

from services.workorder import engine
from services.workorder.runner import EVT_RUN_REQUESTED, RUN_STEP

logger = logging.getLogger(__name__)

TEMPLATE_DONE = "workorder_run_done"
TEMPLATE_STUCK = "workorder_run_stuck"
_EVENT_TYPE = "workorder_run"

_STEP_LABEL = {
    "zh": dict(
        intake="收料",
        sort="分类整理",
        classify="识别归类",
        reconcile="对账核对",
        compute="算税",
        package="出包",
    ),
    "th": dict(
        intake="รับเอกสาร",
        sort="จัดหมวดหมู่",
        classify="จำแนกเอกสาร",
        reconcile="กระทบยอด",
        compute="คำนวณภาษี",
        package="จัดชุดส่งมอบ",
    ),
    "en": dict(
        intake="intake",
        sort="sorting",
        classify="classification",
        reconcile="reconciliation",
        compute="tax calculation",
        package="packaging",
    ),
    "ja": dict(
        intake="資料受領",
        sort="仕分け",
        classify="分類",
        reconcile="照合",
        compute="税額計算",
        package="パッケージ化",
    ),
}
_KIND_LABEL = {
    "zh": {"needs": "缺料", "stuck": "异常"},
    "th": {"needs": "เอกสารไม่ครบ", "stuck": "ติดขัด"},
    "en": {"needs": "missing material", "stuck": "an issue"},
    "ja": {"needs": "資料不足", "stuck": "エラー"},
}
_COPY_DONE = {
    "zh": "{client} {period} 工单已处理完,去待处理看结果。",
    "th": "งาน {client} งวด {period} ประมวลผลเสร็จแล้ว ไปดูผลลัพธ์ในรายการที่รอดำเนินการได้เลยค่ะ",
    "en": "{client} {period} work order is done — check the pending queue for the result.",
    "ja": "{client} {period}のワークオーダー処理が完了しました。保留中の一覧で結果をご確認ください。",
}
_COPY_STUCK = {
    "zh": "{client} {period} 工单卡住:{reason},需要你处理。",
    "th": "งาน {client} งวด {period} ติดขัด: {reason} ต้องการให้คุณเข้าไปดำเนินการค่ะ",
    "en": "{client} {period} work order is stuck: {reason} — needs your attention.",
    "ja": "{client} {period}のワークオーダーが停止しました:{reason}。ご確認をお願いします。",
}


def notify_run_outcome(order: dict, run_event_id: int) -> None:
    """唯一入口:order = advance() 收尾后重读的 work_orders 行(tenant_id/id/period/status/
    workspace_client_id/current_step),run_event_id = 本次 run_finished/run_failed 事件 id。
    任何故障一律吞掉,不向调用方冒泡——通知是增益面,绝不许反过来影响已跑完的工单结果。"""
    try:
        _notify(order, run_event_id)
    except Exception:  # noqa: BLE001 - 通知任何故障不得影响跑批结果
        logger.warning("[workorder_notify] notify_run_outcome skipped", exc_info=True)


def _notify(order: dict, run_event_id: int) -> None:
    from core import feature_flags

    tenant_id = str(order["tenant_id"])
    work_order_id = str(order["id"])
    if not feature_flags.pearnly_ai_run_notify_enabled_for(tenant_id):
        return  # 闸关:零发送零台账写

    if order.get("status") == engine.STATUS_REVIEW:
        template = TEMPLATE_DONE
    elif order.get("status") == engine.STATUS_STUCK:
        template = TEMPLATE_STUCK
    else:
        return  # 非终态(running/collecting/archive)不该走到这,防御性早退

    from core import db

    with db.get_cursor() as cur:
        user_id = _requester_user_id(cur, tenant_id, work_order_id, run_event_id)
        if not user_id:
            return  # 非人类发起(reaper 续跑 / LINE 客户答题自驱)无通知对象,静默跳过
        binding = _line_binding(cur, user_id)
        client_name = _client_name(cur, tenant_id, order.get("workspace_client_id"))
        halt_kind = (
            _halt_kind(cur, tenant_id, work_order_id) if template == TEMPLATE_STUCK else None
        )

    from services.notification import store as notif_store

    event_ref = f"{work_order_id}:{run_event_id}"
    if not binding:
        _log(
            notif_store, user_id, tenant_id, template, event_ref, None, "skipped", "no_line_binding"
        )
        return
    if notif_store.already_sent(user_id, tenant_id, template, event_ref):
        return  # 同一次 run 已发过,不重复推(重跑=新 run_event_id 自然可再发)

    line_user_id = binding["line_user_id"]
    lang = _resolve_lang(line_user_id, tenant_id, binding.get("preferred_lang"))
    reason = _reason_phrase(lang, order.get("current_step"), halt_kind) if halt_kind else None
    text = _copy_for(template, lang, client_name, order.get("period"), reason)

    from services.line_binding import line_reply

    ok = line_reply.push_text_context(line_user_id, text, tenant_id=tenant_id)
    _log(
        notif_store,
        user_id,
        tenant_id,
        template,
        event_ref,
        line_user_id,
        "sent" if ok is not False else "failed",
    )


def _log(
    notif_store, user_id, tenant_id, template, event_ref, line_user_id, status, error=None
) -> None:
    notif_store.log_notification(
        user_id, tenant_id, None, template, _EVENT_TYPE, event_ref, line_user_id, status, error
    )


def _requester_user_id(cur, tenant_id: str, work_order_id: str, run_event_id) -> Optional[str]:
    """该次 run 的发起人:紧邻本次收尾事件之前那条 run_requested 的 actor。只认
    "user:<id>" 形态(会计经 /run 路由或裁决/补料自驱发起);reaper/line_client 等系统或
    终端客户自驱的 actor 不是可通知的会计账号,返回 None。"""
    cur.execute(
        "SELECT actor FROM work_order_events "
        "WHERE tenant_id = %s AND work_order_id = %s AND step = %s AND event_type = %s "
        "AND id < %s ORDER BY id DESC LIMIT 1",
        (tenant_id, work_order_id, RUN_STEP, EVT_RUN_REQUESTED, run_event_id),
    )
    row = cur.fetchone()
    actor = (row["actor"] if isinstance(row, dict) else row[0]) if row else None
    return actor[len("user:") :] if actor and actor.startswith("user:") else None


def _line_binding(cur, user_id: str) -> Optional[dict]:
    cur.execute(
        "SELECT lb.line_user_id, u.preferred_lang FROM line_bindings lb "
        "JOIN users u ON u.id = lb.user_id WHERE lb.user_id = %s LIMIT 1",
        (user_id,),
    )
    row = cur.fetchone()
    return dict(row) if row else None


def _client_name(cur, tenant_id: str, workspace_client_id) -> str:
    if not workspace_client_id:
        return "-"
    cur.execute(
        "SELECT name FROM workspace_clients WHERE tenant_id = %s AND id = %s",
        (tenant_id, workspace_client_id),
    )
    row = cur.fetchone()
    name = (row["name"] if isinstance(row, dict) else row[0]) if row else None
    return name or "-"


def _halt_kind(cur, tenant_id: str, work_order_id: str) -> str:
    """当前卡点是「缺料」还是「异常」——取最近一条卡停事件的真实词汇(engine.EVT_NEEDS /
    EVT_STUCK),不猜。只取 event_type,绝不读 payload(missing/reasons 里可能嵌金额,见
    steps/reconcile.py 的试算不平文案)。"""
    cur.execute(
        "SELECT event_type FROM work_order_events "
        "WHERE tenant_id = %s AND work_order_id = %s AND event_type = ANY(%s) "
        "ORDER BY id DESC LIMIT 1",
        (tenant_id, work_order_id, [engine.EVT_STUCK, engine.EVT_NEEDS]),
    )
    row = cur.fetchone()
    etype = (row["event_type"] if isinstance(row, dict) else row[0]) if row else engine.EVT_STUCK
    return "needs" if etype == engine.EVT_NEEDS else "stuck"


def _resolve_lang(line_user_id: str, tenant_id: str, preferred_lang: Optional[str]) -> str:
    from services.expense import line_lang

    return line_lang.card_lang(line_user_id, tenant_id, preferred_lang or "th")


def _reason_phrase(lang: str, step: Optional[str], kind: str) -> str:
    step_label = _STEP_LABEL.get(lang, _STEP_LABEL["en"]).get(step, step or "-")
    kind_label = _KIND_LABEL.get(lang, _KIND_LABEL["en"])[kind]
    if lang == "en":
        return f"{kind_label} at {step_label}"
    if lang == "th":
        return f"{step_label} {kind_label}"
    return f"{step_label}{kind_label}"


def _copy_for(
    template: str, lang: str, client_name: str, period: Optional[str], reason: Optional[str]
) -> str:
    copy = _COPY_DONE if template == TEMPLATE_DONE else _COPY_STUCK
    text = copy.get(lang, copy["en"])
    return text.format(client=client_name, period=period or "-", reason=reason or "-")
