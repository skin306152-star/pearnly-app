# -*- coding: utf-8 -*-
"""
services/usage/store.py · 用户活动 / 用量计数 / 历史清理(REFACTOR-B2)

从 db.py 抽出的「用户活动跟踪」域:
- update_last_login            登录时刷 users.last_login_at(spec 01 后台触发)
- increment_user_monthly_usage 识别后累加 used_this_month + 跨月重置(老配额 · credits 模式
                                改造前的接口 · 仍由 charge_ocr 调用)
- cleanup_expired_history      按老 plan(free/plus/pro)分档删过期 ocr_history。⚠️ **当前是
                                半死码**:整顿期间已把套餐迁到 credits 单一模式(STATE 头
                                「计费迁移收尾」),users.plan 已不再有 free/plus/pro 值,
                                此函数运行时删 0 行。仍保留以防有遗留 plan='free' 记录,B3
                                Alembic 化时再决定真删。

范式(ADR-007):import db + 运行时 db.get_cursor()。
"""

from __future__ import annotations

import logging

import db

logger = logging.getLogger(__name__)


def update_last_login(user_id: str):
    try:
        with db.get_cursor(commit=True) as cur:
            cur.execute("UPDATE users SET last_login_at = NOW() WHERE id = %s", (user_id,))
    except Exception as e:
        logger.error(f"更新登录时间失败: {e}")


def increment_user_monthly_usage(user_id: str, n: int = 1) -> int:
    """Plus 用户识别后累加本月用量。
    跨月(last_usage_month != 本月)→ 重置为 n;否则 += n。返回最新 used_this_month。
    """
    try:
        with db.get_cursor(commit=True) as cur:
            cur.execute(
                """
                UPDATE users SET
                    used_this_month = CASE
                        WHEN last_usage_month IS NULL
                          OR last_usage_month < DATE_TRUNC('month', NOW())::date
                        THEN %s
                        ELSE COALESCE(used_this_month, 0) + %s
                    END,
                    last_usage_month = DATE_TRUNC('month', NOW())::date
                WHERE id = %s
                RETURNING used_this_month
            """,
                (n, n, user_id),
            )
            row = cur.fetchone()
            return row["used_this_month"] if row else 0
    except Exception as e:
        logger.error(f"更新用户月用量失败 (user_id={user_id}): {e}")
        return 0


def cleanup_expired_history(free_days: int = 7, plus_days: int = 90, pro_days: int = 365) -> int:
    """按 plan 删过期历史 · 返回删除条数。
    ⚠️ 老 plan 模式遗留(整顿后 credits 单档),实际删 0 行;留作 B3 Alembic 化时统一处理。
    """
    total = 0
    try:
        with db.get_cursor(commit=True) as cur:
            cur.execute(
                """
                DELETE FROM ocr_history
                WHERE user_id IN (SELECT id FROM users WHERE plan = 'free')
                  AND created_at < NOW() - (%s || ' days')::interval
            """,
                (str(free_days),),
            )
            total += cur.rowcount
            cur.execute(
                """
                DELETE FROM ocr_history
                WHERE user_id IN (SELECT id FROM users WHERE plan = 'plus')
                  AND created_at < NOW() - (%s || ' days')::interval
            """,
                (str(plus_days),),
            )
            total += cur.rowcount
            cur.execute(
                """
                DELETE FROM ocr_history
                WHERE user_id IN (SELECT id FROM users WHERE plan = 'pro')
                  AND created_at < NOW() - (%s || ' days')::interval
            """,
                (str(pro_days),),
            )
            total += cur.rowcount
        return total
    except Exception as e:
        logger.error(f"cleanup_expired_history failed: {e}")
        return 0
