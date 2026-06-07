# -*- coding: utf-8 -*-
"""开通状态聚合纯逻辑守门测试(POS 项目 · C3)。

不连库(stub get_modules + 计数/存在性查询):onboarded 判定(pos 开 + 有仓 + 有收银员三者
皆备才 true)、业态/能力块从 pos config 读出。真库聚合由 _e2e_c3 覆盖。"""

import unittest
from unittest import mock

from services.pos import onboarding


class _Cur:
    """按 execute 顺序回放:第 1 句收银员计数、第 2 句仓存在性。"""

    def __init__(self, cashier_n, has_wh):
        self._results = [{"n": cashier_n}, ({"x": 1} if has_wh else None)]
        self._i = -1

    def execute(self, sql, params=None):
        self._i += 1

    def fetchone(self):
        return self._results[self._i]


def _modules(pos_on, inv_on, cfg):
    return {
        "pos": {"enabled": pos_on, "config": cfg},
        "inventory": {"enabled": inv_on, "config": {}},
    }


class OnboardingStateTests(unittest.TestCase):
    def test_fully_onboarded(self):
        cfg = {"business_type": "pharmacy", "track_batch": True, "multi_unit": True}
        with mock.patch.object(
            onboarding.modules_store, "get_modules", return_value=_modules(True, True, cfg)
        ):
            st = onboarding.get_state(_Cur(2, True), tenant_id="t", workspace_client_id=9)
        self.assertTrue(st["onboarded"])
        self.assertEqual(st["business_type"], "pharmacy")
        self.assertIn("track_batch", st["capabilities"])
        self.assertEqual(st["cashier_count"], 2)
        self.assertTrue(st["has_warehouse"])

    def test_pos_off_not_onboarded(self):
        with mock.patch.object(
            onboarding.modules_store, "get_modules", return_value=_modules(False, False, {})
        ):
            st = onboarding.get_state(_Cur(0, False), tenant_id="t", workspace_client_id=9)
        self.assertFalse(st["onboarded"])
        self.assertIsNone(st["business_type"])

    def test_pos_on_but_no_cashier_not_onboarded(self):
        cfg = {"business_type": "retail", "multi_unit": True}
        with mock.patch.object(
            onboarding.modules_store, "get_modules", return_value=_modules(True, True, cfg)
        ):
            st = onboarding.get_state(_Cur(0, True), tenant_id="t", workspace_client_id=9)
        self.assertFalse(st["onboarded"])  # 有仓无收银员 → 未完成
        self.assertEqual(st["business_type"], "retail")

    def test_capabilities_only_those_enabled_in_config(self):
        # pharmacy 预设有 4 能力块,但 config 只开了 multi_unit → 只返回 multi_unit
        cfg = {"business_type": "pharmacy", "multi_unit": True}
        with mock.patch.object(
            onboarding.modules_store, "get_modules", return_value=_modules(True, True, cfg)
        ):
            st = onboarding.get_state(_Cur(1, True), tenant_id="t", workspace_client_id=9)
        self.assertEqual(st["capabilities"], ["multi_unit"])


if __name__ == "__main__":
    unittest.main()
