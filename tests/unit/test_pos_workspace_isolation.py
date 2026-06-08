# -*- coding: utf-8 -*-
"""POS 套账隔离 + 强制开班守门(POS-RO-002 / RO-003 · 不连库 · 纯函数/假游标)。

RO-003:POS 单据/商品/单位查询必须带 workspace_client_id,否则同 tenant 多套账下知道 id/票号
即可跨套账读取。RO-002:缺 open 班次不许卖货(现金责任链)。真库行为由 docs/pos/_e2e_isolation.py
覆盖,本文件是 CI 常驻的轻量断言(防回归)。"""

import unittest

from core.pos_api import PosError
from services.pos import sale, sales_store
from services.pos.restaurant import checkout as rcheckout
from services.pos.restaurant import store as rstore


class _Cur:
    def __init__(self, ones=None):
        self.calls = []
        self._ones = list(ones or [])

    def execute(self, sql, params=None):
        self.calls.append((sql, params))

    def fetchone(self):
        return self._ones.pop(0) if self._ones else None

    def fetchall(self):
        return []


class WorkspaceFilterTests(unittest.TestCase):
    """每个查询的 SQL 必含 workspace_client_id 且 ws 值进参数(参数化)。"""

    def _assert_ws_filtered(self, call):
        cur = _Cur(ones=[None])
        call(cur)
        sql, params = cur.calls[-1]
        self.assertIn("workspace_client_id", sql, sql)
        self.assertIn(7, params, params)

    def test_get_sale(self):
        self._assert_ws_filtered(
            lambda c: sales_store.get_sale(c, tenant_id="t", workspace_client_id=7, sale_id="s")
        )

    def test_get_sale_by_receipt(self):
        self._assert_ws_filtered(
            lambda c: sales_store.get_sale_by_receipt(
                c, tenant_id="t", workspace_client_id=7, receipt_no="R-1"
            )
        )

    def test_find_sale_by_client_uuid(self):
        self._assert_ws_filtered(
            lambda c: sales_store.find_sale_by_client_uuid(
                c, tenant_id="t", workspace_client_id=7, client_uuid="cu"
            )
        )

    def test_get_product_for_sale(self):
        self._assert_ws_filtered(
            lambda c: sales_store.get_product_for_sale(
                c, tenant_id="t", workspace_client_id=7, product_id="p"
            )
        )

    def test_get_unit_factor(self):
        self._assert_ws_filtered(
            lambda c: sales_store.get_unit_factor(
                c, tenant_id="t", workspace_client_id=7, product_id="p", unit_name="box"
            )
        )

    def test_restaurant_get_menu_product(self):
        self._assert_ws_filtered(
            lambda c: rstore.get_menu_product(
                c, tenant_id="t", workspace_client_id=7, product_id="p"
            )
        )


class ShiftRequiredTests(unittest.TestCase):
    """RO-002:缺 shift_id → pos.shift_closed;非 open → 拒;open → 放行。零售+餐厅一致。"""

    def _assert_funcs(self):
        return (sale._assert_shift_open, rcheckout._assert_shift_open)

    def test_missing_shift_rejected(self):
        for fn in self._assert_funcs():
            cur = _Cur()
            with self.assertRaises(PosError) as ctx:
                fn(cur, tenant_id="t", shift_id=None)
            self.assertEqual(ctx.exception.code, "pos.shift_closed")
            self.assertEqual(len(cur.calls), 0)  # 缺 shift 直接拒,不查库

    def test_closed_shift_rejected(self):
        for fn in self._assert_funcs():
            cur = _Cur(ones=[{"status": "closed"}])
            with self.assertRaises(PosError) as ctx:
                fn(cur, tenant_id="t", shift_id="sh")
            self.assertEqual(ctx.exception.code, "pos.shift_closed")

    def test_open_shift_passes(self):
        for fn in self._assert_funcs():
            cur = _Cur(ones=[{"status": "open"}])
            fn(cur, tenant_id="t", shift_id="sh")  # 不抛即通过


if __name__ == "__main__":
    unittest.main()
