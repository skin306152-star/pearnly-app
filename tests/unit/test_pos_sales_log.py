# -*- coding: utf-8 -*-
"""POS 交易明细日志(services/pos/sales_log)守门测试。

锁定:
  1. list_sales:总数 + 分页明细往返,cashier_id 筛选带进两条查询的 WHERE
  2. 行映射:金额转字符串(JSON/CSV 安全)· 班次开/关时间透传 · 付款方式随 lang 本地化
  3. export_rows:复用 list_sales,不分页(limit=5000)
"""

import json
import unittest
from datetime import date, datetime
from decimal import Decimal

from services.pos import sales_log as svc


class FakeCursor:
    def __init__(self, fetch_queue=None, fetchall_queue=None):
        self.calls = []
        self._one = list(fetch_queue or [])
        self._all = list(fetchall_queue or [])

    def execute(self, sql, params=None):
        self.calls.append((sql, params))

    def fetchone(self):
        return self._one.pop(0) if self._one else None

    def fetchall(self):
        return self._all.pop(0) if self._all else []


def _row(**overrides):
    base = {
        "id": "s1",
        "receipt_no": "RCP-001",
        "sold_at": datetime(2026, 7, 8, 9, 16, 11),
        "cashier_id": "c1",
        "cashier_name": "Earn",
        "shift_id": "sh1",
        "shift_opened_at": datetime(2026, 7, 8, 8, 0, 0),
        "shift_closed_at": None,
        "subtotal": Decimal("271.03"),
        "discount_total": Decimal("0"),
        "vat_amount": Decimal("18.97"),
        "grand_total": Decimal("290.00"),
        "paid_total": Decimal("300.00"),
        "change_amount": Decimal("10.00"),
        "items": "บลัชออน x1",
        "qty_total": Decimal("1"),
        "method": "transfer",
    }
    base.update(overrides)
    return base


class ListSalesTests(unittest.TestCase):
    def test_total_and_items_roundtrip(self):
        cur = FakeCursor(fetch_queue=[{"n": 3}], fetchall_queue=[[_row()]])
        out = svc.list_sales(cur, tenant_id="t-1", workspace_client_id=7)
        self.assertEqual(out["total"], 3)
        self.assertEqual(len(out["items"]), 1)
        item = out["items"][0]
        self.assertEqual(item["receipt_no"], "RCP-001")
        self.assertEqual(item["cashier_name"], "Earn")
        self.assertEqual(item["grand_total"], "290.00")
        self.assertEqual(item["method"], "โอนเงิน")  # 默认 lang=th
        self.assertEqual(item["shift_opened_at"], "2026-07-08T08:00:00")
        self.assertEqual(item["shift_closed_at"], "")  # 未交班 → 空字符串不是 None

    def test_all_money_fields_are_json_safe(self):
        cur = FakeCursor(fetch_queue=[{"n": 1}], fetchall_queue=[[_row()]])
        out = svc.list_sales(cur, tenant_id="t-1", workspace_client_id=7, lang="zh")
        json.dumps(out)  # Decimal 混进去会在这里炸(同 sheets_sync 那次真事故)
        self.assertEqual(out["items"][0]["method"], "银行转账")

    def test_cashier_filter_appends_to_both_queries(self):
        cur = FakeCursor(fetch_queue=[{"n": 0}], fetchall_queue=[[]])
        svc.list_sales(cur, tenant_id="t-1", workspace_client_id=7, cashier_id="c9")
        count_sql, count_params = cur.calls[0]
        rows_sql, rows_params = cur.calls[1]
        self.assertIn("s.cashier_id = %s", count_sql)
        self.assertIn("c9", count_params)
        self.assertIn("s.cashier_id = %s", rows_sql)
        self.assertIn("c9", rows_params)

    def test_date_range_appends_from_and_to(self):
        cur = FakeCursor(fetch_queue=[{"n": 0}], fetchall_queue=[[]])
        svc.list_sales(
            cur,
            tenant_id="t-1",
            workspace_client_id=7,
            date_from=date(2026, 7, 1),
            date_to=date(2026, 7, 8),
        )
        rows_sql, rows_params = cur.calls[1]
        self.assertIn("s.sold_at >= %s", rows_sql)
        self.assertIn("s.sold_at < %s", rows_sql)
        self.assertIn(date(2026, 7, 1), rows_params)

    def test_no_shift_or_cashier_defaults_blank(self):
        cur = FakeCursor(
            fetch_queue=[{"n": 1}],
            fetchall_queue=[
                [_row(cashier_id=None, cashier_name=None, shift_id=None, shift_opened_at=None)]
            ],
        )
        out = svc.list_sales(cur, tenant_id="t-1", workspace_client_id=7)
        item = out["items"][0]
        self.assertIsNone(item["cashier_id"])
        self.assertEqual(item["cashier_name"], "")
        self.assertIsNone(item["shift_id"])
        self.assertEqual(item["shift_opened_at"], "")


class ExportRowsTests(unittest.TestCase):
    def test_export_uncapped_page_size(self):
        cur = FakeCursor(fetch_queue=[{"n": 1}], fetchall_queue=[[_row()]])
        rows = svc.export_rows(cur, tenant_id="t-1", workspace_client_id=7)
        self.assertEqual(len(rows), 1)
        rows_sql, rows_params = cur.calls[1]
        self.assertIn(5000, rows_params)


if __name__ == "__main__":
    unittest.main()
