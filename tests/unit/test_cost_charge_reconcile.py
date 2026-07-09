# -*- coding: utf-8 -*-
"""scripts/cost_charge_reconcile.py 核心比对逻辑单测(#4b 对账脚本 · 只读)。

覆盖:三份已取数据(ocr 计数/credit 计数/豁免租户集合)→ 按租户对比行的纯函数
build_reconcile_rows;两个 fetch_* 函数的 SQL 形状(mock cursor)。脚本无 import 副作用
(sys.path 注入在 __main__ 之外也安全),直接 import 模块跑单测。
"""

import sys
import unittest
from datetime import date, datetime, timezone
from pathlib import Path

# scripts/ 非 package(无 __init__.py)· 同 tests/unit/test_anti_bigfile.py 的引入范式
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import cost_charge_reconcile as reconcile  # noqa: E402


class FakeCursor:
    def __init__(self, fetchall=None):
        self.calls = []
        self._fetchall = fetchall if fetchall is not None else []

    def execute(self, sql, params=None):
        self.calls.append((sql, params))

    def fetchall(self):
        return self._fetchall

    @property
    def last_sql(self):
        return self.calls[-1][0] if self.calls else ""

    @property
    def last_params(self):
        return self.calls[-1][1] if self.calls else None


class FetchShapeTests(unittest.TestCase):
    def test_fetch_ocr_counts_filters_ok_status(self):
        cur = FakeCursor()
        start = datetime(2026, 7, 8, tzinfo=timezone.utc)
        end = datetime(2026, 7, 9, tzinfo=timezone.utc)
        reconcile.fetch_ocr_counts(cur, start, end)
        self.assertIn("status = 'ok'", cur.last_sql)
        self.assertIn("GROUP BY tenant_id", cur.last_sql)
        self.assertEqual(cur.last_params, (start, end))

    def test_fetch_credit_usage_counts_filters_usage_type(self):
        cur = FakeCursor()
        start = datetime(2026, 7, 8, tzinfo=timezone.utc)
        end = datetime(2026, 7, 9, tzinfo=timezone.utc)
        reconcile.fetch_credit_usage_counts(cur, start, end)
        self.assertIn("type = 'usage'", cur.last_sql)
        self.assertEqual(cur.last_params, (start, end))

    def test_fetch_exempt_tenant_ids_maps_to_str_set(self):
        cur = FakeCursor(fetchall=[{"tenant_id": "t1"}, {"tenant_id": "t2"}])
        out = reconcile.fetch_exempt_tenant_ids(cur)
        self.assertEqual(out, {"t1", "t2"})


class BuildReconcileRowsTests(unittest.TestCase):
    def test_matched_tenant_zero_diff(self):
        ocr = [{"tenant_id": "t1", "cnt": 5, "cost": "1.0"}]
        credit = [{"tenant_id": "t1", "cnt": 5, "amt": "10.0"}]
        rows = reconcile.build_reconcile_rows(ocr, credit, set())
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["diff_count"], 0)
        self.assertFalse(rows[0]["has_exempt_user"])

    def test_ocr_only_tenant_flagged_exempt(self):
        # 豁免账号:只有识别侧,没有扣费侧(预期不对称)
        ocr = [{"tenant_id": "t1", "cnt": 3, "cost": "0.3"}]
        rows = reconcile.build_reconcile_rows(ocr, [], {"t1"})
        self.assertEqual(rows[0]["diff_count"], 3)
        self.assertTrue(rows[0]["has_exempt_user"])

    def test_credit_only_tenant_negative_diff_not_exempt(self):
        credit = [{"tenant_id": "t2", "cnt": 2, "amt": "4.0"}]
        rows = reconcile.build_reconcile_rows([], credit, set())
        self.assertEqual(rows[0]["diff_count"], -2)
        self.assertFalse(rows[0]["has_exempt_user"])

    def test_null_tenant_row_handled(self):
        ocr = [{"tenant_id": None, "cnt": 1, "cost": "0.01"}]
        rows = reconcile.build_reconcile_rows(ocr, [], set())
        self.assertIsNone(rows[0]["tenant_id"])

    def test_sorted_by_tenant_id_none_first(self):
        ocr = [
            {"tenant_id": "zzz", "cnt": 1, "cost": "0"},
            {"tenant_id": None, "cnt": 1, "cost": "0"},
            {"tenant_id": "aaa", "cnt": 1, "cost": "0"},
        ]
        rows = reconcile.build_reconcile_rows(ocr, [], set())
        self.assertEqual([r["tenant_id"] for r in rows], [None, "aaa", "zzz"])


class PrintReportExitSignalTests(unittest.TestCase):
    def test_has_diff_true_when_any_row_mismatched(self):
        rows = [
            {
                "tenant_id": "t1",
                "ocr_count": 1,
                "ocr_cost_thb": 0.1,
                "credit_count": 0,
                "credit_amount_thb": 0.0,
                "diff_count": 1,
                "has_exempt_user": False,
            }
        ]
        self.assertTrue(reconcile.print_report(date(2026, 7, 8), rows))

    def test_has_diff_false_when_all_zero(self):
        rows = [
            {
                "tenant_id": "t1",
                "ocr_count": 1,
                "ocr_cost_thb": 0.1,
                "credit_count": 1,
                "credit_amount_thb": 1.0,
                "diff_count": 0,
                "has_exempt_user": False,
            }
        ]
        self.assertFalse(reconcile.print_report(date(2026, 7, 8), rows))

    def test_empty_rows_no_diff(self):
        self.assertFalse(reconcile.print_report(date(2026, 7, 8), []))


if __name__ == "__main__":
    unittest.main()
