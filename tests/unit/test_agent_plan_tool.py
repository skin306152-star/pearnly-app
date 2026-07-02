# -*- coding: utf-8 -*-
"""plan_incoming_doc 执行器(LI-2)· 计划核验守门。

goals 闭集/互斥、端点/套账名必须对上真实资产(查无退回带真实列表)、
权限闸。存表动作在 write_sink(bridge),这里只验"核验+成形"。
"""

import unittest
from unittest.mock import MagicMock, patch

from services.agent.contracts import AgentContext
from services.agent.executor import AgentToolset

_CTX = AgentContext(user={"id": "u-1", "plan": "credits"}, tenant_id="t-1", line_user_id="Uabc")


class TestPlanIncomingDoc(unittest.TestCase):
    def setUp(self):
        self.ts = AgentToolset()

    def test_goal_validation(self):
        for bad in (None, [], ["fly"], ["record", "fly"], ["nothing", "record"]):
            r = self.ts.plan_incoming_doc(_CTX, goals=bad)
            self.assertFalse(r.ok, bad)
            self.assertEqual(r.error_code, "invalid_goals")
        # 拒绝时喂回合法枚举 → 模型环内自愈,不逼用户重说。
        r = self.ts.plan_incoming_doc(_CTX, goals=["fly"])
        self.assertIn("push", r.data["allowed_goals"])

    def test_goal_aliases_from_real_model(self):
        # prod 真机抓到 gemini 意译枚举(send_to_erp/do_not_record)→ 确定性归一救回。
        r = self.ts.plan_incoming_doc(_CTX, goals=["send_to_erp", "do_not_record"])
        self.assertTrue(r.ok)
        self.assertEqual(r.data["plan"]["goals"], ["push"])
        # 只剩否定记号 = 什么都不做
        r2 = self.ts.plan_incoming_doc(_CTX, goals=["do_not_record"])
        self.assertTrue(r2.ok)
        self.assertEqual(r2.data["plan"]["goals"], [])

    def test_named_endpoint_implies_push(self):
        # prod 真机第二雷:模型只报否定记号+端点名 → 空目标带端点="只推别记"被存成"都不做"。
        # 确定性推断:点名端点=要推;点名套账=要记。
        with patch(
            "services.agent.executor.db.list_erp_endpoints",
            return_value=[{"id": "e1", "name": "MR.ERP TEST2019", "enabled": True}],
        ):
            r = self.ts.plan_incoming_doc(_CTX, goals=["do_not_record"], endpoint_name="MR.ERP")
        self.assertTrue(r.ok)
        self.assertEqual(r.data["plan"]["goals"], ["push"])

    def test_nothing_maps_to_empty_goals(self):
        r = self.ts.plan_incoming_doc(_CTX, goals=["nothing"])
        self.assertTrue(r.ok)
        self.assertEqual(r.data["plan"]["goals"], [])

    def test_push_requires_permission(self):
        with patch(
            "services.agent.executor._plan_permissions", return_value={"can_push_erp": False}
        ):
            r = self.ts.plan_incoming_doc(_CTX, goals=["push"])
        self.assertEqual(r.error_code, "forbidden")

    def test_endpoint_must_match_real_asset(self):
        with patch(
            "services.agent.executor.db.list_erp_endpoints",
            return_value=[{"id": "e1", "name": "MR.ERP TEST2019", "enabled": True}],
        ):
            miss = self.ts.plan_incoming_doc(_CTX, goals=["push"], endpoint_name="SAP")
            hit = self.ts.plan_incoming_doc(_CTX, goals=["push"], endpoint_name="mr.erp")
        self.assertEqual(miss.error_code, "no_endpoint")
        self.assertEqual(miss.data["endpoints"], ["MR.ERP TEST2019"])  # 反问喂真实列表
        self.assertTrue(hit.ok)
        self.assertEqual(hit.data["plan"]["push_to"], "MR.ERP TEST2019")

    def test_workspace_must_match_real_asset(self):
        cur = MagicMock()
        cm = MagicMock()
        cm.__enter__ = MagicMock(return_value=cur)
        cm.__exit__ = MagicMock(return_value=False)
        with (
            patch("services.agent.executor.db.get_cursor_rls", return_value=cm),
            patch("services.line_binding.line_workspace.match_by_name", return_value=None),
            patch("services.line_binding.line_workspace.list_active", return_value=[]),
        ):
            miss = self.ts.plan_incoming_doc(_CTX, goals=["record"], workspace_name="ไม่มีจริง")
        self.assertEqual(miss.error_code, "workspace_not_found")
        with (
            patch("services.agent.executor.db.get_cursor_rls", return_value=cm),
            patch(
                "services.line_binding.line_workspace.match_by_name",
                return_value={"id": 84, "name": "มานะชัย"},
            ),
        ):
            hit = self.ts.plan_incoming_doc(_CTX, goals=["record"], workspace_name="มานะชัย")
        self.assertTrue(hit.ok)
        self.assertEqual(hit.data["plan"]["book_to_id"], 84)


class TestPlanDmsGoal(unittest.TestCase):
    """dms 目标(身份证建 DMS 客户 · LINE-DMS-PUSH-DESIGN):独占、闸 fail-closed、
    端点必须真实存在——绝不存一个到时执行不了的计划。"""

    def setUp(self):
        self.ts = AgentToolset()

    _EP = {"id": "e1", "adapter": "mrerp_dms"}

    def _run(self, goals, *, flag=True, ep=_EP):
        with (
            patch("core.feature_flags.agent_dms_enabled_for", return_value=flag),
            patch("services.erp.dms_id_ocr.resolve_dms_endpoint", return_value=ep),
        ):
            return self.ts.plan_incoming_doc(_CTX, goals=goals)

    def test_dms_goal_and_aliases(self):
        for g in ("dms", "dms_customer", "id_card_to_dms", "create_dms_customer"):
            r = self._run([g])
            self.assertTrue(r.ok, g)
            self.assertEqual(r.data["plan"]["goals"], ["dms"])

    def test_dms_is_exclusive(self):
        r = self._run(["dms", "record"])
        self.assertEqual(r.error_code, "invalid_goals")

    def test_gate_off_fails_closed(self):
        r = self._run(["dms"], flag=False)
        self.assertEqual(r.error_code, "not_available_yet")

    def test_no_dms_endpoint_is_honest(self):
        r = self._run(["dms"], ep=None)
        self.assertEqual(r.error_code, "no_dms_endpoint")

    def test_dms_requires_push_permission(self):
        with (
            patch("core.feature_flags.agent_dms_enabled_for", return_value=True),
            patch(
                "services.agent.executor._plan_permissions",
                return_value={"can_push_erp": False},
            ),
        ):
            r = self.ts.plan_incoming_doc(_CTX, goals=["dms"])
        self.assertEqual(r.error_code, "forbidden")


class TestPlanToolVisibility(unittest.TestCase):
    def test_gate_controls_visibility(self):
        # image 闸开(且写开)才对模型可见;闸关 = 提示词里没有这个工具 = 现状。
        from services.agent.loop import _visible_tools

        on = {t.name for t in _visible_tools(frozenset({"write", "image"}))}
        off = {t.name for t in _visible_tools(frozenset({"write"}))}
        self.assertIn("plan_incoming_doc", on)
        self.assertNotIn("plan_incoming_doc", off)


if __name__ == "__main__":
    unittest.main()
