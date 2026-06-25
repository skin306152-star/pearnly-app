# -*- coding: utf-8 -*-
"""B8 RLS 自愈守卫契约:disable_orphan_rls 只关「RLS 已开但零 policy」的孤儿表。

事故复盘 docs/refactor/b8-rls-no-policy-orphans-INCIDENT.md:孤儿表对 pearnly_app 角色 deny-all,
会把走 get_cursor_rls 的查询静默拖空。守卫扫出这些表并 DISABLE,有 policy 的真隔离表不碰。
"""

import unittest

from core.rls import disable_orphan_rls


class _Cur:
    def __init__(self, orphans):
        self._orphans = orphans
        self.executed = []

    def execute(self, sql, *a):
        self.executed.append(sql)

    def fetchall(self):
        return [(name,) for name in self._orphans]


class DisableOrphanRlsContract(unittest.TestCase):
    def test_disables_each_orphan_and_returns_names(self):
        cur = _Cur(["users", "sales_documents"])
        result = disable_orphan_rls(cur)
        self.assertEqual(result, ["users", "sales_documents"])
        self.assertIn('ALTER TABLE "users" DISABLE ROW LEVEL SECURITY', cur.executed)
        self.assertIn('ALTER TABLE "sales_documents" DISABLE ROW LEVEL SECURITY', cur.executed)

    def test_noop_when_no_orphans(self):
        cur = _Cur([])
        result = disable_orphan_rls(cur)
        self.assertEqual(result, [])
        # 只跑了那条扫描 SELECT,没有任何 DISABLE
        self.assertTrue(all("DISABLE" not in s for s in cur.executed))

    def test_scans_before_any_disable(self):
        # 守卫先扫一次只读 pg 目录,再 DISABLE —— 不钉死谓词文本(免无谓改写即红)。
        cur = _Cur(["users"])
        disable_orphan_rls(cur)
        self.assertIn("pg_class", cur.executed[0])
        self.assertNotIn("DISABLE", cur.executed[0])


if __name__ == "__main__":
    unittest.main()
