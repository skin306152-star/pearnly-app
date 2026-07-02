# -*- coding: utf-8 -*-
"""M4 只读工具单测(push_status / rd_lookup / my_plan)+ 观测/兜底覆盖。

钱与状态诚实红线:failed/未推绝不算 pushed;RD 查无此号是诚实结果不是报错;
套餐读订阅失败不挡基础信息。
"""

import unittest
from unittest.mock import patch

from services.agent import fallbacks, observe
from services.agent.contracts import AgentContext, ToolResult
from services.agent.executor import AgentToolset

_CTX = AgentContext(user={"id": "u1", "tenant_id": "t1", "plan": "pro"}, tenant_id="t1")


def _hist(items):
    return {"items": items, "total": len(items)}


class TestPushStatus(unittest.TestCase):
    def setUp(self):
        self.ts = AgentToolset()
        self.perms = patch(
            "services.agent.executor._plan_permissions",
            return_value={
                "can_push_erp": True,
                "can_view_history": True,
                "history_retention_days": 365,
            },
        )
        self.perms.start()
        self.addCleanup(self.perms.stop)
        patch("core.db.get_visible_client_ids_for_user", return_value=None).start()
        self.addCleanup(patch.stopall)

    def test_pushed_success(self):
        with (
            patch(
                "core.db.list_ocr_history",
                return_value=_hist([{"id": "h1", "seller_name": "7-11", "total_amount": 120}]),
            ),
            patch(
                "core.db.list_push_logs",
                return_value={
                    "items": [
                        {
                            "status": "success",
                            "endpoint_name": "MR.ERP",
                            "created_at": "2026-07-01",
                            "error_msg": None,
                        }
                    ]
                },
            ),
            patch("core.db.counts_as_endpoint_success", return_value=True),
        ):
            res = self.ts.get_push_status(_CTX, keyword="7-11")
        self.assertTrue(res.ok)
        self.assertTrue(res.data["pushed"])
        self.assertEqual(res.data["endpoint"], "MR.ERP")

    def test_failed_is_not_pushed(self):
        # 状态诚实红线:failed 绝不显示成已推送。
        with (
            patch(
                "core.db.list_ocr_history",
                return_value=_hist([{"id": "h1", "seller_name": "7-11", "total_amount": 120}]),
            ),
            patch(
                "core.db.list_push_logs",
                return_value={"items": [{"status": "failed", "error_msg": "ERR_NO_CLIENT"}]},
            ),
            patch("core.db.counts_as_endpoint_success", return_value=False),
        ):
            res = self.ts.get_push_status(_CTX, keyword="7-11")
        self.assertTrue(res.ok)
        self.assertFalse(res.data["pushed"])
        self.assertEqual(res.data["status"], "failed")

    def test_never_pushed(self):
        with (
            patch("core.db.list_ocr_history", return_value=_hist([{"id": "h1"}])),
            patch("core.db.list_push_logs", return_value={"items": []}),
        ):
            res = self.ts.get_push_status(_CTX)
        self.assertTrue(res.ok)
        self.assertFalse(res.data["pushed"])
        self.assertEqual(res.data["status"], "never_pushed")

    def test_ambiguous_returns_candidates(self):
        with patch(
            "core.db.list_ocr_history",
            return_value=_hist(
                [{"id": "h1", "seller_name": "A"}, {"id": "h2", "seller_name": "B"}]
            ),
        ):
            res = self.ts.get_push_status(_CTX, keyword="บิล")
        self.assertFalse(res.ok)
        self.assertEqual(res.error_code, "ambiguous_doc")
        self.assertEqual(len(res.data["candidates"]), 2)

    def test_not_found(self):
        with patch("core.db.list_ocr_history", return_value=_hist([])):
            res = self.ts.get_push_status(_CTX, keyword="ghost")
        self.assertEqual(res.error_code, "history_not_found")

    def test_no_permission_forbidden(self):
        with patch(
            "services.agent.executor._plan_permissions", return_value={"can_push_erp": False}
        ):
            res = self.ts.get_push_status(_CTX)
        self.assertEqual(res.error_code, "forbidden")


