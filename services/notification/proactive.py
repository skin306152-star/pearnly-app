# -*- coding: utf-8 -*-
"""主动触达 v1:每月一条 VAT(ภ.พ.30)申报截止提醒(PROACTIVE-NUDGE-DESIGN)。

挂 background_loops.run_recovery_tick 顺带跑(无 cron 先例)。push 是花钱面,防线:
日窗口(10–15)先判免费退出 + 进程内 1h 节流 + 闸 agent_proactive_nudge 逐用户判(默认关)
+ notification_logs 去重台账(每用户每期恰一条·重启/多 worker 不重发)。
逐用户 try/except 不连坐;发送结果 sent/failed 全落台账。文案四语确定性,不带数字
(想看汇总用户一句话问 Agent 即得),语言跟随对话(card_lang)。
"""

from __future__ import annotations

import asyncio
import logging
import time
from datetime import date
from typing import Optional

logger = logging.getLogger(__name__)

TEMPLATE_CODE = "tax_due_nudge"
WINDOW_DAYS = range(10, 16)  # 每月 10–15 日(纸质 ภ.พ.30 截止 15 日)
_TICK_MIN_INTERVAL_S = 3600  # recovery tick 30s 一跳,这里 1h 节流足够
_last_run = 0.0

_COPY = {
    "th": (
        "📅 อย่าลืมยื่นภาษีมูลค่าเพิ่ม (ภ.พ.30) ของเดือน {p} นะคะ "
        "แบบกระดาษครบกำหนดวันที่ 15 เดือนนี้ อยากดูสรุปเอกสารเดือนที่แล้ว พิมพ์ถามได้เลยค่ะ"
    ),
    "zh": "📅 别忘了申报 {p} 的增值税(ภ.พ.30),纸质申报本月 15 号截止。想看上月单据汇总,直接问我就行。",
    "en": (
        "📅 Reminder: VAT filing (PP30) for {p} — paper filing is due on the 15th this month. "
        "Ask me anytime for last month's document summary."
    ),
    "ja": "📅 {p}分の付加価値税(PP30)の申告をお忘れなく。紙申告は今月15日締切です。先月の書類サマリーはいつでもお尋ねください。",
}
# W4-2 数字版:该用户上月有单据时改发带自己数字的提醒(更有用);查不到/零单回落无数字版。
# 措辞用「เอกสาร N ใบ รวม ฿X」不说"销项"——ocr_history 合计是扫描单据口径,不冒充申报数。
_COPY_NUM = {
    "th": (
        "📅 เดือน {p} คุณมีเอกสาร {n} ใบ รวม ฿{total:,.0f} — อย่าลืมยื่น ภ.พ.30 นะคะ "
        "แบบกระดาษครบกำหนดวันที่ 15 เดือนนี้ค่ะ"
    ),
    "zh": "📅 你 {p} 有 {n} 张单据,合计 ฿{total:,.0f}——别忘了申报 ภ.พ.30,纸质本月 15 号截止。",
    "en": (
        "📅 You booked {n} docs totaling ฿{total:,.0f} in {p} — PP30 paper filing is due "
        "on the 15th this month."
    ),
    "ja": "📅 {p}は書類{n}件・合計฿{total:,.0f}でした。PP30の紙申告は今月15日締切です。お忘れなく。",
}


def _period(today: date) -> str:
    """本月 15 日要申报的期 = 上一个自然月(YYYY-MM)。"""
    y, m = (today.year, today.month - 1) if today.month > 1 else (today.year - 1, 12)
    return f"{y:04d}-{m:02d}"


def _bound_users() -> list:
    """全部 LINE 绑定用户(跨租户扫描 · 与 list_active_notification_rules_by_template
    同理由的显式 bypass:后台任务无单租户上下文,行级过滤在逐用户闸与去重)。"""
    from core import db

    with db.get_cursor() as cur:
        cur.execute(
            "SELECT lb.user_id, lb.line_user_id, u.tenant_id, u.preferred_lang "
            "FROM line_bindings lb JOIN users u ON u.id = lb.user_id"
        )
        return list(cur.fetchall())


def send_due_nudges(today: Optional[date] = None) -> int:
    """同步核心(测试/一次性脚本直调)。返回本轮实际发送条数。"""
    from core import feature_flags
    from services.expense import line_lang
    from services.line_binding import line_reply
    from services.notification import store

    today = today or store.bangkok_today()
    if today.day not in WINDOW_DAYS:
        return 0
    period = _period(today)
    sent = 0
    for row in _bound_users():
        try:
            uid = str(row["user_id"])
            if not feature_flags.agent_proactive_enabled_for(uid):
                continue
            tid = row.get("tenant_id")
            if store.already_sent(uid, tid, TEMPLATE_CODE, period):
                continue
            lang = line_lang.card_lang(row["line_user_id"], tid, row.get("preferred_lang") or "th")
            text = _copy_for(uid, tid, period, lang)
            ok = line_reply.push_text_context(row["line_user_id"], text, tenant_id=tid)
            store.log_notification(
                uid,
                tid,
                None,
                TEMPLATE_CODE,
                "tax_due",
                period,
                row["line_user_id"],
                "sent" if ok is not False else "failed",
            )
            if ok is not False:
                sent += 1
        except Exception:
            logger.warning("[proactive] nudge failed for one user; continue", exc_info=True)
    if sent:
        logger.info("[proactive] tax_due_nudge sent=%d period=%s", sent, period)
    return sent


def _copy_for(user_id, tenant_id, period, lang) -> str:
    """有上月数字发数字版,查不到/零单回落无数字版(文案层故障不许挡提醒)。"""
    from core import db
    from services.ocr_history import list_status as ls

    try:
        where, params = ls.owner_visibility_where(user_id, tenant_id, None, None)
        with db.get_cursor_rls(tenant_id=tenant_id, user_id=str(user_id)) as cur:
            cur.execute(
                f"SELECT COUNT(*) AS n, COALESCE(SUM(total_amount), 0) AS total "
                f"FROM ocr_history WHERE {' AND '.join(where)} "
                f"AND to_char(created_at AT TIME ZONE 'Asia/Bangkok', 'YYYY-MM') = %s "
                f"AND created_at >= now() - make_interval(days => 40)",
                params + [period],
            )
            row = cur.fetchone()
        if row and int(row["n"]):
            return _COPY_NUM.get(lang, _COPY_NUM["en"]).format(
                p=period, n=int(row["n"]), total=float(row["total"])
            )
    except Exception:
        logger.warning("[proactive] numbered copy failed; fallback plain", exc_info=True)
    return _COPY.get(lang, _COPY["en"]).format(p=period)


async def run_tick() -> int:
    """recovery tick 挂点:节流 + 窗口先判(无 DB 免费退出),核心跑 to_thread。"""
    from services.notification import store

    global _last_run
    now = time.monotonic()
    if now - _last_run < _TICK_MIN_INTERVAL_S:
        return 0
    if store.bangkok_today().day not in WINDOW_DAYS:
        _last_run = now
        return 0
    _last_run = now
    return await asyncio.to_thread(send_due_nudges)
