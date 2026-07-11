# -*- coding: utf-8 -*-
"""LINE 待问客户池 · 周期催办 + 关闭清扫(D2 方案 §5/§6.4/§7.2 S6 · 主窗修正 1②)。

挂 `services/background_loops.run_recovery_tick` 顺带跑(无 cron,`proactive.py` 同挂点)。
tick 内**先扫后催**——清扫先于催办执行,别催一个已经被会计处理掉的问题(方案 §6.4 硬门)。

清扫(主窗修正 1②:不改 workorder 引擎写路径,原 §0 三条自动关闭规则收窄为本 tick
兜底扫描的两条,规则 3「period 关账」与规则 2 同落点已合并):
  规则 1 该票在问题创建之后已有人工裁决(读 `evidence.replay_items_by_type` latest-wins)
        → PENDING 问题转 RESOLVED_INTERNALLY(该态原生合法边);STAGED/MANUAL_REVIEW
          问题转 CANCELLED——`client_pool_vocab.LEGAL_TRANSITIONS`(S1 单一事实源,
          `tests/unit/test_client_pool_vocab.py` 钉死)不许这两态直转 resolved_internally,
          CANCELLED 对三态都合法,语义同样是"不必再等这条了",不为本模块放宽共享契约。
  规则 2 所属工单已 archive(`engine.STATUS_ARCHIVE`,账已封)→ 该问题转 CANCELLED。
清扫只读 `services/workorder` 既有读口(`store.get_work_order`/`list_events` +
`evidence.replay_items_by_type`),零写路径依赖——不 import `api.py`/`freeze.py`/
`archive.py` 的写口(C2/C3 刚加固域,外围功能不倒灌依赖)。逐条 try/except 不连坐。

催办(照 `proactive.py` 范式逐条对齐,§5.1 复用清单):
  三层节流——进程内 1h(`_TICK_MIN_INTERVAL_S`)→ 曼谷 10:00–18:00 日内窗口先判免费
  退出 → `notification_logs` 台账去重(`already_sent`/`log_notification`,template_code=
  "line_client_dunning",event_ref=f"{batch_id}:{iso_year}-W{iso_week}",每批每周至多
  一封)。逐 tenant 闸 `pearnly_ai_client_pool_enabled_for`(默认关 fail-closed)。催办
  对象:status=pending 且 sent_at ≤ now-3天,按 (tenant, client, batch) 分组一封,跨月
  不停(pending 不过期)。

`notification_logs.user_id` 是 NOT NULL UUID,客户是 `workspace_clients` 主体不是
Pearnly 登录用户、没有天然 user_id 可填——复用 tenant_id 当 user_id:`已发` 判定只按
(user_id, template_code, event_ref) 命中,event_ref 已含 batch_id 保证跨客户/跨批不撞;
`apply_tenant_or_user_rls` 按 tenant_id 命中即可见,不破坏隔离。
"""

from __future__ import annotations

import asyncio
import logging
import time
from datetime import timedelta

from services.line_binding import client_pool_vocab as vocab

logger = logging.getLogger(__name__)

TEMPLATE_CODE = "line_client_dunning"
CHASE_AFTER_DAYS = 3  # 推送后 3 天无回答起催(方案 §5.2)
WINDOW_HOURS = range(10, 18)  # 曼谷 10:00–18:00,工作时段不半夜吵客户
_TICK_MIN_INTERVAL_S = 3600
_last_run = 0.0

# 人工裁决事件类型字面量:services/workorder 全域(api.py/evidence.py/package.py 等)
# 均各自内联同一字符串,无共享导出常量——本模块照此既有惯例,不新造依赖。
_EVT_HUMAN_DECISION = "human_decision"

_COPY = {
    "th": "🙏 คำถามที่ถามไปก่อนหน้านี้ {n} รายการยังไม่ได้รับคำตอบเลยค่ะ รบกวนช่วยยืนยันหน่อยได้ไหมคะ",
    "zh": "上次问的 {n} 条还没收到,方便帮我确认下吗?🙏",
    "en": "Hi! I haven't heard back on {n} question(s) I sent earlier — could you take a look? 🙏",
    "ja": "以前お送りした{n}件の確認事項について、まだご回答をいただいていません。ご確認いただけますか?🙏",
}