class TestRdLookup(unittest.TestCase):
    def test_found(self):
        payload = {"tax_id": "0105561234567", "name": "บริษัท ทดสอบ จำกัด", "province": "กรุงเทพ"}
        with patch("services.rd.rd_api.lookup_vat", return_value={"ok": True, "data": payload}):
            res = AgentToolset().rd_lookup(_CTX, tax_id="0105561234567")
        self.assertTrue(res.ok)
        self.assertEqual(res.data["name"], "บริษัท ทดสอบ จำกัด")

    def test_not_found_honest(self):
        with patch(
            "services.rd.rd_api.lookup_vat", return_value={"ok": False, "error": "not_found"}
        ):
            res = AgentToolset().rd_lookup(_CTX, tax_id="0105561234567")
        self.assertEqual(res.error_code, "rd_not_found")

    def test_invalid_format(self):
        with patch(
            "services.rd.rd_api.lookup_vat", return_value={"ok": False, "error": "invalid_format"}
        ):
            res = AgentToolset().rd_lookup(_CTX, tax_id="123")
        self.assertEqual(res.error_code, "rd_invalid_tax_id")


class TestMyPlan(unittest.TestCase):
    def test_with_subscription(self):
        with (
            patch(
                "core.db.get_billing_status_combined",
                return_value={"balance_thb": 88.5},
            ),
            patch(
                "services.billing.subscription.get_active_subscription",
                return_value={"plan_key": "M", "current_period_end": "2026-07-20"},
            ),
        ):
            res = AgentToolset().get_my_plan(_CTX)
        self.assertTrue(res.ok)
        self.assertEqual(res.data["plan"], "pro")
        self.assertEqual(res.data["subscription"]["plan"], "M")

    def test_subscription_error_does_not_block(self):
        with (
            patch("core.db.get_billing_status_combined", return_value={"balance_thb": 1}),
            patch(
                "services.billing.subscription.get_active_subscription",
                side_effect=RuntimeError("db down"),
            ),
        ):
            res = AgentToolset().get_my_plan(_CTX)
        self.assertTrue(res.ok)
        self.assertIsNone(res.data["subscription"])


class TestObserveAndFallback(unittest.TestCase):
    def test_push_status_observation_trims_error(self):
        r = ToolResult(ok=True, data={"pushed": False, "status": "failed", "error": "x" * 500})
        obs = observe.payload("push_status", r)
        self.assertLessEqual(len(obs["error"]), 160)

    def test_push_status_failure_carries_candidates(self):
        r = ToolResult(ok=False, error_code="ambiguous_doc", data={"candidates": [{"vendor": "A"}]})
        obs = observe.payload("push_status", r)
        self.assertFalse(obs["ok"])
        self.assertEqual(len(obs["candidates"]), 1)

    def test_fallback_push_yes_no(self):
        yes = fallbacks.grounded_fallback(
            [{"tool": "push_status", "ok": True, "pushed": True, "endpoint": "MR.ERP"}], "th"
        )
        no = fallbacks.grounded_fallback(
            [{"tool": "push_status", "ok": True, "pushed": False, "endpoint": ""}], "zh"
        )
        self.assertIn("MR.ERP", yes)
        self.assertIn("还没", no)

    def test_fallback_push_not_ok_returns_none(self):
        out = fallbacks.grounded_fallback(
            [{"tool": "push_status", "ok": False, "error": "ambiguous_doc"}], "th"
        )
        self.assertIsNone(out)

    def test_fallback_plan_and_rd(self):
        plan = fallbacks.grounded_fallback([{"tool": "my_plan", "ok": True, "plan": "M"}], "en")
        rd = fallbacks.grounded_fallback(
            [{"tool": "rd_lookup", "ok": True, "tax_id": "0105561234567", "name": "ACME"}], "th"
        )
        self.assertIn("M", plan)
        self.assertIn("ACME", rd)


if __name__ == "__main__":
    unittest.main()
