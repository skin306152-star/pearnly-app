#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_push_logs_adapter_filter.py

守门测试 · 批 3 改动 6 (Zihao 2026-05-19 拍板 · v118.34.34) ·
`db.list_push_logs(..., adapter_filter=...)` 的 SQL 契约.

ERP filter chip (MR.ERP / Xero / FlowAccount) 在 toolbar 里 ·
后端 endpoint /api/erp/logs?adapter=mrerp 透传到这里. 一旦 SQL 错:
  - false negative: 用户筛 MR.ERP 拉不到自己的 MR.ERP log
  - false positive: 跨账号读 (没拼 user_id) 或拉到 Xero/webhook log
  - performance: 没用 LOWER 索引或 join 错表 → slow query

覆盖:
  1. adapter_filter=None / "" → 不加 e.adapter 条件 (老 behavior 不动)
  2. adapter_filter="mrerp" → SQL 含 LOWER(e.adapter) = LOWER(%s) 且 params 有 "mrerp"
  3. 大小写不敏感: adapter_filter="MR.ERP" 也走 LOWER
  4. SQL 必有 LEFT JOIN erp_endpoints e (COUNT + main 都要)
  5. user_id 永远在 WHERE (防 cross-tenant)
"""

from __future__ import annotations

import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

# Stub psycopg2.
if "psycopg2" not in sys.modules:
    fake_pg = types.ModuleType("psycopg2")
    fake_pg.connect = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("stub"))
    fake_pg.Error = Exception
    fake_pg.OperationalError = Exception
    fake_pg.extras = types.ModuleType("psycopg2.extras")
    fake_pg.extras.RealDictCursor = object
    fake_pg.extras.DictCursor = object
    fake_pg.extras.execute_values = lambda *a, **k: None
    fake_pg.extras.Json = lambda x: x
    fake_pg.pool = types.ModuleType("psycopg2.pool")

    class _StubPool:
        def __init__(self, *a, **k):
            pass

        def getconn(self):
            raise RuntimeError("stub")

        def putconn(self, *a, **k):
            pass

        def closeall(self):
            pass

    fake_pg.pool.ThreadedConnectionPool = _StubPool
    fake_pg.pool.SimpleConnectionPool = _StubPool
    fake_pg.sql = types.ModuleType("psycopg2.sql")
    fake_pg.sql.SQL = lambda s: s
    fake_pg.sql.Identifier = lambda s: s
    sys.modules["psycopg2"] = fake_pg
    sys.modules["psycopg2.extras"] = fake_pg.extras
    sys.modules["psycopg2.pool"] = fake_pg.pool
    sys.modules["psycopg2.sql"] = fake_pg.sql


from core import db  # noqa: E402


class _MockCursor:
    """记录 execute · fetchone 返 {n: 0} · fetchall 返 [] (空结果)."""

    def __init__(self):
        self.executed = []
        self._call_count = 0

    def execute(self, sql, params=None):
        self.executed.append((sql, list(params) if params else []))
        self._call_count += 1

    def fetchone(self):
        # 第 1 次 fetchone 用于 COUNT query · 返 {n: 0}
        return {"n": 0}

    def fetchall(self):
        return []


class _MockCursorCM:
    def __init__(self, cursor):
        self.cursor = cursor

    def __enter__(self):
        return self.cursor

    def __exit__(self, exc_type, exc, tb):
        return False


class AdapterFilterShapeTests(unittest.TestCase):
    """SQL shape · 验证 adapter_filter 拼出的 WHERE 子句."""

    def _run(self, **kwargs):
        cur = _MockCursor()
        with (
            patch.object(db, "get_cursor", lambda *a, **k: _MockCursorCM(cur)),
            patch.object(db, "get_cursor_rls", lambda *a, **k: _MockCursorCM(cur)),
        ):
            r = db.list_push_logs("user-X", **kwargs)
        return cur, r

    def test_no_adapter_filter_default_behavior(self):
        cur, r = self._run()
        # 应跑 COUNT + main 两条 SQL
        self.assertGreaterEqual(len(cur.executed), 2)
        # WHERE 不应包含 adapter 过滤条件 (LOWER(e.adapter) = LOWER(%s))
        # 注意: 主查询 SELECT 里有 `e.adapter AS endpoint_adapter` · 是合法的 ·
        # 我们只检 WHERE 子句不该出现 adapter filter.
        for sql, _ in cur.executed:
            self.assertNotIn(
                "LOWER(e.adapter)", sql, "未指定 adapter_filter 时不该加 LOWER(e.adapter) 过滤"
            )
        # 返回结构应 OK (空结果)
        self.assertEqual(r, {"items": [], "total": 0})

    def test_adapter_filter_mrerp_adds_where_clause(self):
        cur, _ = self._run(adapter_filter="mrerp")
        # 每条 SQL 都该有 LOWER(e.adapter) = LOWER(%s) (COUNT + main 两条)
        for sql, params in cur.executed:
            self.assertIn(
                "LOWER(e.adapter)", sql, f"adapter filter 必须用 LOWER 大小写不敏感 SQL: {sql}"
            )
            self.assertIn("LOWER(%s)", sql)
            # params 应包含 "mrerp" 字符串
            self.assertIn(
                "mrerp", [str(p) for p in params], f"params 应包含 adapter 值 mrerp: {params}"
            )

    def test_adapter_filter_case_insensitive_value(self):
        """前端可能传 "MR.ERP" 或 "MRERP" · 后端 LOWER 应都匹配."""
        cur, _ = self._run(adapter_filter="MR.ERP")
        for sql, params in cur.executed:
            self.assertIn("LOWER(e.adapter)", sql)
            # value 仍是用户传进来的 "MR.ERP" · SQL 里用 LOWER 处理
            self.assertIn("MR.ERP", [str(p) for p in params])

    def test_sql_always_joins_erp_endpoints_for_adapter_check(self):
        """COUNT + main 都必须 LEFT JOIN erp_endpoints e · 否则 e.adapter 引用不到."""
        cur, _ = self._run(adapter_filter="xero")
        for sql, _ in cur.executed:
            self.assertIn(
                "LEFT JOIN erp_endpoints", sql, f"SQL 缺 LEFT JOIN erp_endpoints (e): {sql[:200]}"
            )

    def test_user_id_always_in_where(self):
        """无论 adapter_filter 给没给 · user_id 必须出现在 WHERE 防 cross-tenant."""
        for af in (None, "", "mrerp", "xero"):
            cur, _ = self._run(adapter_filter=af)
            for sql, params in cur.executed:
                self.assertIn(
                    "user_id = %s",
                    sql,
                    f"user_id WHERE 必须存在 (adapter_filter={af!r}): {sql[:200]}",
                )
                self.assertIn(
                    "user-X",
                    [str(p) for p in params],
                    f"params 必须包含 user-X (adapter_filter={af!r})",
                )


class AdapterFilterCombinedWithStatusTests(unittest.TestCase):
    """adapter_filter 跟 status_filter / trigger_filter 共存 · 互不冲突."""

    def _run(self, **kwargs):
        cur = _MockCursor()
        with (
            patch.object(db, "get_cursor", lambda *a, **k: _MockCursorCM(cur)),
            patch.object(db, "get_cursor_rls", lambda *a, **k: _MockCursorCM(cur)),
        ):
            db.list_push_logs("user-Y", **kwargs)
        return cur

    def test_adapter_plus_success_filter(self):
        cur = self._run(adapter_filter="mrerp", status_filter="success")
        for sql, params in cur.executed:
            self.assertIn("LOWER(e.adapter)", sql)
            self.assertIn("status = 'success'", sql)
            self.assertIn("mrerp", [str(p) for p in params])

    def test_adapter_plus_trigger_filter(self):
        cur = self._run(adapter_filter="mrerp", trigger_filter="auto")
        for sql, params in cur.executed:
            self.assertIn("LOWER(e.adapter)", sql)
            self.assertIn("trigger = %s", sql)
            params_str = [str(p) for p in params]
            self.assertIn("mrerp", params_str)
            self.assertIn("auto", params_str)


class ExcludePushTypeShapeTests(unittest.TestCase):
    """exclude_push_type · 主站推送日志排身份证订车行(DMS 已搬 /dms)· total 诚实.

    判据与 push_type 同源(adapter=mrerp_dms 或 trigger=id_card)取否定,COUNT + main
    两条同拼(否则「共 N 条」含隐藏行虚高)。/dms 记录页走 adapter 参数、不传 exclude,
    仍能看到 id_card 行——故这里只在显式传参时才排,默认不动老 behavior.
    """

    # 排 id_card = push_type='invoice' 的等价否定式(单一判据源)。
    _EXCLUDE_IDCARD_SQL = "COALESCE(LOWER(e.adapter),'') <> 'mrerp_dms'"

    def _run(self, **kwargs):
        cur = _MockCursor()
        with (
            patch.object(db, "get_cursor", lambda *a, **k: _MockCursorCM(cur)),
            patch.object(db, "get_cursor_rls", lambda *a, **k: _MockCursorCM(cur)),
        ):
            db.list_push_logs("user-Z", **kwargs)
        return cur

    def test_no_exclude_default_behavior(self):
        cur = self._run()
        for sql, _ in cur.executed:
            self.assertNotIn(self._EXCLUDE_IDCARD_SQL, sql)

    def test_exclude_id_card_adds_negation_to_count_and_main(self):
        cur = self._run(exclude_push_type="id_card")
        self.assertGreaterEqual(len(cur.executed), 2)  # COUNT + main
        for sql, _ in cur.executed:
            self.assertIn(
                self._EXCLUDE_IDCARD_SQL,
                sql,
                "排 id_card 的否定式必须同时进 COUNT 和主查询(total 才诚实)",
            )
            self.assertIn("<> 'id_card'", sql)

    def test_exclude_invoice_is_inverse_predicate(self):
        cur = self._run(exclude_push_type="invoice")
        for sql, _ in cur.executed:
            self.assertIn("LOWER(e.adapter) = 'mrerp_dms' OR l.trigger = 'id_card'", sql)

    def test_exclude_stacks_with_adapter_filter(self):
        # /dms 记录页口径:adapter=mrerp_dms 不传 exclude → 仍看 id_card(见类注释)。
        # 主站口径:两者可并存,exclude 与 adapter 各自 AND 生效、互不吞没。
        cur = self._run(adapter_filter="mrerp", exclude_push_type="id_card")
        for sql, params in cur.executed:
            self.assertIn("LOWER(e.adapter) = LOWER(%s)", sql)
            self.assertIn(self._EXCLUDE_IDCARD_SQL, sql)
            self.assertIn("mrerp", [str(p) for p in params])

    def test_user_id_still_scoped(self):
        cur = self._run(exclude_push_type="id_card")
        for sql, params in cur.executed:
            self.assertIn("user_id = %s", sql)
            self.assertIn("user-Z", [str(p) for p in params])


if __name__ == "__main__":
    unittest.main()