def _in_window(now) -> bool:
    return now.hour in WINDOW_HOURS


# ---------------------------------------------------------------------------
# B. 关闭清扫(先扫后催)
# ---------------------------------------------------------------------------


def _sweep_active_questions(now) -> int:
    """扫全部租户 active 问题,命中两条关闭规则的转终态。逐条 try/except 不连坐,
    返回本轮实际关闭条数。"""
    from services.line_binding import line_client_pool_store as pool_store

    closed = 0
    for row in pool_store.list_active_all():
        try:
            if _sweep_one(row, now):
                closed += 1
        except Exception:
            logger.warning(
                "[line_client_dunning] sweep failed qid=%s", row.get("id"), exc_info=True
            )
    return closed


def _sweep_one(row: dict, now) -> bool:
    """单条问题的关闭判定。闸关的租户跳过(0 副作用,fail-closed)。"""
    from core import db
    from core import feature_flags
    from services.workorder import engine
    from services.workorder import evidence
    from services.workorder import store as wo_store

    tenant_id = row["tenant_id"]
    if not feature_flags.pearnly_ai_client_pool_enabled_for(str(tenant_id)):
        return False

    work_order_id = str(row["work_order_id"])
    item_id = str(row["item_id"])

    # 判定与落笔分两段:读侧读完就关掉游标,再另开一个连接写(同 line_client_answer.
    # _decided_after → _record_decision 的分段范式),不把读游标横跨到 pool_store.
    # transition 自己的 db.get_cursor_rls 之上。
    with db.get_cursor(commit=False) as cur:
        wo = wo_store.get_work_order(cur, tenant_id=str(tenant_id), work_order_id=work_order_id)
        if wo is None:
            return False
        if wo["status"] == engine.STATUS_ARCHIVE:
            target = vocab.CANCELLED
        else:
            events = wo_store.list_events(
                cur, tenant_id=str(tenant_id), work_order_id=work_order_id
            )
            decided = evidence.replay_items_by_type(events, _EVT_HUMAN_DECISION).get(item_id)
            created_at = row.get("created_at")
            decided_after = bool(
                decided and decided.get("at") and created_at and decided["at"] > created_at
            )
            if not decided_after:
                target = None
            elif row["status"] == vocab.PENDING:
                target = vocab.RESOLVED_INTERNALLY
            else:
                # staged/manual_review 直转 resolved_internally 不在 LEGAL_TRANSITIONS
                # 合法边内(S1 契约钉死),CANCELLED 对三态皆合法,退而求其次同样封口。
                target = vocab.CANCELLED

    if target is None:
        return False
    return _close(tenant_id, row, target)


def _close(tenant_id, row: dict, to_status: str) -> bool:
    """结构化跳转;latest-wins 竞态(期间被别处并发关闭)静默放行,不算本轮新关闭。"""
    from services.line_binding import line_client_pool_store as pool_store

    try:
        pool_store.transition(tenant_id, row["id"], to_status)
        return True
    except pool_store.IllegalTransitionError:
        return False


# ---------------------------------------------------------------------------
# A. 周期催办
# ---------------------------------------------------------------------------


def _group_by_batch(rows: list) -> dict:
    """按 (tenant_id, workspace_client_id, batch_id) 分组,同批合并催一封(方案 §5.2)。"""
    groups: dict = {}
    for row in rows:
        batch_id = row.get("batch_id")
        if batch_id is None:
            logger.warning(
                "[line_client_dunning] pending 问题缺 batch_id · qid=%s 跳过", row.get("id")
            )
            continue
        key = (row["tenant_id"], row["workspace_client_id"], batch_id)
        groups.setdefault(key, []).append(row)
    return groups


def _resolve_lang(contact: dict, tenant_id) -> str:
    """语言优先取该 LINE 号最近实际对话语言,查不到/异常回落 contact.preferred_lang
    (fail-open,同 `line_client_pool_push._resolve_lang`/`proactive._copy_for` 同款兜底)。"""
    preferred = contact.get("preferred_lang") or "th"
    try:
        from services.expense import line_lang

        return line_lang.card_lang(contact["line_user_id"], tenant_id, preferred)
    except Exception:
        return preferred


