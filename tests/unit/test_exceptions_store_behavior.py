# -*- coding: utf-8 -*-
"""
REFACTOR-WA 覆盖补强 · services/exceptions/store.py 行为单测(异常栏 DAL · 非高敏)

补真实行为/边界/错误分支覆盖(原仅 test_exceptions_store_contract 锁结构 · 行为覆盖 ~9%):
insert/list/get/resolve/delete/count/batch_resolve 的 SQL 形状 + 参数 + 返回映射 +
tenant vs 无-tenant 隔离两路径 + ON CONFLICT no-op + 异常吞咽兜底 + 越权过滤。
全部用 FakeCursor mock(隔离确定 · 不打真实 DB · 不触发任何外部)。
"""

import unittest
from unittest import mock

import db  # noqa: F401  · 先 import db 完成,避免 dal_reexports partial-init 循环
from services.exceptions import store as exc


class FakeCursor:
    """记录每次 execute 的 (sql, params);可预设 fetchone/fetchall 与 rowcount。"""

    def __init__(self, fetchone=None, fetchall=None, rowcount=0):
        self.calls = []
        self._fetchone = fetchone
        self._fetchall = fetchall if fetchall is not None else []
        self.rowcount = rowcount

    def execute(self, sql, params=None):
        self.calls.append((sql, params))

    def fetchone(self):
        return self._fetchone

    def fetchall(self):
        return self._fetchall

    @property
    def last_sql(self):
        return self.calls[-1][0] if self.calls else ""

    @property
    def last_params(self):
        return self.calls[-1][1] if self.calls else None

    def all_sql(self):
        return " ".join(c[0] for c in self.calls)


class _CM:
    def __init__(self, cur, kwargs_box):
        self.cur = cur
        self._box = kwargs_box

    def __enter__(self):
        return self.cur

    def __exit__(self, *a):
        return False


def patch_cursor(cur):
    """把 exc.db.get_cursor 换成产出 cur 的工厂 · 收集每次 commit kwarg 到 cur.cm_kwargs。"""
    cur.cm_kwargs = []

    def factory(*a, **k):
        cur.cm_kwargs.append(k)
        return _CM(cur, None)

    return mock.patch.object(exc.db, "get_cursor", factory)


def patch_cursor_raises(exc_obj=RuntimeError("boom")):
    def factory(*a, **k):
        raise exc_obj

    return mock.patch.object(exc.db, "get_cursor", factory)


class InsertExceptionTests(unittest.TestCase):
    def test_insert_returns_id_and_uses_commit_and_conflict(self):
        cur = FakeCursor(fetchone={"id": 42})
        with patch_cursor(cur):
            ex_id = exc.insert_exception(
                "u1",
                "t1",
                "h-uuid",
                "ERR_NO_TOTAL",
                severity="high",
                seller_name="ACME",
                invoice_no="INV-1",
                total_amount=100.0,
                detail={"k": "v"},
            )
        self.assertEqual(ex_id, 42)
        self.assertIn("INSERT INTO exceptions", cur.last_sql)
        self.assertIn("ON CONFLICT", cur.last_sql)
        self.assertEqual(cur.cm_kwargs[0].get("commit"), True)  # DDL/写必须 commit
        p = cur.last_params
        self.assertEqual(p[0], "u1")
        self.assertEqual(p[1], "t1")
        self.assertEqual(p[3], "ERR_NO_TOTAL")
        # detail 被 JSON 序列化
        self.assertIn('"k": "v"', p[8])

    def test_insert_conflict_noop_returns_none(self):
        cur = FakeCursor(fetchone=None)  # ON CONFLICT DO NOTHING → 无 RETURNING 行
        with patch_cursor(cur):
            self.assertIsNone(exc.insert_exception("u1", "t1", "h", "R"))

    def test_insert_exception_swallowed_returns_none(self):
        with patch_cursor_raises():
            self.assertIsNone(exc.insert_exception("u1", "t1", "h", "R"))


