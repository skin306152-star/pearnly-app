# -*- coding: utf-8 -*-
"""pos_cashier DAL 守门测试(POS 项目 · PO-B1)。

锁定:每条语句 WHERE tenant_id(应用层隔离)· 公开名单不漏 pin_hash · open 班次只读 ·
租户反查 · 全参数化(占位符,无 f-string 拼值)。"""

import unittest

from services.pos import cashier


class FakeCursor:
    def __init__(self, ones=None, many=None):
        self.calls = []
        self._ones = list(ones or [])
        self._many = list(many or [])

    def execute(self, sql, params=None):
        self.calls.append((sql, params))

    def fetchone(self):
        return self._ones.pop(0) if self._ones else None

    def fetchall(self):
        return self._many.pop(0) if self._many else []


class CashierStoreTests(unittest.TestCase):
    def test_list_cashiers_public_fields_only(self):
        cur = FakeCursor(many=[[{"id": "c1", "display_name": "Nok", "color": "#f00"}]])
        rows = cashier.list_cashiers(cur, tenant_id="t", workspace_client_id=9)
        sql = cur.calls[0][0]
        self.assertIn("WHERE tenant_id = %s AND workspace_client_id = %s", sql)
        self.assertNotIn("pin_hash", sql)  # 名单绝不带 PIN
        self.assertEqual(rows[0]["display_name"], "Nok")

    def test_get_cashier_includes_pin_hash(self):
        cur = FakeCursor(ones=[{"id": "c1", "pin_hash": "x", "is_active": True}])
        cashier.get_cashier(cur, tenant_id="t", workspace_client_id=9, cashier_id="c1")
        sql, params = cur.calls[0]
        self.assertIn("pin_hash", sql)
        self.assertEqual(params, ("t", 9, "c1"))

    def test_create_cashier_parameterized(self):
        cur = FakeCursor(
            ones=[{"id": "c2", "display_name": "Som", "color": None, "is_active": True}]
        )
        cashier.create_cashier(
            cur, tenant_id="t", workspace_client_id=9, display_name="Som", pin_hash="h"
        )
        sql, params = cur.calls[0]
        self.assertIn("INSERT INTO pos_cashiers", sql)
        self.assertEqual(params, ("t", 9, None, "Som", "h", None))

    def test_get_open_shift_filters_status_open(self):
        cur = FakeCursor(ones=[None])
        cashier.get_open_shift_for_cashier(cur, tenant_id="t", cashier_id="c1")
        sql, params = cur.calls[0]
        self.assertIn("status = 'open'", sql)
        self.assertEqual(params, ("t", "c1"))

    def test_resolve_tenant_for_workspace(self):
        cur = FakeCursor(ones=[{"tenant_id": "t-99"}])
        tid = cashier.resolve_tenant_for_workspace(cur, workspace_client_id=9)
        self.assertEqual(tid, "t-99")
        self.assertIn("FROM workspace_clients WHERE id = %s", cur.calls[0][0])

    def test_resolve_tenant_missing_returns_none(self):
        cur = FakeCursor(ones=[None])
        self.assertIsNone(cashier.resolve_tenant_for_workspace(cur, workspace_client_id=1))


if __name__ == "__main__":
    unittest.main()
