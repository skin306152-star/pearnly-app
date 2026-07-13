# -*- coding: utf-8 -*-
"""逐件检查点公用原语(C1 范式单一事实源 · MC2-A2 ①)。

classify(C1)与 reconcile 的 R3 银行流水解析共用同一套「每件独立事务 + 逐件心跳续约」:
把它从 classify 收口到这里,两处不再各写一份(避免范式漂移)。零业务逻辑,只管事务边界
与租约心跳。

item_scope:有 cursor_factory → 每件开一个独立短事务(件级写 + 事件原子落库并提交),
进程被杀只丢在飞件、已落件永久成立;提交前顺带给 run 租约续期(MC2-A1 ④ 心跳)。无
cursor_factory(内存测试 / CLI 单事务)复用 ctx.cur,由上层统一提交,行为逐字节不变。
"""

from __future__ import annotations

from contextlib import contextmanager


@contextmanager
def item_scope(ctx):
    """单件写作用域(见模块 docstring)。退出前对持约的 run 续租(易主/无约则零动作)。"""
    if ctx.cursor_factory is None:
        yield
        return
    prev = ctx.cur
    with ctx.cursor_factory() as cur:
        ctx.cur = cur
        try:
            yield
            renew_lease(ctx, cur)
        finally:
            ctx.cur = prev


def renew_lease(ctx, cur) -> None:
    """检查点心跳:只续自己 owner 的租约(条件 UPDATE,易主即不续)。租约料由 runner.advance
    放进 ctx.data['run_lease'];直调(CLI/测试)不持约则无此键,零动作。"""
    lease = ctx.data.get("run_lease") or {}
    if not lease.get("owner"):
        return
    ctx.store.renew_run_lease(
        cur,
        tenant_id=ctx.tenant_id,
        work_order_id=ctx.work_order_id,
        owner=lease["owner"],
        ttl_seconds=lease["ttl_seconds"],
    )