class ListExceptionsTests(unittest.TestCase):
    def test_tenant_path_filters_by_tenant(self):
        cur = FakeCursor(fetchall=[])
        with patch_cursor(cur):
            exc.list_exceptions("u1", tenant_id="t1", status="pending")
        self.assertIn("e.tenant_id = %s", cur.last_sql)
        self.assertNotIn("e.tenant_id IS NULL", cur.last_sql)
        self.assertEqual(cur.last_params[0], "t1")
        self.assertIn("e.status = %s", cur.last_sql)

    def test_no_tenant_path_filters_by_user_and_null_tenant(self):
        cur = FakeCursor(fetchall=[])
        with patch_cursor(cur):
            exc.list_exceptions("u1", tenant_id=None)
        self.assertIn("e.user_id = %s", cur.last_sql)
        self.assertIn("e.tenant_id IS NULL", cur.last_sql)

    def test_status_all_drops_status_clause(self):
        cur = FakeCursor(fetchall=[])
        with patch_cursor(cur):
            exc.list_exceptions("u1", tenant_id="t1", status="all")
        self.assertNotIn("e.status = %s", cur.last_sql)

    def test_restrict_client_ids_empty_vs_nonempty(self):
        cur = FakeCursor(fetchall=[])
        with patch_cursor(cur):
            exc.list_exceptions("u1", tenant_id="t1", restrict_client_ids=[])
        self.assertIn("h.client_id IS NULL", cur.last_sql)
        cur2 = FakeCursor(fetchall=[])
        with patch_cursor(cur2):
            exc.list_exceptions("u1", tenant_id="t1", restrict_client_ids=[5, 6])
        self.assertIn("h.client_id = ANY(%s::bigint[])", cur2.last_sql)
        self.assertIn([5, 6], cur2.last_params)

    def test_row_mapping_and_limit_offset(self):
        row = {
            "id": 7,
            "history_id": "hid",
            "rule_code": "R",
            "severity": "high",
            "seller_name": "S",
            "invoice_no": "I",
            "total_amount": "12.50",
            "detail_json": None,
            "status": "pending",
            "created_at": None,
            "resolved_at": None,
            "filename": "f.pdf",
            "invoice_date": None,
            "confidence": 0.9,
            "client_id": "3",
        }
        cur = FakeCursor(fetchall=[row])
        with patch_cursor(cur):
            items = exc.list_exceptions("u1", tenant_id="t1", limit=20, offset=40)
        self.assertEqual(len(items), 1)
        it = items[0]
        self.assertEqual(it["id"], 7)
        self.assertEqual(it["total_amount"], 12.5)  # str→float
        self.assertEqual(it["detail"], {})  # None→{}
        self.assertEqual(it["client_id"], 3)  # str→int
        self.assertEqual(cur.last_params[-2:], [20, 40])  # LIMIT/OFFSET 末尾

    def test_exception_returns_empty_list(self):
        with patch_cursor_raises():
            self.assertEqual(exc.list_exceptions("u1", tenant_id="t1"), [])


class GetExceptionTests(unittest.TestCase):
    def test_found_maps_dict(self):
        row = {
            "id": 1,
            "history_id": "h",
            "rule_code": "R",
            "severity": "low",
            "seller_name": None,
            "invoice_no": None,
            "total_amount": None,
            "detail_json": {"a": 1},
            "status": "pending",
            "created_at": None,
            "resolved_at": None,
            "filename": None,
            "confidence": None,
        }
        cur = FakeCursor(fetchone=row)
        with patch_cursor(cur):
            out = exc.get_exception("u1", 1, tenant_id="t1")
        self.assertEqual(out["id"], 1)
        self.assertIsNone(out["total_amount"])
        self.assertEqual(out["detail"], {"a": 1})
        self.assertIn("e.tenant_id = %s", cur.last_sql)

    def test_not_found_returns_none(self):
        cur = FakeCursor(fetchone=None)
        with patch_cursor(cur):
            self.assertIsNone(exc.get_exception("u1", 99, tenant_id=None))
        self.assertIn("e.user_id = %s", cur.last_sql)  # 无 tenant 走 user 路径

    def test_exception_returns_none(self):
        with patch_cursor_raises():
            self.assertIsNone(exc.get_exception("u1", 1, tenant_id="t1"))


class ResolveExceptionTests(unittest.TestCase):
    def test_invalid_status_returns_false_without_db(self):
        # 非法状态直接 False · 不应触碰 get_cursor
        with patch_cursor_raises():
            self.assertFalse(exc.resolve_exception("u1", 1, "t1", new_status="bogus"))

    def test_valid_resolve_rowcount(self):
        cur = FakeCursor(rowcount=1)
        with patch_cursor(cur):
            self.assertTrue(exc.resolve_exception("u1", 1, tenant_id="t1", new_status="resolved"))
        self.assertIn("UPDATE exceptions", cur.last_sql)
        self.assertIn(
            "e.tenant_id = %s", cur.last_sql.replace("tenant_id = %s", "e.tenant_id = %s")
        )
        self.assertEqual(cur.cm_kwargs[0].get("commit"), True)

    def test_rowcount_zero_returns_false(self):
        cur = FakeCursor(rowcount=0)
        with patch_cursor(cur):
            self.assertFalse(exc.resolve_exception("u1", 1, tenant_id=None, new_status="ignored"))

    def test_exception_returns_false(self):
        with patch_cursor_raises():
            self.assertFalse(exc.resolve_exception("u1", 1, "t1", new_status="resolved"))


