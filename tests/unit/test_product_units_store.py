# -*- coding: utf-8 -*-
"""product_units DAL 守门测试(POS 项目 · PO-A2)。

锁定:
  1. 每条语句按 tenant_id + product_id 隔离 + 全参数化(值不入 SQL 串)
  2. numeric(factor_to_base/price)经 Decimal 存(不 float)
  3. 设默认单位前先清同商品其它默认(单一默认)
  4. delete 是硬删(product_units 无引用历史)
"""

import unittest
from decimal import Decimal

from services.products import units as dal


class FakeCursor:
    def __init__(self, fetchone=None, fetchall=None, rowcount=1):
        self.calls = []
        self._fetchone = fetchone
        self._fetchall = fetchall or []
        self.rowcount = rowcount

    def execute(self, sql, params=None):
        self.calls.append((sql, params))

    def fetchone(self):
        return self._fetchone

    def fetchall(self):
        return self._fetchall

    @property
    def last_sql(self):
        return self.calls[-1][0]

    @property
    def last_params(self):
        return self.calls[-1][1]


ROW = {
    "id": "u1",
    "tenant_id": "t-1",
    "product_id": "p-1",
    "unit_name": "กล่อง",
    "factor_to_base": Decimal("100.000"),
    "barcode": "8850",
    "price": Decimal("90.00"),
    "is_default_sell": False,
    "created_at": None,
    "updated_at": None,
}


class UnitsIsolationTests(unittest.TestCase):
    def test_every_statement_scopes_to_tenant_and_product(self):
        for fn in (
            lambda c: dal.list_units(c, tenant_id="t-1", workspace_client_id=7, product_id="p-1"),
            lambda c: dal.get_unit(
                c, tenant_id="t-1", workspace_client_id=7, product_id="p-1", unit_id="u1"
            ),
            lambda c: dal.update_unit(
                c,
                tenant_id="t-1",
                workspace_client_id=7,
                product_id="p-1",
                unit_id="u1",
                fields={"barcode": "x"},
            ),
            lambda c: dal.delete_unit(
                c, tenant_id="t-1", workspace_client_id=7, product_id="p-1", unit_id="u1"
            ),
        ):
            cur = FakeCursor(fetchone=ROW, fetchall=[ROW])
            fn(cur)
            self.assertIn("tenant_id = %s", cur.last_sql)
            self.assertIn("workspace_client_id = %s", cur.last_sql)
            self.assertIn("product_id = %s", cur.last_sql)
            self.assertIn("t-1", cur.last_params)
            self.assertIn(7, cur.last_params)
            self.assertIn("p-1", cur.last_params)


class CreateUnitTests(unittest.TestCase):
    def test_insert_parameterized_and_decimal(self):
        cur = FakeCursor(fetchone=ROW)
        dal.create_unit(
            cur,
            tenant_id="t-1",
            workspace_client_id=7,
            product_id="p-1",
            fields={"unit_name": "กล่อง", "factor_to_base": 100, "price": 90},
        )
        self.assertIn("INSERT INTO product_units", cur.last_sql)
        self.assertIn("RETURNING", cur.last_sql)
        self.assertEqual(cur.last_params[0], "t-1")
        self.assertEqual(cur.last_params[1], 7)
        self.assertEqual(cur.last_params[2], "p-1")
        # numeric 走 Decimal · 值不拼进 SQL
        self.assertIn(Decimal("100"), cur.last_params)
        self.assertIn(Decimal("90"), cur.last_params)
        self.assertNotIn("กล่อง", cur.last_sql)

    def test_default_sell_clears_others_first(self):
        cur = FakeCursor(fetchone=ROW)
        dal.create_unit(
            cur,
            tenant_id="t-1",
            workspace_client_id=7,
            product_id="p-1",
            fields={"unit_name": "ขวด", "factor_to_base": 1, "is_default_sell": True},
        )
        # 第一条语句应是清旧默认,再 INSERT
        self.assertIn("is_default_sell = FALSE", cur.calls[0][0])
        self.assertIn("INSERT INTO product_units", cur.calls[1][0])

    def test_non_default_skips_clear(self):
        cur = FakeCursor(fetchone=ROW)
        dal.create_unit(
            cur,
            tenant_id="t-1",
            workspace_client_id=7,
            product_id="p-1",
            fields={"unit_name": "ขวด", "factor_to_base": 1},
        )
        self.assertNotIn("is_default_sell = FALSE", cur.calls[0][0])


class UpdateDeleteTests(unittest.TestCase):
    def test_update_no_fields_returns_current(self):
        cur = FakeCursor(fetchone=ROW)
        dal.update_unit(
            cur, tenant_id="t-1", workspace_client_id=7, product_id="p-1", unit_id="u1", fields={}
        )
        # 空更新走 get_unit(SELECT),不发 UPDATE
        self.assertIn("SELECT", cur.last_sql)
        self.assertNotIn("UPDATE", cur.last_sql)

    def test_delete_is_hard_delete(self):
        cur = FakeCursor(rowcount=1)
        ok = dal.delete_unit(
            cur, tenant_id="t-1", workspace_client_id=7, product_id="p-1", unit_id="u1"
        )
        self.assertTrue(ok)
        self.assertIn("DELETE FROM product_units", cur.last_sql)


if __name__ == "__main__":
    unittest.main()
