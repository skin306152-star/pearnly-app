# -*- coding: utf-8 -*-
"""费用科目预设播种的并发防呆守门(services/purchase/categories.seed_presets)。

线上事故:两个并发首读各自看到空树 → 各种一棵预设树 → 科目重复一倍。修复=先取
事务级 advisory lock(按 tenant+ws)串行化播种。本测试锁定不回归:
  1. advisory lock 在 _count 检查之前发出(否则起不到串行作用)。
  2. 已非空(_count>0)时直接返回,不插任何行(幂等)。
  3. 空树时只种一棵完整树(16 个大类)。
"""

import unittest

from services.purchase import categories


class FakeCursor:
    """记录 (sql, params);count 查询返回预设值,INSERT 返回自增 id 行。"""

    def __init__(self, count_value: int):
        self.count_value = count_value
        self.calls: list[tuple] = []
        self._last = None
        self._idseq = 0

    def execute(self, sql, params=None):
        self.calls.append((sql, params))
        s = sql.lower()
        if "count(*)" in s:
            self._last = {"n": self.count_value}
        elif "insert into expense_categories" in s:
            self._idseq += 1
            self._last = {
                "id": f"id{self._idseq}",
                "parent_id": params[2],
                "name": params[3],
                "is_active": True,
                "sort": params[4],
            }
        else:
            self._last = None

    def fetchone(self):
        return self._last

    # 便捷过滤
    def _idx(self, needle):
        return next(i for i, (sql, _) in enumerate(self.calls) if needle in sql.lower())

    def parent_inserts(self):
        return [
            p
            for sql, p in self.calls
            if "insert into expense_categories" in sql.lower() and p[2] is None
        ]

    def any_insert(self):
        return any("insert into expense_categories" in sql.lower() for sql, _ in self.calls)


class SeedGuardTests(unittest.TestCase):
    def test_lock_taken_before_count_check(self):
        cur = FakeCursor(count_value=0)
        categories.seed_presets(cur, tenant_id="t1", workspace_client_id=6)
        self.assertLess(cur._idx("pg_advisory_xact_lock"), cur._idx("count(*)"))

    def test_no_insert_when_already_seeded(self):
        cur = FakeCursor(count_value=89)  # 已有一棵树
        categories.seed_presets(cur, tenant_id="t1", workspace_client_id=6)
        self.assertFalse(cur.any_insert())
        # 锁仍先取(并发第二个请求靠它排队后才发现已非空)
        self.assertTrue(any("pg_advisory_xact_lock" in sql for sql, _ in cur.calls))

    def test_seeds_exactly_16_parents_when_empty(self):
        cur = FakeCursor(count_value=0)
        categories.seed_presets(cur, tenant_id="t1", workspace_client_id=6)
        self.assertEqual(len(cur.parent_inserts()), 16)


if __name__ == "__main__":
    unittest.main()
