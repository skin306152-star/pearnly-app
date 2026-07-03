# -*- coding: utf-8 -*-
"""LINE webhook 事件去重(webhookEventId 幂等)。

LINE 在投递失败/超时后会重投同一事件(redelivery),而文本直录没有消息级幂等 →
同一句「กาแฟ 50」可能被记两笔。每个事件带全局唯一 webhookEventId → 落一张小表,
INSERT ON CONFLICT DO NOTHING 原子抢占:插不进 = 处理过,整个事件跳过。

口径 = at-most-once:钱路上重复入账比丢一条消息伤害大(没回复用户会重发,双记账
用户不知道)。无 event_id 的老格式放行;表故障 fail-open 放行——去重是增强不是闸,
绝不许挡正常消息。prod 无 alembic 钩子 → ensure_table 启动幂等建(alembic 0046 留档)。
"""

from __future__ import annotations

import logging
import random

logger = logging.getLogger(__name__)

TTL_HOURS = 48  # LINE redelivery 窗口远短于此;采样清老行,表恒小
_CLEAN_PROB = 0.02  # 清理采样率:webhook 最热路径,别每个事件都为"几乎总删空"的 DELETE 买单

_TABLE = """
CREATE TABLE IF NOT EXISTS line_webhook_events (
    event_id text PRIMARY KEY,
    received_at timestamptz NOT NULL DEFAULT now()
)
"""


def ensure_table() -> None:
    """幂等建 line_webhook_events(startup 调)。非租户表(webhook 早于身份解析)→
    RLS 显式 DISABLE 钉死,防托管库给新表自动开 RLS 裸成 deny-all 孤儿。"""
    from core import db

    with db.get_cursor(commit=True) as cur:
        cur.execute(_TABLE)
        cur.execute("ALTER TABLE line_webhook_events DISABLE ROW LEVEL SECURITY")


def seen_before(event_id) -> bool:
    """该事件是否已处理过(原子:INSERT 抢占,插不进=重投)。故障/无 id → False 放行。"""
    eid = str(event_id or "").strip()
    if not eid:
        return False  # 老格式无 id:放行(宁可重复处理,不许误吞)
    try:
        from core import db

        with db.get_cursor(commit=True) as cur:
            cur.execute(
                "INSERT INTO line_webhook_events (event_id) VALUES (%s) "
                "ON CONFLICT (event_id) DO NOTHING",
                (eid,),
            )
            fresh = cur.rowcount > 0
            if fresh and random.random() < _CLEAN_PROB:
                cur.execute(
                    "DELETE FROM line_webhook_events "
                    "WHERE received_at < now() - make_interval(hours => %s)",
                    (TTL_HOURS,),
                )
            return not fresh
    except Exception:
        logger.warning("[line webhook] dedup store failed; processing anyway", exc_info=True)
        return False
