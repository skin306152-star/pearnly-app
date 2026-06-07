# -*- coding: utf-8 -*-
"""POS 收款设置守门测试(老板后台 · 按账套隔离)。

锁定:
  1. get_settings:无行回落默认 + 读 workspace_clients.promptpay_id;每句按 tenant_id 隔离 + 参数化
  2. save_settings:upsert(ON CONFLICT)+ 回写 workspace_clients.promptpay_id;费率 clamp[0,100]
  3. _clean_rate / _rate_str 边界
  4. 路由契约:GET+PUT 注册 + app 挂载 + owner 守门(收银员 403)+ 模块守门(pos)
"""

import inspect
import unittest
from decimal import Decimal

from services.pos import payment_settings as svc


class FakeCursor:
    def __init__(self, fetch_queue=None):
        self.calls = []
        self._q = list(fetch_queue or [])

    def execute(self, sql, params=None):
        self.calls.append((sql, params))

    def fetchone(self):
        return self._q.pop(0) if self._q else None


class RateHelpersTests(unittest.TestCase):
    def test_clean_rate_clamps(self):
        self.assertEqual(svc._clean_rate("10"), Decimal("10"))
        self.assertEqual(svc._clean_rate(-5), Decimal("0"))
        self.assertEqual(svc._clean_rate(250), Decimal("100"))
        self.assertEqual(svc._clean_rate("oops"), Decimal("0"))

    def test_rate_str_trims(self):
        self.assertEqual(svc._rate_str(Decimal("10.00")), "10")
        self.assertEqual(svc._rate_str(Decimal("8.50")), "8.5")
        self.assertEqual(svc._rate_str(None), "0")


class GetSettingsTests(unittest.TestCase):
    # 第3次 fetchone = _default_service_rate→get_business_type 的哨兵行查询。
    def test_defaults_when_no_row_non_restaurant(self):
        cur = FakeCursor([None, {"promptpay_id": None}, None])  # 业态哨兵 None → 非餐厅
        out = svc.get_settings(cur, tenant_id="t-1", workspace_client_id=7)
        self.assertTrue(out["promptpay_enabled"])
        self.assertTrue(out["card_enabled"])
        self.assertEqual(out["service_charge_rate"], "0")  # 非餐厅默认 0
        self.assertTrue(out["price_includes_vat"])
        self.assertEqual(out["promptpay_id"], "")
        self.assertIn("tenant_id = %s AND workspace_client_id = %s", cur.calls[0][0])
        self.assertEqual(cur.calls[0][1], ("t-1", 7))

    def test_restaurant_default_service_rate_is_10(self):
        # 餐厅业态(哨兵 restaurant)无显式设置 → 服务费智能默认 10%
        cur = FakeCursor([None, {"promptpay_id": None}, {"config": {"value": "restaurant"}}])
        out = svc.get_settings(cur, tenant_id="t-1", workspace_client_id=7)
        self.assertEqual(out["service_charge_rate"], "10")

    def test_reads_explicit_row_and_promptpay(self):
        cur = FakeCursor(
            [
                {
                    "promptpay_enabled": False,
                    "card_enabled": True,
                    "service_charge_rate": Decimal("10.00"),
                    "price_includes_vat": False,
                },
                {"promptpay_id": "0812345678"},
                {"config": {"value": "restaurant"}},  # 业态查询(显式行会覆盖费率,不受默认影响)
            ]
        )
        out = svc.get_settings(cur, tenant_id="t-1", workspace_client_id=7)
        self.assertFalse(out["promptpay_enabled"])
        self.assertEqual(out["service_charge_rate"], "10")
        self.assertFalse(out["price_includes_vat"])
        self.assertEqual(out["promptpay_id"], "0812345678")


class SaveSettingsTests(unittest.TestCase):
    def test_upsert_and_writeback_promptpay_and_clamp(self):
        # save 末尾会调 get_settings(settings + promptpay + 业态哨兵 3 次查询)→ 备好回读结果
        cur = FakeCursor([None, {"promptpay_id": "088"}, None])
        svc.save_settings(
            cur,
            tenant_id="t-1",
            workspace_client_id=7,
            promptpay_enabled=True,
            card_enabled=False,
            service_charge_rate=250,  # 越界 → clamp 100
            price_includes_vat=True,
            promptpay_id="  088  ",
        )
        upsert = cur.calls[0]
        self.assertIn("INSERT INTO pos_payment_settings", upsert[0])
        self.assertIn("ON CONFLICT (tenant_id, workspace_client_id)", upsert[0])
        self.assertEqual(upsert[1][0], "t-1")
        self.assertEqual(upsert[1][1], 7)
        self.assertEqual(upsert[1][4], Decimal("100"))  # 费率 clamp
        writeback = cur.calls[1]
        self.assertIn("UPDATE workspace_clients SET promptpay_id", writeback[0])
        self.assertEqual(writeback[1], ("088", 7, "t-1"))  # trim + 账套 + 租户


class RoutesContractTests(unittest.TestCase):
    def test_router_registers_get_put(self):
        from routes.pos_payment_routes import router

        got = set()
        for r in router.routes:
            for m in getattr(r, "methods", set()) or set():
                if m in ("GET", "PUT"):
                    got.add((m, r.path))
        self.assertEqual(
            got,
            {
                ("GET", "/api/pos/admin/payment-settings"),
                ("PUT", "/api/pos/admin/payment-settings"),
            },
        )

    def test_app_includes_router(self):
        import app

        paths = {r.path for r in app.app.routes if hasattr(r, "path")}
        self.assertIn("/api/pos/admin/payment-settings", paths)

    def test_owner_and_module_gated(self):
        from routes import pos_payment_routes

        src = inspect.getsource(pos_payment_routes)
        self.assertIn('role") == "cashier"', src)  # 收银员 403
        self.assertIn('assert_module_enabled(cur, tid, "pos")', src)  # 模块守门
        self.assertIn("require_workspace", src)  # 账套归属


if __name__ == "__main__":
    unittest.main()
