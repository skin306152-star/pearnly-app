# -*- coding: utf-8 -*-
"""Serialize MR.ERP logins with a transaction-pinned PostgreSQL advisory lock.

Cloud Run must acquire the lock before opening a session. Legacy local execution
retains the existing no-database fallback.
"""

from __future__ import annotations

import time
import os
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


class MrerpSessionLockUnavailable(RuntimeError):
    """No browser session may start without the required distributed lock."""


def cloud_lock_required() -> bool:
    return os.environ.get("PEARNLY_RUNTIME_ROLE") in {"web", "worker"}


def _require_cloud_lock(reason: str) -> None:
    if cloud_lock_required():
        raise MrerpSessionLockUnavailable(f"mrerp_session_lock_{reason}")


@contextmanager
def mrerp_session_lock(account_key: str, timeout_sec: float = 180.0, poll_sec: float = 1.0):
    """
    对同一 MR.ERP 账号串行化浏览器会话。

    account_key: 唯一标识一个 MR.ERP 账号 · 典型 = f"{login_url}|{username}"。
    timeout_sec: 最长等待持锁时间；Cloud Run 超时拒绝执行，旧本机模式保留降级。

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
            _require_cloud_lock("unavailable")
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
                _require_cloud_lock("query_failed")
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
                _require_cloud_lock("timeout")
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


def dms_booking_scope_key(endpoint) -> str:
    """DMS 建单共享锁键:按规范化服务地址收敛,不带账号凭据。

    URL 规范化:去尾斜杠、剥掉 /index.php —— full index.php URL 与 /dms/ base URL
    归一成同一键。当前 DMS 登录适配器不读取 comidyear/seldb,无法从 endpoint
    配置可靠推导账套 id;按服务地址保守串行,避免同一服务上的共享账套漏锁。
    """
    cfg = endpoint.get("config") or {}
    url = (
        str(cfg.get("system_url") or "https://www.mrerp4sme.com/dms/index.php").strip().rstrip("/")
    )
    if url.lower().endswith("/index.php"):
        url = url[: -len("/index.php")]
    return url


@contextmanager
def mrerp_booking_lock(endpoint, timeout_sec: float = 180.0, poll_sec: float = 1.0):
    """对同一 DMS 账套(非同一账号)串行化「取号→提交」临界区。

    同账套多个销售账号并发建单,autonum 取号可能撞到同一单号 → DMS 唯一约束 + 重复号
    重试是最后安全网,但跨账号互斥能直接避免无谓重试。锁按整个账套(不加 branch_id):
    不同分店的 autonum 仍可能撞全局单号。锁基础设施失败 → 降级放行(语义同
    mrerp_session_lock)。
    """
    with mrerp_session_lock(
        f"booking|{dms_booking_scope_key(endpoint)}",
        timeout_sec=timeout_sec,
        poll_sec=poll_sec,
    ) as got:
        yield got
