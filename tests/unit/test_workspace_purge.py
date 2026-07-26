# -*- coding: utf-8 -*-
"""按账套清空数据的服务层行为(假游标 · 不起真库)。

钉三件最容易出事的:
  ① 隔离——每条 DELETE 都必须带 workspace_client_id,一条不带就是横扫别人的账套;
  ② 顺序——子表先于父表删,否则 RESTRICT 外键会把父表挡下来;
  ③ 卡住要如实报——外键死结时 leftover 必须有内容,不许报"清空成功"。
"""

from __future__ import annotations

import unittest

from services.workspace import purge as P

SCOPE = ["ocr_history", "products", "work_orders"]
EDGES = [
    {
        "child": "work_order_items",
        "child_col": "work_order_id",
        "parent": "work_orders",
        "parent_col": "id",
    },
]


class _FakeCursor:
    """记录每条 execute;按需让指定表的 DELETE 抛一次外键错(模拟顺序问题)。"""

    def __init__(self, fail_once_on=None):
        self.executed: list = []
        self.rowcount = 0
        self._fail_once = set(fail_once_on or [])
        self._rows = []

    def execute(self, sql, params=None):
        self.executed.append((" ".join(sql.split()), params))
        s = sql.strip().upper()
        if s.startswith(("SAVEPOINT", "RELEASE", "ROLLBACK")):
            self.rowcount = 0
            return
        if s.startswith("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.COLUMNS") and "'PUBLIC'" in s:
            self._rows = [{"table_name": t} for t in SCOPE]
            return
        if "CONSTRAINT_TYPE = 'FOREIGN KEY'" in sql.upper():
            self._rows = [dict(e) for e in EDGES]
            return
        if s.startswith("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS"):
            self._rows = [{"column_name": c} for c in ("address", "phone", "name", "tax_id")]
            return
        if s.startswith("SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS"):
            self._rows = [{"?column?": 1}]
            return
        if s.startswith("DELETE"):
            table = sql.split("FROM", 1)[1].split()[0]
            if table in self._fail_once:
                self._fail_once.discard(table)
                raise RuntimeError(f"fk violation on {table}")
            self.rowcount = 3
            return
        self.rowcount = 0

    def fetchall(self):
        rows, self._rows = self._rows, []
        return rows

    def fetchone(self):
        rows, self._rows = self._rows, []
        return rows[0] if rows else None


def _deletes(cur):
    return [(sql, params) for sql, params in cur.executed if sql.upper().startswith("DELETE")]


class PurgeIsolationTests(unittest.TestCase):
    def test_every_delete_is_scoped_to_the_workspace(self):
        cur = _FakeCursor()
        list(P.purge(cur, tenant_id="t-1", ws_id=42))
        deletes = _deletes(cur)
        self.assertTrue(deletes, "一条 DELETE 都没跑,测试本身失效")
        for sql, params in deletes:
            self.assertIn("workspace_client_id", sql, f"这条 DELETE 没带账套隔离: {sql}")
            self.assertIn(42, list(params or ()), f"账套 id 没进参数: {sql}")

    def test_tenant_id_stacked_when_column_exists(self):
        cur = _FakeCursor()
        list(P.purge(cur, tenant_id="t-1", ws_id=42))
        scope_deletes = [s for s, _ in _deletes(cur) if "IN (SELECT" not in s]
        self.assertTrue(scope_deletes)
        for sql in scope_deletes:
            self.assertIn("tenant_id = %s", sql, f"账套级表该叠租户隔离: {sql}")


class PurgeOrderTests(unittest.TestCase):
    def test_child_tables_deleted_before_their_parent(self):
        cur = _FakeCursor()
        list(P.purge(cur, tenant_id="t-1", ws_id=42))
        order = [s for s, _ in _deletes(cur)]
        child = next(i for i, s in enumerate(order) if s.startswith("DELETE FROM work_order_items"))
        # 认语句开头,不认子串:子表那条的子查询里也有 "FROM work_orders WHERE"。
        parent = next(i for i, s in enumerate(order) if s.startswith("DELETE FROM work_orders "))
        self.assertLess(child, parent, "子表必须先于父表删,否则 RESTRICT 外键挡住父表")

    def test_table_that_fails_once_is_retried_and_succeeds(self):
        cur = _FakeCursor(fail_once_on={"products"})
        events = list(P.purge(cur, tenant_id="t-1", ws_id=42))
        finished = events[-1]
        self.assertEqual(finished["step"], "finished")
        self.assertEqual(finished["leftover"], [], "重试一轮就该成功,不该留残表")
        self.assertIn("products", [e.get("label") for e in events])


class PurgeHonestyTests(unittest.TestCase):
    def test_permanently_stuck_table_is_reported_not_hidden(self):
        cur = _FakeCursor()
        cur._fail_once = set()

        original = cur.execute

        def always_fail(sql, params=None):
            if sql.strip().upper().startswith("DELETE") and "products" in sql:
                cur.executed.append((" ".join(sql.split()), params))
                raise RuntimeError("fk violation forever")
            return original(sql, params)

        cur.execute = always_fail
        finished = list(P.purge(cur, tenant_id="t-1", ws_id=42))[-1]
        self.assertEqual(finished["step"], "finished")
        self.assertIn("products", finished["leftover"], "删不掉的表必须报出来,不许假装清空了")

    def test_subject_row_keeps_name_and_tax_id(self):
        cur = _FakeCursor()
        list(P.purge(cur, tenant_id="t-1", ws_id=42))
        updates = [s for s, _ in cur.executed if s.upper().startswith("UPDATE WORKSPACE_CLIENTS")]
        self.assertEqual(len(updates), 1)
        sql = updates[0]
        self.assertIn("address = NULL", sql)
        self.assertIn("phone = NULL", sql)
        self.assertNotIn("name = NULL", sql, "套账名称必须留下")
        self.assertNotIn("tax_id = NULL", sql, "税号必须留下")


class PurgeFilePathGuardTests(unittest.TestCase):
    def test_paths_outside_storage_root_are_skipped(self):
        # 库里的字符串不是可信输入:越界路径必须跳过,不能顺着删到 storage 之外。
        removed = P.purge_files(["../../etc/passwd", "/etc/shadow"])
        self.assertEqual(removed, 0)


if __name__ == "__main__":
    unittest.main()