class DeletePendingTests(unittest.TestCase):
    def test_returns_rowcount_tenant_path(self):
        cur = FakeCursor(rowcount=3)
        with patch_cursor(cur):
            n = exc.delete_pending_exceptions_by_history("h", tenant_id="t1")
        self.assertEqual(n, 3)
        self.assertIn("DELETE FROM exceptions", cur.last_sql)
        self.assertIn("status = 'pending'", cur.last_sql)

    def test_no_tenant_path(self):
        cur = FakeCursor(rowcount=0)
        with patch_cursor(cur):
            exc.delete_pending_exceptions_by_history("h", tenant_id=None, user_id="u1")
        self.assertIn("tenant_id IS NULL", cur.last_sql)

    def test_exception_returns_zero(self):
        with patch_cursor_raises():
            self.assertEqual(exc.delete_pending_exceptions_by_history("h", "t1"), 0)


class CountTests(unittest.TestCase):
    def test_aggregation_by_status_rule_and_high_severity(self):
        rows = [
            {"status": "pending", "rule_code": "A", "severity": "high", "n": 2},
            {"status": "pending", "rule_code": "B", "severity": "low", "n": 1},
            {"status": "resolved", "rule_code": "A", "severity": "high", "n": 5},
        ]
        cur = FakeCursor(fetchall=rows)
        with patch_cursor(cur):
            out = exc.count_exceptions_by_status_and_rule("u1", tenant_id="t1")
        self.assertEqual(out["pending"], 3)
        self.assertEqual(out["resolved"], 5)
        self.assertEqual(out["high_severity"], 2)  # 仅 pending+high
        self.assertEqual(out["by_rule"], {"A": 2, "B": 1})  # 默认 by_rule_status=pending

    def test_by_rule_status_resolved(self):
        rows = [
            {"status": "pending", "rule_code": "A", "severity": "low", "n": 1},
            {"status": "resolved", "rule_code": "B", "severity": "low", "n": 4},
        ]
        cur = FakeCursor(fetchall=rows)
        with patch_cursor(cur):
            out = exc.count_exceptions_by_status_and_rule(
                "u1", tenant_id="t1", by_rule_status="resolved"
            )
        self.assertEqual(out["by_rule"], {"B": 4})

    def test_client_id_filter_adds_clause(self):
        cur = FakeCursor(fetchall=[])
        with patch_cursor(cur):
            exc.count_exceptions_by_status_and_rule("u1", tenant_id="t1", client_id=9)
        self.assertIn("h.client_id = %s", cur.last_sql)
        self.assertIn(9, cur.last_params)

    def test_exception_returns_default(self):
        with patch_cursor_raises():
            out = exc.count_exceptions_by_status_and_rule("u1", "t1")
        self.assertEqual(out["pending"], 0)
        self.assertEqual(out["by_rule"], {})


class BatchResolveTests(unittest.TestCase):
    def test_invalid_status_empty(self):
        self.assertEqual(
            exc.batch_resolve_exceptions("u1", [1, 2], "t1", new_status="bogus")["processed"], 0
        )

    def test_empty_ids_empty(self):
        self.assertEqual(exc.batch_resolve_exceptions("u1", [], "t1")["processed"], 0)

    def test_no_matching_rows_empty(self):
        cur = FakeCursor(fetchall=[])  # SELECT 返空 → 无可处理
        with patch_cursor(cur):
            out = exc.batch_resolve_exceptions("u1", [1, 2], tenant_id="t1")
        self.assertEqual(out["processed"], 0)
        self.assertEqual(out["ids_done"], [])

    def test_resolved_no_whitelist_pairs(self):
        rows = [{"id": 1, "seller_name": "ACME", "rule_code": "R"}]
        cur = FakeCursor(fetchall=rows, rowcount=1)
        with patch_cursor(cur):
            out = exc.batch_resolve_exceptions("u1", [1], tenant_id="t1", new_status="resolved")
        self.assertEqual(out["ids_done"], [1])
        self.assertEqual(out["whitelist_pairs"], [])  # resolved 不产白名单对

    def test_ignored_dedups_whitelist_pairs_and_skips_blank_seller(self):
        rows = [
            {"id": 1, "seller_name": "ACME", "rule_code": "R1"},
            {"id": 2, "seller_name": "ACME", "rule_code": "R1"},  # 重复 → 去重
            {"id": 3, "seller_name": "", "rule_code": "R2"},  # 空 seller → 跳过
            {"id": 4, "seller_name": "BETA", "rule_code": "R2"},
        ]
        cur = FakeCursor(fetchall=rows, rowcount=4)
        with patch_cursor(cur):
            out = exc.batch_resolve_exceptions(
                "u1", [1, 2, 3, 4], tenant_id="t1", new_status="ignored"
            )
        self.assertEqual(out["processed"], 4)
        self.assertEqual(out["ids_done"], [1, 2, 3, 4])
        self.assertEqual(out["whitelist_pairs"], [("ACME", "R1"), ("BETA", "R2")])

    def test_exception_returns_error_dict(self):
        with patch_cursor_raises():
            out = exc.batch_resolve_exceptions("u1", [1], "t1", new_status="resolved")
        self.assertEqual(out["processed"], 0)
        self.assertIn("error", out)


if __name__ == "__main__":
    unittest.main()
