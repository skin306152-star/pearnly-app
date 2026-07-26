# -*- coding: utf-8 -*-
"""按账套清空数据的服务层行为(假游标 · 不起真库)。

钉三件最容易出事的:
  ① 隔离——每条 DELETE 都必须带 workspace_client_id,一条不带就是横扫别人的账套;
  ② 顺序——子表先于父表删,否则 RESTRICT 外键会把父表挡下来;
  ③ 卡住要如实报——外键死结时 leftover 必须有内容,不许报"清空成功"。
"""

from __future__ import annotations

import unittest
from pathlib import Path

from services.workspace import purge as P
from services.workspace import purge_files as PF

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

    def __init__(self, fail_once_on=None, leftover_rows=None):
        self.executed: list = []
        self.rowcount = 0
        self._fail_once = set(fail_once_on or [])
        self._rows = []
        # 删完回数时每张表还剩多少行(默认全 0 = 真清干净)
        self.leftover_rows = dict(leftover_rows or {})

    def execute(self, sql, params=None):
        self.executed.append((" ".join(sql.split()), params))
        s = sql.strip().upper()
        if s.startswith(("SAVEPOINT", "RELEASE", "ROLLBACK")):
            self.rowcount = 0
            return
        if "PG_CONSTRAINT" in s:
            self._rows = [dict(e) for e in EDGES]
            return
        if "PG_ATTRIBUTE" in s and "WORKSPACE_CLIENT_ID" in s:
            self._rows = [{"table_name": t} for t in SCOPE]
            return
        if "PG_ATTRIBUTE" in s and "TENANT_ID" in s:
            self._rows = [{"?column?": 1}]
            return
        if s.startswith("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS"):
            self._rows = [{"column_name": c} for c in ("address", "phone", "name", "tax_id")]
            return
        if s.startswith("SELECT COUNT(*)"):
            table = sql.split("FROM", 1)[1].split()[0]
            self._rows = [{"n": self.leftover_rows.get(table, 0)}]
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
    def test_leftover_comes_from_real_recount_not_rowcount(self):
        """结论必须靠删完真回数。

        2026-07-26 线上事故的形状:子表一张没删,但每条 DELETE 都「成功」(rowcount=0),
        按 rowcount 判就是「全清干净」。这里让所有 DELETE 都报成功、回数却仍有 105 行,
        结论必须是残留。
        """
        cur = _FakeCursor(leftover_rows={"work_order_items": 105})
        finished = list(P.purge(cur, tenant_id="t-1", ws_id=42))[-1]
        self.assertEqual(finished["step"], "finished")
        self.assertIn("work_order_items", finished["leftover"], "回数还有行就必须报残留")
        self.assertEqual(finished["leftover_detail"], [{"table": "work_order_items", "rows": 105}])

    def test_clean_purge_reports_no_leftover(self):
        cur = _FakeCursor()
        finished = list(P.purge(cur, tenant_id="t-1", ws_id=42))[-1]
        self.assertEqual(finished["leftover"], [])
        self.assertEqual(finished["leftover_detail"], [])

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


class SchemaDiscoveryPrivilegeTests(unittest.TestCase):
    """根因钉(2026-07-26 线上事故)。

    information_schema 的约束视图【按权限过滤】——只对表属主可见。生产业务连接跑在
    最小权限角色 pearnly_app 上,constraint_column_usage / key_column_usage 一律返回 0 行,
    于是子表清单为空、一张子表没删、父表被 RESTRICT 挡住,却报「清除完毕」。
    本地验收连的是属主账号,视图正常,所以本地怎么跑都是绿的。
    表结构一律走 pg_catalog(不挑权限),这条钉住它别被改回去。
    """

    def test_discovery_never_uses_privilege_filtered_views(self):
        src = (Path(P.__file__)).read_text(encoding="utf-8")
        for view in (
            "information_schema.constraint_column_usage",
            "information_schema.key_column_usage",
            "information_schema.table_constraints",
        ):
            self.assertNotIn(view, src, f"{view} 按权限过滤,最小权限角色下返回空 → 静默漏删")

    def test_discovery_reads_pg_catalog(self):
        src = (Path(P.__file__)).read_text(encoding="utf-8")
        self.assertIn("pg_constraint", src)
        self.assertIn("pg_attribute", src)


class PurgeFilePathGuardTests(unittest.TestCase):
    def test_paths_outside_allowed_roots_are_skipped(self):
        # 库里的字符串不是可信输入:越界路径必须跳过,不能顺着删到允许的存储根之外。
        removed = PF.purge({"files": ["/etc/shadow", "../../etc/passwd"], "dirs": ["/etc"]})
        self.assertEqual(removed, 0)

    def test_collect_uses_the_columns_that_actually_hold_paths(self):
        """根因钉:上一版只认 ocr_history.storage_path —— 生产上这列恒 NULL,真正存路径的是
        pdf_storage_path;而且它相对的是 PDF_STORAGE_DIR 不是 storage 根。两处都错 →
        每次 files=0,用户上传的图一张没删过(单 workorders 目录线上就 1.4G)。"""
        src = (Path(PF.__file__)).read_text(encoding="utf-8")
        self.assertIn("pdf_storage_path", src)
        self.assertIn("PDF_STORAGE_DIR", src)
        self.assertIn("WORKORDER_STORAGE_DIR", src, "用户上传的原件在工单目录下,必须一并删")
        self.assertNotIn("PEARNLY_STORAGE_ROOT", src, "别再拿 storage 根去拼相对路径")


if __name__ == "__main__":
    unittest.main()
