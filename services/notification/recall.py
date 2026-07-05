# -*- coding: utf-8 -*-
"""掉线召回(W4-2 · Zihao 拍板:月最多一条 · 温和文案 · 文案过目后才放)。

对象 = 用过产品(有过单据)但连续 14 天零单的绑定用户;每人每自然月最多一条
(notification_logs 去重·event_ref=YYYY-MM)。闸 agent_recall_nudge 默认关,
文案 Zihao 过目点头后才开。防线与 proactive 同款:进程内节流 + 逐户不连坐。
从没扫过单的用户不算"掉线"(那是引导层的事,不在召回射程)。
"""

from __future__ import annotations

import asyncio
import logging
import time
from datetime import date
from typing import Optional

logger = logging.getLogger(__name__)

TEMPLATE_CODE = "recall_nudge"
IDLE_DAYS = 14
_TICK_MIN_INTERVAL_S = 6 * 3600  # 无日窗口的扫描,6h 一轮足够(月最多发一条)
_last_run = 0.0

# 温和·不催账·给一个动手就能做的动作。★放量前文案须 Zihao 过目(拍板 2026-07-05)。
_COPY = {
    "th": "🧾 ช่วงนี้บิลกองอยู่หรือเปล่าคะ ถ่ายส่งมาได้เลย เดี๋ยวจัดการลงบัญชีให้ค่ะ",
    "zh": "🧾 最近票是不是攒着啦?拍张发过来,我来记账。",
    "en": "🧾 Receipts piling up? Snap one over anytime and I'll book it for you.",
    "ja": "🧾 レシートが溜まっていませんか?写真を送っていただければ記帳しておきます。",
}


def _period(today: date) -> str:
    return f"{today.year:04d}-{today.month:02d}"


def _already_sent(user_id, tenant_id, period) -> bool:
    """月度去重(与 proactive 同口径):查询失败按已发处理,花钱面宁少勿重。"""
    from core import db

    try:
        with db.get_cursor_rls(tenant_id=tenant_id, user_id=str(user_id)) as cur:
            cur.execute(
                "SELECT 1 FROM notification_logs "
                "WHERE user_id = %s AND template_code = %s AND event_ref = %s AND status = 'sent' "
                "LIMIT 1",
                (str(user_id), TEMPLATE_CODE, period),
            )
            return cur.fetchone() is not None
    except Exception:
        logger.warning("[recall] dedup check failed; skip to be safe", exc_info=True)
        return True


def _idle(user_id, tenant_id) -> bool:
    """有过单据 && 最近 14 天零单 = 掉线。查不出按不掉线(宁少勿扰)。"""
    from core import db
    from services.ocr_history import list_status as ls

    try:
        where, params = ls.owner_visibility_where(user_id, tenant_id, None, None)
        vis = " AND ".join(where)
        with db.get_cursor_rls(tenant_id=tenant_id, user_id=str(user_id)) as cur:
            cur.execute(
                f"SELECT EXISTS(SELECT 1 FROM ocr_history WHERE {vis}) AS has_any, "
                f"EXISTS(SELECT 1 FROM ocr_history WHERE {vis} "
                f"       AND created_at >= now() - make_interval(days => %s)) AS active",
                params + params + [IDLE_DAYS],
            )
            row = cur.fetchone()
        return bool(row and row["has_any"] and not row["active"])
    except Exception:
        logger.warning("[recall] idle check failed; treat as active", exc_info=True)
        return False


def send_recall_nudges(today: Optional[date] = None) -> int:
    """同步核心。返回本轮实际发送条数。"""
    from core import feature_flags
    from services.expense import line_lang
    from services.line_binding import line_reply
    from services.notification.proactive import _bound_users
    from services.notification.store import log_notification

    today = today or _bangkok_today()
    period = _period(today)
    sent = 0
    for row in _bound_users():
        try:
            uid = str(row["user_id"])
            if not feature_flags.agent_recall_enabled_for(uid):
                continue
            tid = row.get("tenant_id")
            if _already_sent(uid, tid, period):
                continue
            if not _idle(uid, tid):
                continue
            lang = line_lang.card_lang(row["line_user_id"], tid, row.get("preferred_lang") or "th")
            ok = line_reply.push_text_context(
                row["line_user_id"], _COPY.get(lang, _COPY["en"]), tenant_id=tid
            )
            log_notification(
                uid,
                tid,
                None,
                TEMPLATE_CODE,
                "recall",
                period,
                row["line_user_id"],
                "sent" if ok is not False else "failed",
            )
            if ok is not False:
                sent += 1
        except Exception:
            logger.warning("[recall] failed for one user; continue", exc_info=True)
    if sent:
        logger.info("[recall] sent=%d period=%s", sent, period)
    return sent


def _bangkok_today() -> date:
    from services.sales.dates import bangkok_now

    return bangkok_now().date()


async def run_tick() -> int:
    """recovery tick 挂点:节流后核心跑 to_thread(闸默认关 = 扫描后零发送)。"""
    global _last_run
    now = time.monotonic()
    if now - _last_run < _TICK_MIN_INTERVAL_S:
        return 0
    _last_run = now
    return await asyncio.to_thread(send_recall_nudges)
