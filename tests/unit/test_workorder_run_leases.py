# -*- coding: utf-8 -*-
"""run 租约 + 死亡判据 DAL 守门(services/workorder/run_leases.py · C-1/MC2-0/MC2-A1)。

FakeCursor 录 SQL 不连库(复用 test_workorder_store 配方)。锁定:①抢约条件(空/自持/过期)
单句原子 ②心跳只续自己 owner 且刷新 updated_at ③释放只认自己 ④死亡判据谓词单一事实源,
过期支 + 孤儿宽限支缺一必红,list 与 claim 同谓词。
"""

import unittest

from services.workorder import run_leases
from tests.unit.test_workorder_store import FakeCursor


class RunLeaseTests(unittest.TestCase):
    """C-1 §3 租约 SQL 形状:条件抢占(空/自持/过期)+ 参数化 + 释放只认自己。"""

    def test_acquire_conditional_update_and_params(self):
        cur = FakeCursor([{"id": "wo-1"}])  # RETURNING 到行 = 抢到
        got = run_leases.acquire_run_lease(
            cur, tenant_id="t-1", work_order_id="wo-1", owner="run:abc", ttl_seconds=1800
        )
        self.assertTrue(got)
        sql, params = cur.calls[0]
        self.assertIn("UPDATE work_orders", sql)
        self.assertIn("run_lease_owner IS NULL", sql)
        self.assertIn("run_lease_expires_at < now()", sql)
        self.assertIn("make_interval(secs => %s)", sql)
        self.assertEqual(params, ("run:abc", 1800, "t-1", "wo-1", "run:abc"))

    def test_acquire_returns_false_when_no_row(self):
        cur = FakeCursor([None])  # 被他人未过期租约占着 → 0 行
        self.assertFalse(
            run_leases.acquire_run_lease(
                cur, tenant_id="t-1", work_order_id="wo-1", owner="run:x", ttl_seconds=60
            )
        )

    def test_release_only_matches_owner(self):
        cur = FakeCursor()
        run_leases.release_run_lease(cur, tenant_id="t-1", work_order_id="wo-1", owner="run:abc")
        sql, params = cur.calls[0]
        self.assertIn("SET run_lease_owner = NULL", sql)
        self.assertIn("AND run_lease_owner = %s", sql)
        self.assertEqual(params, ("t-1", "wo-1", "run:abc"))

    def test_renew_run_lease_is_owner_conditional_update(self):
        # MC2-A1 ④:心跳只续自己 owner 的租约(条件 UPDATE),并同步刷新 updated_at
        # (孤儿宽限判据不误咬活 run)。
        cur = FakeCursor([{"id": "wo-1"}])
        got = run_leases.renew_run_lease(
            cur, tenant_id="t-1", work_order_id="wo-1", owner="run:hb", ttl_seconds=1800
        )
        self.assertTrue(got)
        sql, params = cur.calls[0]
        self.assertIn("AND run_lease_owner = %s", sql)
        self.assertIn("updated_at = now()", sql)
        self.assertEqual(params, (1800, "t-1", "wo-1", "run:hb"))

    def test_renew_run_lease_false_when_owner_changed(self):
        cur = FakeCursor([None])
        self.assertFalse(
            run_leases.renew_run_lease(
                cur, tenant_id="t-1", work_order_id="wo-1", owner="run:old", ttl_seconds=60
            )
        )

    def test_store_reexports_lease_dal(self):
        # store.* 口径不变的直接证据:re-export 与实现是同一对象(调用方/测试 patch 不走空)。
        from services.workorder import store

        for name in (
            "acquire_run_lease",
            "renew_run_lease",
            "release_run_lease",
            "run_lease_holder",
            "list_dead_runs",
            "claim_dead_run",
        ):
            self.assertIs(getattr(store, name), getattr(run_leases, name), name)


class DeadRunReaperDalTests(unittest.TestCase):
    """MC2-0/MC2-A1 收尸 DAL:死亡判据(status + 过期租约 或 无租约孤儿过宽限)进 SQL 谓词,
    list 与 claim 共用同一谓词常量(扫描命中而抢占不认 = 孤儿永远收不走),状态词由调用方注入。"""

    def test_list_dead_runs_predicate_and_params(self):
        cur = FakeCursor(fetchall_queue=[[{"id": "wo-1", "tenant_id": "t-1"}]])
        rows = run_leases.list_dead_runs(cur, status="running", orphan_grace_seconds=1800, limit=5)
        sql, params = cur.calls[0]
        self.assertIn("WHERE status = %s", sql)
        self.assertIn(run_leases._DEAD_RUN_PREDICATE, sql)
        self.assertEqual(params, ("running", 1800, 5))
        self.assertEqual(rows, [{"id": "wo-1", "tenant_id": "t-1"}])

    def test_dead_run_predicate_covers_both_death_branches(self):
        # 判据 = 不变式「活 run 必持未过期租约」的完整表达:过期支 + 孤儿支,缺一必红。
        self.assertIn("run_lease_expires_at < now()", run_leases._DEAD_RUN_PREDICATE)
        self.assertIn("run_lease_owner IS NULL", run_leases._DEAD_RUN_PREDICATE)
        self.assertIn(
            "updated_at < now() - make_interval(secs => %s)", run_leases._DEAD_RUN_PREDICATE
        )

    def test_claim_dead_run_revalidates_death_in_single_update(self):
        cur = FakeCursor([{"id": "wo-1"}])
        got = run_leases.claim_dead_run(
            cur,
            tenant_id="t-1",
            work_order_id="wo-1",
            owner="reaper:x",
            ttl_seconds=1800,
            status="running",
            orphan_grace_seconds=1800,
        )
        self.assertTrue(got)
        sql, params = cur.calls[0]
        self.assertIn("UPDATE work_orders", sql)
        self.assertIn("AND status = %s", sql)
        self.assertIn(run_leases._DEAD_RUN_PREDICATE, sql)
        self.assertEqual(params, ("reaper:x", 1800, "t-1", "wo-1", "running", 1800))

    def test_claim_dead_run_false_when_criteria_gone(self):
        cur = FakeCursor([None])  # 别人已收 / 原单已推进 → 0 行
        self.assertFalse(
            run_leases.claim_dead_run(
                cur,
                tenant_id="t-1",
                work_order_id="wo-1",
                owner="reaper:x",
                ttl_seconds=60,
                status="running",
                orphan_grace_seconds=60,
            )
        )


if __name__ == "__main__":
    unittest.main()
