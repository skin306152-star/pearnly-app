# -*- coding: utf-8 -*-
"""前门意图闭集单一事实源(services/front_desk/intents.py · FD-0a)。

锁:①首发只开 monthly_vat,四意图在册但 enabled=False;②闭集边界(枚举内/外);③执行计划
映射到工单 intent;④UNSUPPORTED 哨兵永不进注册表(拒绝卡靠它,不冒充意图)。
"""

import unittest

from services.front_desk import intents


class IntentClosedSetTests(unittest.TestCase):
    def test_only_monthly_vat_enabled_on_launch(self):
        self.assertEqual(intents.enabled_ids(), ("monthly_vat",))

    def test_four_intents_registered_but_disabled(self):
        for iid in ("digitize", "vat_report_check", "payroll_filing", "bank_match"):
            self.assertTrue(intents.is_known(iid), f"{iid} 应在册")
            self.assertFalse(intents.is_enabled(iid), f"{iid} 首发应未开放")

    def test_unsupported_sentinel_never_in_registry(self):
        self.assertFalse(intents.is_known(intents.UNSUPPORTED))
        self.assertNotIn(intents.UNSUPPORTED, intents.ALL_IDS)
        self.assertIsNone(intents.get(intents.UNSUPPORTED))

    def test_unknown_intent_is_neither_known_nor_enabled(self):
        for junk in (None, "", "pnd50", "chitchat"):
            self.assertFalse(intents.is_known(junk))
            self.assertFalse(intents.is_enabled(junk))

    def test_monthly_vat_execution_plan_maps_to_work_order_intent(self):
        m = intents.get("monthly_vat")
        self.assertIsNotNone(m)
        self.assertEqual(m.work_order_intent, "monthly_vat")
        self.assertTrue(m.enabled)
        self.assertTrue(m.name_key.startswith("fd.intent."))
        self.assertTrue(m.deliverables and m.needs)

    def test_all_ids_covers_full_closed_set(self):
        self.assertEqual(
            set(intents.ALL_IDS),
            {"monthly_vat", "digitize", "vat_report_check", "payroll_filing", "bank_match"},
        )


if __name__ == "__main__":
    unittest.main()
