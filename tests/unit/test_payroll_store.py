# -*- coding: utf-8 -*-
"""工资进料 DAL SQL 形态(假游标 · 不连库)。验隔离带 tenant_id、幂等 upsert、整体替换。"""

import datetime as dt
import json
import unittest
from decimal import Decimal

from services.payroll import model, store


class FakeCursor:
    def __init__(self, fetchone=None, fetchall=None):
        self.calls = []
        self._fetchone = fetchone
        self._fetchall = fetchall or []

    def execute(self, sql, params=None):
        self.calls.append((" ".join(sql.split()), params))

    def fetchone(self):
        return self._fetchone

    def fetchall(self):
        return self._fetchall


def _row(seq, amount):
    return model.PayrollRow(
        seq=seq,
        employee_id="0105548082417",
        title="นาย",
        first_name="ก",
        last_name="ข",
        paid_amount=Decimal(str(amount)),
        wht_amount=Decimal("0"),
        paid_date=dt.date(2026, 5, 31),
    )


class TemplateStoreTests(unittest.TestCase):
    def test_upsert_template_idempotent_and_serializes_json(self):
        cur = FakeCursor()
        store.upsert_template(
            cur,
            tenant_id="t",
            workspace_client_id=1,
            column_map={model.F_EMPLOYEE_ID: 3},
            fixed_values={"a": 1},
        )
        sql, params = cur.calls[0]
        self.assertIn("INSERT INTO client_payroll_templates", sql)
        self.assertIn("ON CONFLICT (tenant_id, workspace_client_id) DO UPDATE", sql)
        self.assertEqual(params[0], "t")
        self.assertEqual(json.loads(params[2]), {model.F_EMPLOYEE_ID: 3})

    def test_get_template_parses_json_columns(self):
        cur = FakeCursor(
            fetchone={
                "column_map": json.dumps({model.F_PAID_AMOUNT: 8}),
                "income_code": "40(1)",
                "fixed_values": "{}",
                "header_hash": "h",
            }
        )
        tpl = store.get_template(cur, tenant_id="t", workspace_client_id=1)
        self.assertEqual(tpl["column_map"], {model.F_PAID_AMOUNT: 8})
        self.assertIn("WHERE tenant_id = %s AND workspace_client_id = %s", cur.calls[0][0])

    def test_get_template_missing_returns_none(self):
        self.assertIsNone(
            store.get_template(FakeCursor(fetchone=None), tenant_id="t", workspace_client_id=9)
        )


class PeriodRowsStoreTests(unittest.TestCase):
    def test_save_replaces_then_inserts(self):
        cur = FakeCursor()
        n = store.save_period_rows(
            cur,
            tenant_id="t",
            workspace_client_id=1,
            period="2569-05",
            rows=[_row(1, 13000), _row(2, 12040)],
        )
        self.assertEqual(n, 2)
        self.assertIn("DELETE FROM client_payroll_rows", cur.calls[0][0])
        self.assertEqual(cur.calls[0][1], ("t", 1, "2569-05"))
        self.assertEqual(len(cur.calls), 3)  # 1 delete + 2 insert
        self.assertIn("INSERT INTO client_payroll_rows", cur.calls[1][0])
        # 金额以 Decimal 入参(禁 float)。
        self.assertIsInstance(cur.calls[1][1][10], Decimal)

    def test_load_period_rows_scoped_by_tenant(self):
        cur = FakeCursor(fetchall=[{"seq": 1}])
        rows = store.load_period_rows(cur, tenant_id="t", workspace_client_id=1, period="2569-05")
        self.assertEqual(rows, [{"seq": 1}])
        self.assertIn(
            "WHERE tenant_id = %s AND workspace_client_id = %s AND period = %s", cur.calls[0][0]
        )


class YearRowsStoreTests(unittest.TestCase):
    def test_load_year_rows_scoped_by_tenant_and_year_pattern(self):
        cur = FakeCursor(fetchall=[{"period": "2569-05", "seq": 1}])
        rows = store.load_year_rows(cur, tenant_id="t", workspace_client_id=1, tax_year="2569")
        self.assertEqual(rows, [{"period": "2569-05", "seq": 1}])
        sql, params = cur.calls[0]
        self.assertIn("WHERE tenant_id = %s AND workspace_client_id = %s AND period LIKE %s", sql)
        self.assertEqual(params, ("t", 1, "2569-%"))

    def test_load_year_rows_empty_when_no_data(self):
        cur = FakeCursor(fetchall=[])
        rows = store.load_year_rows(cur, tenant_id="t", workspace_client_id=1, tax_year="2570")
        self.assertEqual(rows, [])


if __name__ == "__main__":
    unittest.main()
