# -*- coding: utf-8 -*-
"""RD(泰国税务局)校验日限(rd_daily_usage)· 数据访问层

从 db.py 抽出(REFACTOR-B2 · 纯搬家 · 0 逻辑改)。
Free 套餐每天调 RD 校验的次数限额计数(按当天聚合)。
db.py 文件尾 re-export 回本命名空间 · 所有 `db.xxx()` 调用点不变。
"""

import logging

import db

logger = logging.getLogger(__name__)


def get_rd_daily_usage(user_id: str) -> int:
    """返回今天用户已调 RD 的次数"""
    try:
        with db.get_cursor() as cur:
            cur.execute(
                """
                SELECT count FROM rd_daily_usage
                WHERE user_id = %s AND day = CURRENT_DATE
            """,
                (user_id,),
            )
            r = cur.fetchone()
            return int(r["count"]) if r else 0
    except Exception as e:
        logger.error(f"get_rd_daily_usage failed: {e}")
        return 0


def increment_rd_daily_usage(user_id: str, n: int = 1) -> int:
    """RD 调用成功后 +1 · 自动按当天聚合"""
    try:
        with db.get_cursor(commit=True) as cur:
            cur.execute(
                """
                INSERT INTO rd_daily_usage (user_id, day, count)
                VALUES (%s, CURRENT_DATE, %s)
                ON CONFLICT (user_id, day) DO UPDATE
                SET count = rd_daily_usage.count + EXCLUDED.count
                RETURNING count
            """,
                (user_id, n),
            )
            r = cur.fetchone()
            return int(r["count"]) if r else n
    except Exception as e:
        logger.error(f"increment_rd_daily_usage failed: {e}")
        return 0
