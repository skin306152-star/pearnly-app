# -*- coding: utf-8 -*-
"""开通收银编排守门测试(POS 项目 · PO-B1)。

锁定:开 inventory+pos 两模块 · pos.config 写业态预设能力块 · 建默认仓/终端 · 建首位收银员
(PIN 经 hash 非明文)· first_cashier 缺省时不建收银员。依赖以 monkeypatch 隔离(纯编排单测)。"""

import unittest

from services.pos import onboarding


class _Recorder:
    def __init__(self):
        self.modules = {}
        self.cashiers = []
        self.warehouses = []
        self.terminals = 0

    def set_module(self, cur, *, tenant_id, module_key, enabled, config=None):
        self.modules[module_key] = {"enabled": enabled, "config": config}
        return {"module_key": module_key, "enabled": enabled, "config": config or {}}

    def get_or_create_default_warehouse(self, cur, *, tenant_id, workspace_client_id, name=None):
        self.warehouses.append(name)
        return {"id": 1, "name": name or "ร้าน"}

    def get_or_create_default_terminal(self, cur, *, tenant_id, workspace_client_id):
        self.terminals += 1
        return {"id": 1}

    def create_cashier(
        self, cur, *, tenant_id, workspace_client_id, display_name, pin_hash, color=None
    ):
        self.cashiers.append({"display_name": display_name, "pin_hash": pin_hash})
        return {"id": "new-cashier"}


class OnboardingTests(unittest.TestCase):
    def setUp(self):
        self.rec = _Recorder()
        self._saved = (
            onboarding.modules_store.set_module,
            onboarding.inventory_store.get_or_create_default_warehouse,
            onboarding.cashier_dal.get_or_create_default_terminal,
            onboarding.cashier_dal.create_cashier,
        )
        onboarding.modules_store.set_module = self.rec.set_module
        onboarding.inventory_store.get_or_create_default_warehouse = (
            self.rec.get_or_create_default_warehouse
        )
        onboarding.cashier_dal.get_or_create_default_terminal = (
            self.rec.get_or_create_default_terminal
        )
        onboarding.cashier_dal.create_cashier = self.rec.create_cashier

    def tearDown(self):
        (
            onboarding.modules_store.set_module,
            onboarding.inventory_store.get_or_create_default_warehouse,
            onboarding.cashier_dal.get_or_create_default_terminal,
            onboarding.cashier_dal.create_cashier,
        ) = self._saved

    def test_pharmacy_enables_modules_and_capabilities(self):
        out = onboarding.onboard(
            None,
            tenant_id="t",
            workspace_client_id=9,
            business_type="pharmacy",
            warehouse_name="ร้านยา",
            first_cashier={"display_name": "Nok", "pin": "1234"},
        )
        self.assertTrue(self.rec.modules["inventory"]["enabled"])
        self.assertTrue(self.rec.modules["pos"]["enabled"])
        cfg = self.rec.modules["pos"]["config"]
        self.assertEqual(cfg["business_type"], "pharmacy")
        self.assertTrue(cfg["track_batch"])
        self.assertTrue(cfg["track_expiry"])
        self.assertIn("track_batch", out["capabilities"])
        self.assertEqual(out["enabled_modules"], ["inventory", "pos"])
        self.assertEqual(out["cashier_id"], "new-cashier")
        self.assertEqual(self.rec.warehouses, ["ร้านยา"])
        self.assertEqual(self.rec.terminals, 1)

    def test_pin_is_hashed_not_plaintext(self):
        onboarding.onboard(
            None,
            tenant_id="t",
            workspace_client_id=9,
            business_type="retail",
            first_cashier={"display_name": "Som", "pin": "4321"},
        )
        self.assertNotEqual(self.rec.cashiers[0]["pin_hash"], "4321")

    def test_unknown_business_type_falls_back_to_retail(self):
        out = onboarding.onboard(
            None, tenant_id="t", workspace_client_id=9, business_type="spaceship"
        )
        self.assertEqual(out["capabilities"], onboarding.BUSINESS_PRESETS["retail"])

    def test_no_first_cashier_skips_creation(self):
        out = onboarding.onboard(None, tenant_id="t", workspace_client_id=9, business_type="retail")
        self.assertIsNone(out["cashier_id"])
        self.assertEqual(self.rec.cashiers, [])


if __name__ == "__main__":
    unittest.main()