def _chase_one_batch(tenant_id, workspace_client_id, batch_id, questions: list, now) -> str:
    """单批催办:闸判定 → 台账去重 → 找联系人 → 发送 → 落台账。返回
    "sent"/"failed"/"skip:<reason>"(skip 不计入调用方 sent/failed 计数)。"""
    from core import feature_flags
    from services.line_binding import line_client_contact
    from services.line_binding import line_reply
    from services.notification import store

    if not feature_flags.pearnly_ai_client_pool_enabled_for(str(tenant_id)):
        return "skip:disabled"

    iso_year, iso_week, _ = now.isocalendar()
    event_ref = f"{batch_id}:{iso_year}-W{iso_week:02d}"
    if store.already_sent(str(tenant_id), tenant_id, TEMPLATE_CODE, event_ref):
        return "skip:already_sent"

    contact = line_client_contact.get_contact(tenant_id, workspace_client_id)
    if not contact:
        return "skip:not_bound"

    lang = _resolve_lang(contact, tenant_id)
    text = (_COPY.get(lang) or _COPY["th"]).format(n=len(questions))

    try:
        ok = (
            line_reply.push_text_context(contact["line_user_id"], text, tenant_id=tenant_id)
            is not False
        )
    except Exception:
        logger.warning("[line_client_dunning] push_text_context raised", exc_info=True)
        ok = False

    store.log_notification(
        str(tenant_id),
        tenant_id,
        None,
        TEMPLATE_CODE,
        "dunning",
        event_ref,
        contact["line_user_id"],
        "sent" if ok else "failed",
    )
    return "sent" if ok else "failed"


def _chase_pending(now) -> tuple[int, int]:
    """扫 3 天无回答的 pending 批次,逐批 try/except 不连坐。返回 (sent, failed)。"""
    from services.line_binding import line_client_pool_store as pool_store

    threshold = now - timedelta(days=CHASE_AFTER_DAYS)
    rows = pool_store.list_pending_for_dunning(sent_before=threshold)
    sent = failed = 0
    for (tenant_id, workspace_client_id, batch_id), questions in _group_by_batch(rows).items():
        try:
            outcome = _chase_one_batch(tenant_id, workspace_client_id, batch_id, questions, now)
        except Exception:
            logger.warning(
                "[line_client_dunning] batch chase failed tenant=%s client=%s batch=%s",
                tenant_id,
                workspace_client_id,
                batch_id,
                exc_info=True,
            )
            continue
        if outcome == "sent":
            sent += 1
        elif outcome == "failed":
            failed += 1
    return sent, failed


# ---------------------------------------------------------------------------
# 挂点
# ---------------------------------------------------------------------------


def run_dunning_and_sweep(now=None) -> dict:
    """同步核心(测试/一次性脚本直调)。窗口外直接 0 副作用退出——先扫后催,清扫本身
    也是写路径,不因为"只是整理"就绕过窗口闸(方案 §6.4 断言③覆盖直调场景)。"""
    from services.sales.dates import bangkok_now

    now = now or bangkok_now()
    if not _in_window(now):
        return {"closed": 0, "sent": 0, "failed": 0}
    closed = _sweep_active_questions(now)
    sent, failed = _chase_pending(now)
    if closed or sent or failed:
        logger.info("[line_client_dunning] tick closed=%d sent=%d failed=%d", closed, sent, failed)
    return {"closed": closed, "sent": sent, "failed": failed}


async def run_tick() -> int:
    """recovery tick 挂点(`services/background_loops.run_recovery_tick` 同挂点接一行):
    节流 + 窗口先判(无 DB 免费退出),核心跑 to_thread。返回本轮实际催办发送条数
    (清扫条数走日志,不占返回值——与 `proactive.run_tick` "返回发送数" 口径一致)。"""
    global _last_run
    now = time.monotonic()
    if now - _last_run < _TICK_MIN_INTERVAL_S:
        return 0
    from services.sales.dates import bangkok_now

    if not _in_window(bangkok_now()):
        _last_run = now
        return 0
    _last_run = now
    result = await asyncio.to_thread(run_dunning_and_sweep)
    return result["sent"]
