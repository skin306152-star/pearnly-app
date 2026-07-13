# -*- coding: utf-8 -*-
"""逐件检查点公用原语守门(services/workorder/steps/checkpoint.py · MC2-A2 ①)。

脱库:验证 item_scope 的两种事务边界 + 心跳续约只续持约 run。classify 与 reconcile 的 R3
共用这一份,范式不再各写。
"""

from __future__ import annotations

import unittest
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from services.workorder.steps import checkpoint


class _RecordStore:
    def __init__(self):
        self.renewals = []

    def renew_run_lease(self, cur, *, tenant_id, work_order_id, owner, ttl_seconds):
        self.renewals.append({"cur": cur, "owner": owner, "ttl_seconds": ttl_seconds})
        return True


@dataclass
class _Ctx:
    cur: Any = None
    tenant_id: str = "t-1"
    work_order_id: str = "wo-1"
    store: Any = None
    data: dict = field(default_factory=dict)
    cursor_factory: Optional[Callable] = None


class _FakeCursor:
    def __init__(self):
        self.closed = False

    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.closed = True
        return False


class ItemScopeTests(unittest.TestCase):
    def test_no_factory_reuses_ctx_cur_no_renew(self):
        store = _RecordStore()
        ctx = _Ctx(
            cur="shared", store=store, data={"run_lease": {"owner": "run:x", "ttl_seconds": 60}}
        )
        with checkpoint.item_scope(ctx):
            self.assertEqual(ctx.cur, "shared")  # 复用,不换游标
        self.assertEqual(ctx.cur, "shared")
        self.assertEqual(store.renewals, [])  # 无独立事务 = 无心跳

    def test_factory_opens_subtxn_binds_and_restores_cur(self):
        store = _RecordStore()
        opened, closed = [], []

        @contextmanager
        def factory():
            cur = _FakeCursor()
            opened.append(cur)
            try:
                yield cur
            finally:
                closed.append(cur)

        ctx = _Ctx(
            cur="outer",
            store=store,
            cursor_factory=factory,
            data={"run_lease": {"owner": "run:x", "ttl_seconds": 60}},
        )
        with checkpoint.item_scope(ctx):
            self.assertIs(ctx.cur, opened[0])  # 块内绑到子事务游标
        self.assertEqual(ctx.cur, "outer")  # 退出还原
        self.assertEqual(closed, opened)  # 子事务提交/关闭
        self.assertEqual(len(store.renewals), 1)  # 提交前续租一次
        self.assertEqual(store.renewals[0]["owner"], "run:x")

    def test_renew_noop_without_lease_owner(self):
        store = _RecordStore()
        ctx = _Ctx(cur="c", store=store, data={})  # 无 run_lease(直调/CLI)
        checkpoint.renew_lease(ctx, "c")
        self.assertEqual(store.renewals, [])


if __name__ == "__main__":
    unittest.main()
