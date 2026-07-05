# -*- coding: utf-8 -*-
"""LINE 获客漏斗打点(W0 观测)—— 加好友→绑定→用起来 三级转化的地基。

follow 事件此前完全没有落库,「多少人加了好友却没绑定」量不出来;绑定与使用侧
已有数据(line_bindings.bound_at 换绑不刷首绑时间、agent_turn_logs.intent),
所以这里只补 follow 一级 + 一个跨表聚合口。(line_user_id, event) 主键=每人每级
只记首次,重复 follow 不刷时间。

建表照 line_pending_intents 范式(prod 无 alembic 钩子 → 首用 ensure 幂等自愈);
无 tenant 列(follow 发生在绑定前,天然无租户)。mark 全程 best-effort:打点绝不挡主路径。
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

_TABLE = """
CREATE TABLE IF NOT EXISTS line_funnel_events (
    line_user_id text NOT NULL,
    event text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (line_user_id, event)
)
"""


def ensure_table() -> None:
    """幂等建 line_funnel_events(首用自愈调,alembic 0052 留档)。"""
    from core import db

    with db.get_cursor(commit=True) as cur:
        cur.execute(_TABLE)


def _with_heal(fn):
    try:
        return fn()
    except Exception as e:
        if "line_funnel_events" not in str(e):
            raise
        ensure_table()
        return fn()


def mark(event: str, line_user_id) -> None:
    """记一级漏斗事件(首次为准,重复无声跳过)。任何故障只记日志。"""
    if not line_user_id:
        return
    from core import db

    def _run():
        with db.get_cursor(commit=True) as cur:
            cur.execute(
                "INSERT INTO line_funnel_events (line_user_id, event) "
                "VALUES (%s, %s) ON CONFLICT (line_user_id, event) DO NOTHING",
                (str(line_user_id), str(event)),
            )

    try:
        _with_heal(_run)
    except Exception:
        logger.warning("[line_funnel] mark %s failed", event, exc_info=True)


def funnel_stats(days: int = 7) -> dict:
    """窗口内 加好友→绑定→用过 Agent→记过账 四级计数(超管看板口,只读跨租户)。

    binds 取 line_bindings.bound_at(upsert 不刷首绑时间=首绑口径);used/recorded 取
    agent_turn_logs 窗口内活跃(v1 活跃口径,非严格首次转化——够指导迭代,先别过度工程)。
    """
    from core import db

    with db.get_cursor() as cur:
        cur.execute(
            "SELECT count(*) AS n FROM line_funnel_events "
            "WHERE event = 'follow' AND created_at > now() - make_interval(days => %s)",
            (days,),
        )
        follows = int(cur.fetchone()["n"])
        cur.execute(
            "SELECT count(*) AS n FROM line_bindings "
            "WHERE bound_at > now() - make_interval(days => %s)",
            (days,),
        )
        binds = int(cur.fetchone()["n"])
        cur.execute(
            "SELECT count(DISTINCT line_user_id) AS used, "
            "       count(DISTINCT line_user_id) FILTER (WHERE intent = 'record') AS recorded "
            "FROM agent_turn_logs "
            "WHERE created_at > now() - make_interval(days => %s)",
            (days,),
        )
        row = cur.fetchone()
    return {
        "days": days,
        "follows": follows,
        "binds": binds,
        "agent_used": int(row["used"] or 0),
        "recorded": int(row["recorded"] or 0),
    }
