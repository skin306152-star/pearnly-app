# -*- coding: utf-8 -*-
"""逐件检查点公用原语(C1 范式单一事实源 · MC2-A2 ①)。

classify(C1)与 reconcile 的 R3 银行流水解析共用同一套「每件独立事务 + 逐件心跳续约」:
把它从 classify 收口到这里,两处不再各写一份(避免范式漂移)。零业务逻辑,只管事务边界
与租约心跳。

item_scope:有 cursor_factory → 每件开一个独立短事务(件级写 + 事件原子落库并提交),
进程被杀只丢在飞件、已落件永久成立。件事务提交后再心跳续约(R1):心跳跑在自己的短事务
里,单次失败(DB 抖动)只记日志、绝不回滚已提交的检查点、也绝不拖垮跑批——靠 TTL 裕量
下一拍再续。无 cursor_factory(内存测试 / CLI 单事务)复用 ctx.cur,由上层统一提交。
"""

from __future__ import annotations

import logging
import time
from contextlib import contextmanager

logger = logging.getLogger(__name__)


@contextmanager
def item_scope(ctx):
    """单件写作用域(见模块 docstring)。件事务提交后对持约的 run 续租(易主/无约则零动作)。"""
    if ctx.cursor_factory is None:
        yield
        return
    prev = ctx.cur
    with ctx.cursor_factory() as cur:
        ctx.cur = cur
        try:
            yield
        finally:
            ctx.cur = prev
    # 心跳在件事务【提交之后】、于独立短事务里做:与检查点解耦,心跳失败不回滚已落件。
    renew_lease(ctx)


def renew_lease(ctx) -> None:
    """检查点心跳:只续自己 owner 的租约(条件 UPDATE,易主即不续)。租约料由 runner.advance
    放进 ctx.data['run_lease'];直调(CLI/测试)不持约则无此键,零动作。

    R1:按 heartbeat_seconds 节流(未配 = 每件都续,保旧行为);单次续租失败只记日志、绝不
    抛出——跑批不因一次 DB 抖动被心跳拖死,靠 TTL 裕量下一拍再续。"""
    lease = ctx.data.get("run_lease") or {}
    owner = lease.get("owner")
    if not owner:
        return
    if not _heartbeat_due(lease):
        return
    try:
        _renew(ctx, owner, lease)
        lease["_last_heartbeat"] = time.monotonic()
    except Exception:  # noqa: BLE001 - 心跳单次失败不杀跑批(见 docstring)
        logger.warning("[workorder-checkpoint] lease heartbeat skipped", exc_info=True)


def _heartbeat_due(lease: dict) -> bool:
    """到续租节拍没有:heartbeat_seconds 未配/≤0 → 每次检查点都续(旧行为);配了则距上次
    ≥ 间隔才续(短 TTL 下少打无谓 UPDATE,又保证 ≥3 次心跳裕量)。"""
    interval = lease.get("heartbeat_seconds") or 0
    if interval <= 0:
        return True
    last = lease.get("_last_heartbeat")
    return last is None or (time.monotonic() - last) >= interval


def _renew(ctx, owner: str, lease: dict) -> None:
    """续租一次。有 cursor_factory → 自开独立短事务(与件检查点解耦,失败不牵连已落件);
    无(直调/CLI 单事务)→ 复用 ctx.cur。"""
    if ctx.cursor_factory is None:
        ctx.store.renew_run_lease(
            ctx.cur,
            tenant_id=ctx.tenant_id,
            work_order_id=ctx.work_order_id,
            owner=owner,
            ttl_seconds=lease["ttl_seconds"],
        )
        return
    with ctx.cursor_factory() as cur:
        ctx.store.renew_run_lease(
            cur,
            tenant_id=ctx.tenant_id,
            work_order_id=ctx.work_order_id,
            owner=owner,
            ttl_seconds=lease["ttl_seconds"],
        )
