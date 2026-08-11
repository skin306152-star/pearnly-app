# -*- coding: utf-8 -*-
"""Pearnly Voice 每日上限(P3A-2 · best-effort · 多 worker 安全)。

自然语气闲聊回复不二次计费(大脑调用已扣过一次),成本由「每用户每日条数上限」控。一张小表按
LINE 用户 + 泰国时区日期计数;读 within_cap、写 bump。这是成本闸,故障按「已超额」处理
(within_cap → False):查不出今天回了几条就别再自费多回一句,否则配额表一挂 = 上限形同虚设。
代价很轻——闲聊回不了只是退回固定模板(compose 返 None,见 line_voice.try_reply),记账主路径
一步都不受影响。

键 = line_user_id(LINE 平台身份,跨租户唯一),不入 tenant 隔离(只是计数器,无业务数据)。
prod 无 alembic 钩子 → startup 经 ensure_table() 幂等建表(alembic 0044 留档)。
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

DAILY_CAP = 30

_TABLE = """
CREATE TABLE IF NOT EXISTS line_voice_quota (
    line_user_id text NOT NULL,
    day date NOT NULL,
    n int NOT NULL DEFAULT 0,
    PRIMARY KEY (line_user_id, day)
)
"""


def ensure_table() -> None:
    """幂等建 line_voice_quota(startup 调,套在 startup_ddl_lock 内 → 多 worker 不死锁)。"""
    from core import db

    with db.get_cursor(commit=True) as cur:
        cur.execute(_TABLE)


def within_cap(line_user_id, tenant_id) -> bool:
    """今日该用户语气回复条数 < DAILY_CAP → True。任何异常 → False(查不出计数就不再花钱)。"""
    if not line_user_id:
        return True
    try:
        from core import db
        from services.sales.dates import bangkok_today

        with db.get_cursor() as cur:
            cur.execute(
                "SELECT n FROM line_voice_quota WHERE line_user_id = %s AND day = %s",
                (line_user_id, bangkok_today()),
            )
            row = cur.fetchone()
        return (int(row["n"]) if row else 0) < DAILY_CAP
    except Exception as e:  # noqa: BLE001 - 查不出计数按超额,静默退回固定模板(不吞成放行)
        logger.warning("[voice quota] within_cap failed(按超额处理): %s", str(e)[:120])
        return False


def bump(line_user_id, tenant_id) -> None:
    """今日该用户计数 +1(UPSERT)。best-effort,失败只记日志。"""
    if not line_user_id:
        return
    try:
        from core import db
        from services.sales.dates import bangkok_today

        with db.get_cursor(commit=True) as cur:
            cur.execute(
                "INSERT INTO line_voice_quota (line_user_id, day, n) VALUES (%s, %s, 1) "
                "ON CONFLICT (line_user_id, day) DO UPDATE SET n = line_voice_quota.n + 1",
                (line_user_id, bangkok_today()),
            )
    except Exception as e:  # noqa: BLE001
        logger.warning("[voice quota] bump failed: %s", str(e)[:120])
