# -*- coding: utf-8 -*-
"""
MR.ERP 会话跨进程串行锁(2026-05-25)

根因(已实测坐实):mrerp4sme 是老 PHP · 一个账号只允许一个活动会话 ·
第二个登录会把第一个踢下线 → 被踢的那次报 ERR_AUTH。生产 uvicorn `--workers 2` ·
两个 worker 同时推送同一 MR.ERP 账号 → 随机一个被踢 → "几乎都失败"。

进程内 threading.Lock 解不了(两个 worker 是独立进程)· 必须跨进程锁。
用 Postgres session 级 advisory lock(pg_advisory_lock)· 按 MR.ERP 账号
(login_url|username)取键 · 不同账号互不阻塞 · 同账号串行。

崩溃安全:session 级 advisory lock 在持锁连接断开时(含进程崩溃)自动释放 ·
不会留死锁。

降级:DATABASE_URL 未配 / 取锁失败 → 记日志后**放行**(可用性 > 偶发互踢)·
单测无 DB 时天然 no-op。
"""

from __future__ import annotations

import time
import hashlib
import logging
from contextlib import contextmanager

logger = logging.getLogger(__name__)

# advisory lock 命名空间(随手取的常量 · 避免和别处 advisory lock 撞 key 空间)
_LOCK_NAMESPACE = 0x4D524552  # 'MRER'


def _account_lock_key(account_key: str) -> int:
    """把账号串映射成 pg advisory lock 用的有符号 64-bit int。"""
    digest = hashlib.sha256(account_key.encode("utf-8")).digest()
    # 取前 4 字节作低位 · 拼上命名空间高位 · 再压到 signed 64-bit
    low = int.from_bytes(digest[:4], "big")
    key = (_LOCK_NAMESPACE << 32) | low
    # 转 signed 64-bit(pg bigint 范围)
    if key >= 2**63:
        key -= 2**64
    return key


@contextmanager
def mrerp_session_lock(account_key: str, timeout_sec: float = 180.0, poll_sec: float = 1.0):
    """
    对同一 MR.ERP 账号串行化浏览器会话。

    account_key: 唯一标识一个 MR.ERP 账号 · 典型 = f"{login_url}|{username}"。
    timeout_sec: 最长等待持锁时间 · 超时仍放行(记 warning · 不阻塞业务)。

    实现:用一条专用连接,在**一个保持打开的事务**里取 `pg_advisory_xact_lock`。
    关键 · 为何用 xact 锁而非 session 锁:Supabase Pooler 若是 transaction-pooling,
    每条 autocommit 语句可能落到不同后端 → session 级 pg_advisory_lock 会失效且泄漏。
    保持事务打开会让 PgBouncer 把后端 pin 到本连接,xact 锁在两种 pooling 下都真正互斥;
    退出时 rollback 结束事务 → 自动释放锁 + 解 pin(崩溃断连也自动释放)。
    """
    from core import db

    key = _account_lock_key(account_key)
    conn = None
    locked = False
    prev_autocommit = None
    t0 = time.time()
    try:
        try:
            conn = db.get_pool().getconn()
            prev_autocommit = conn.autocommit
            # 必须事务式(非 autocommit):让事务保持打开 → 后端被 pin → xact 锁跨语句有效
            conn.autocommit = False
        except Exception as e:
            # 没 DB / 池建不起来 → 降级放行(单测、本地无 DB)
            logger.debug("[mrerp-lock] 无法取锁连接 · 降级放行: %s", e)
            yield False
            return

        # 在同一个打开的事务里轮询 try-lock(失败不结束事务 · 不释放任何东西)
        while True:
            try:
                with conn.cursor() as cur:
                    cur.execute("SELECT pg_try_advisory_xact_lock(%s)", (key,))
                    row = cur.fetchone()
                    locked = bool(row[0]) if row else False
            except Exception as e:
                logger.warning("[mrerp-lock] try-lock 异常 · 降级放行: %s", e)
                try:
                    conn.rollback()
                except Exception:
                    pass
                yield False
                return

            if locked:
                waited = time.time() - t0
                if waited > 0.5:
                    logger.info("[mrerp-lock] 取锁成功 key=%s 等待=%.1fs", key, waited)
                break

            if time.time() - t0 >= timeout_sec:
                logger.warning(
                    "[mrerp-lock] 等待 %.0fs 仍未取到锁 key=%s · 降级放行(可能与他会话并发)",
                    timeout_sec,
                    key,
                )
                try:
                    conn.rollback()  # 结束空事务 · 解 pin(降级期不占着后端)
                except Exception:
                    pass
                yield False
                return

            time.sleep(poll_sec)

        # 持锁期间事务保持打开(调用方在此跑 Playwright)· 退出 finally 才 rollback 放锁
        yield True

    finally:
        if conn is not None:
            try:
                conn.rollback()  # 结束事务 → 释放 xact 锁
            except Exception as e:
                logger.warning("[mrerp-lock] rollback 释放锁异常(连接归还后会自动释放): %s", e)
            try:
                if prev_autocommit is not None:
                    conn.autocommit = prev_autocommit
            except Exception:
                pass
            try:
                db.get_pool().putconn(conn)
            except Exception:
                pass
