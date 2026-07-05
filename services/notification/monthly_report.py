# -*- coding: utf-8 -*-
"""月报卡(W4-1 · Zihao 2026-07-05 拍板:默认开 + 一键退订)。

每月 1–3 日窗口给绑定 LINE 用户推「上月你扫了 N 张、合计 ฿X、类目 top3、环比 ±%」,
带「ดูรายละเอียด」深链按钮 + 「ปิดรับสรุป」一键退订按钮。防线与 proactive 同款:
日窗口先判 + 进程内 1h 节流 + 闸 agent_monthly_report 逐用户判 + notification_logs
去重(每用户每期恰一条)+ 逐户不连坐。上月零单的用户不发(没数字的月报是噪音)。
退订标记存 line_bindings.monthly_report_opt_out(列缺失首用自愈 ALTER)。
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
from datetime import date
from typing import Optional

logger = logging.getLogger(__name__)

TEMPLATE_CODE = "monthly_report"
WINDOW_DAYS = range(1, 4)  # 每月 1–3 日发上月报
_TICK_MIN_INTERVAL_S = 3600
_last_run = 0.0

_BKK_MONTH = "to_char(created_at AT TIME ZONE 'Asia/Bangkok', 'YYYY-MM')"

_COPY = {
    "th": "📊 สรุปเดือน {p}: {n} ใบ รวม ฿{total:,.0f}{delta} หมวดยอดนิยม: {cats}",
    "zh": "📊 {p} 月报:{n} 张单据,合计 ฿{total:,.0f}{delta}。常用类目:{cats}",
    "en": "📊 {p} recap: {n} docs, ฿{total:,.0f} total{delta}. Top categories: {cats}",
    "ja": "📊 {p}のまとめ:{n}件・合計฿{total:,.0f}{delta}。上位カテゴリ:{cats}",
}
_DELTA = {
    "th": " ({sign}{pct:.0f}% จากเดือนก่อน)",
    "zh": "(比上月{sign}{pct:.0f}%)",
    "en": " ({sign}{pct:.0f}% vs prior month)",
    "ja": "(前月比{sign}{pct:.0f}%)",
}
_BTN_DETAIL = {"th": "ดูรายละเอียด", "zh": "看明细", "en": "Details", "ja": "詳細を見る"}
_BTN_UNSUB = {"th": "ปิดรับสรุป", "zh": "退订月报", "en": "Unsubscribe", "ja": "配信停止"}
_UNSUB_OK = {
    "th": "ปิดรับสรุปรายเดือนแล้วค่ะ ถ้าอยากเปิดใหม่ทักมาบอกได้เลยนะคะ",
    "zh": "已退订月报。想恢复的话随时跟我说一声。",
    "en": "Monthly recap turned off. Tell me anytime if you want it back.",
    "ja": "月次まとめの配信を停止しました。再開したいときは声をかけてください。",
}


def _t(table: dict, lang: str) -> str:
    return table.get(lang, table["en"])


def _period_back(today: date, n: int) -> str:
    """今天(曼谷)往回数 n 个自然月的 'YYYY-MM'。月序号直接减,免跨年分支/魔法数。"""
    idx = today.year * 12 + (today.month - 1) - n
    return f"{idx // 12:04d}-{idx % 12 + 1:02d}"


def _month_stats(user_id, tenant_id, period, prior_period) -> Optional[dict]:
    """上月单量/合计/类目 top3 + 上上月合计(环比)。可见性与列表同一事实源。"""
    from core import db
    from services.ocr_history import list_status as ls

    try:
        where, params = ls.owner_visibility_where(user_id, tenant_id, None, None)
        vis = " AND ".join(where)
        with db.get_cursor_rls(tenant_id=tenant_id, user_id=str(user_id)) as cur:
            cur.execute(
                f"SELECT COUNT(*) FILTER (WHERE {_BKK_MONTH} = %s) AS n, "
                f"COALESCE(SUM(total_amount) FILTER (WHERE {_BKK_MONTH} = %s), 0) AS total, "
                f"COALESCE(SUM(total_amount) FILTER (WHERE {_BKK_MONTH} = %s), 0) AS prior "
                f"FROM ocr_history WHERE {vis} "
                f"AND created_at >= now() - make_interval(days => 70)",
                [period, period, prior_period] + params,
            )
            row = cur.fetchone()
            out = {"n": int(row["n"]), "total": float(row["total"]), "prior": float(row["prior"])}
            if not out["n"]:
                return out
            cur.execute(
                f"SELECT category_tag, COUNT(*) AS c FROM ocr_history "
                f"WHERE {vis} AND {_BKK_MONTH} = %s AND COALESCE(category_tag, '') <> '' "
                f"GROUP BY category_tag ORDER BY c DESC LIMIT 3",
                params + [period],
            )
            out["cats"] = [r["category_tag"] for r in cur.fetchall()]
            return out
    except Exception:
        logger.warning("[monthly_report] stats failed", exc_info=True)
        return None


def _ensure_opt_out_column() -> None:
    from core import db

    with db.get_cursor(commit=True) as cur:
        cur.execute(
            "ALTER TABLE line_bindings "
            "ADD COLUMN IF NOT EXISTS monthly_report_opt_out boolean NOT NULL DEFAULT false"
        )


def _with_heal(fn):
    """退订列缺失(prod 无 alembic 钩子)→ 首用 ALTER 自愈重试一次;其余异常上抛。"""
    try:
        return fn()
    except Exception as e:
        if "monthly_report_opt_out" not in str(e):
            raise
        _ensure_opt_out_column()
        return fn()


def _recipients() -> list:
    """绑定用户 + 退订标记(跨租户扫描·同 proactive._bound_users 的显式 bypass 理由)。"""
    from core import db

    def _run():
        with db.get_cursor() as cur:
            cur.execute(
                "SELECT lb.user_id, lb.line_user_id, lb.monthly_report_opt_out, "
                "u.tenant_id, u.preferred_lang "
                "FROM line_bindings lb JOIN users u ON u.id = lb.user_id"
            )
            return list(cur.fetchall())

    return _with_heal(_run)


def set_opt_out(line_user_id, value: bool) -> bool:
    """写退订标记。返回是否命中绑定行。列缺失首用自愈。"""
    from core import db

    def _run():
        with db.get_cursor(commit=True) as cur:
            cur.execute(
                "UPDATE line_bindings SET monthly_report_opt_out = %s WHERE line_user_id = %s",
                (bool(value), line_user_id),
            )
            return cur.rowcount > 0

    return _with_heal(_run)


def _message(stats: dict, period: str, lang: str) -> dict:
    from services.line_binding import line_card_sections, line_postback

    delta = ""
    if stats["prior"] > 0:
        pct = (stats["total"] - stats["prior"]) / stats["prior"] * 100
        delta = _t(_DELTA, lang).format(sign="+" if pct >= 0 else "-", pct=abs(pct))
    cats = ", ".join(stats.get("cats") or []) or "-"
    body = _t(_COPY, lang).format(
        p=period, n=stats["n"], total=stats["total"], delta=delta, cats=cats
    )
    uri = line_card_sections.liff_link(
        os.getenv("LINE_LIFF_ID", "").strip(), "https://pearnly.com/home", ""
    )
    return {
        "type": "template",
        "altText": body[:160] or "Pearnly",
        "template": {
            "type": "buttons",
            "text": body[:160],
            "actions": [
                {"type": "uri", "label": _t(_BTN_DETAIL, lang)[:20], "uri": uri},
                {
                    "type": "postback",
                    "label": _t(_BTN_UNSUB, lang)[:20],
                    "data": line_postback.monthly_report_unsub_data(),
                },
            ],
        },
    }


def send_monthly_reports(today: Optional[date] = None) -> int:
    """同步核心(测试/一次性脚本直调)。返回本轮实际发送条数。"""
    from core import feature_flags
    from services.expense import line_lang
    from services.line_binding import line_reply
    from services.notification import store

    today = today or store.bangkok_today()
    if today.day not in WINDOW_DAYS:
        return 0
    period = _period_back(today, 1)
    prior = _period_back(today, 2)
    sent = 0
    for row in _recipients():
        try:
            uid = str(row["user_id"])
            if row.get("monthly_report_opt_out"):
                continue
            if not feature_flags.agent_monthly_report_enabled_for(uid):
                continue
            tid = row.get("tenant_id")
            if store.already_sent(uid, tid, TEMPLATE_CODE, period):
                continue
            stats = _month_stats(uid, tid, period, prior)
            if not stats or not stats["n"]:  # 上月零单:没数字的月报是噪音,不发
                continue
            lang = line_lang.card_lang(row["line_user_id"], tid, row.get("preferred_lang") or "th")
            ok = line_reply.push_messages_context(
                row["line_user_id"], [_message(stats, period, lang)], tenant_id=tid
            )
            store.log_notification(
                uid,
                tid,
                None,
                TEMPLATE_CODE,
                "monthly_report",
                period,
                row["line_user_id"],
                "sent" if ok is not False else "failed",
            )
            if ok is not False:
                sent += 1
        except Exception:
            logger.warning("[monthly_report] failed for one user; continue", exc_info=True)
    if sent:
        logger.info("[monthly_report] sent=%d period=%s", sent, period)
    return sent


def handle_unsub(bound_user, reply_token, lang) -> None:
    """退订按钮回调:置标记 + 四语确认。幂等(重复点同样回执)。"""
    from services.line_binding import line_reply

    luid = bound_user.get("line_user_id") or ""
    tid = str(bound_user["tenant_id"]) if bound_user.get("tenant_id") else None
    try:
        set_opt_out(luid, True)
    except Exception:
        logger.warning("[monthly_report] opt-out write failed", exc_info=True)
    line_reply.reply_text_context(
        reply_token, _t(_UNSUB_OK, lang), line_user_id=luid, tenant_id=tid
    )


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
    return await asyncio.to_thread(send_monthly_reports)
