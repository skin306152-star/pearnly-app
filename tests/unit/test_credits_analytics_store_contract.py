# -*- coding: utf-8 -*-
"""REFACTOR-B2 守门 · credits 只读分析 DAL 抽取契约

锁定:
  1. 4 个只读分析函数从 services.credits.store 提供,db.py 经 re-export 暴露同一对象
     (admin_cost_routes/admin_users_routes 走 db.x 零改动)。
  2. 纯结构性 0 逻辑改 + 跨域 _bkk_year_month 走 db.*:异常兜底(查库出错→返默认空)
     经 mock.patch("db.get_cursor") 仍生效。
  3. 钱路径仍在 db.py(charge_ocr / charge_ocr_async 未搬)。
"""

import unittest
from unittest import mock

import db
from services.credits import store


class CreditsAnalyticsReexportContract(unittest.TestCase):
    def test_funcs_reexported_same_object(self):
        for n in [
            "get_credits_revenue_overview",
            "get_tenants_credits_summary",
            "get_tenant_credit_summary",
            "get_credits_daily_trend",
        ]:
            self.assertTrue(hasattr(store, n), f"service missing {n}")
            self.assertIs(
                getattr(db, n), getattr(store, n), f"db.{n} not re-exporting service object"
            )

    def test_charge_ocr_now_in_services_billing_charge(self):
        # 旧守门曾断言「钱路径不出 db」· REFACTOR-B2 第 24 轮已迁 services/billing/charge
        # (spec 11+16 E2E 兜底)· db.charge_ocr 仍可调(re-export 同对象 · 调用点零改动)
        self.assertEqual(db.charge_ocr.__module__, "services.billing.charge")
        self.assertEqual(db.charge_ocr_async.__module__, "services.billing.charge")


class CreditsAnalyticsBehaviorContract(unittest.TestCase):
    def test_trend_returns_empty_list_on_db_error(self):
        with mock.patch("db.get_cursor", side_effect=RuntimeError("boom")):
            self.assertEqual(store.get_credits_daily_trend(days=7), [])

    def test_tenants_summary_returns_empty_list_on_db_error(self):
        with mock.patch("db.get_cursor", side_effect=RuntimeError("boom")):
            self.assertEqual(store.get_tenants_credits_summary(limit=10), [])


if __name__ == "__main__":
    unittest.main()
