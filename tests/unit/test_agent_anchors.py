# -*- coding: utf-8 -*-
"""跨轮锚点采集/消费(services/agent/anchors)+ _locate_doc 守门。

三条守门:锚点优先(不再落最近一张)、锚点失效复核回落、带 keyword 不认锚。
采集侧:闸关 no-op、多命中不锚(不替用户猜)、push 备料锚单据+端点。
"""

import unittest
from unittest.mock import patch

from services.agent import anchors
from services.agent.contracts import AgentContext, ToolResult
from services.agent.executor import AgentToolset


def _ctx(anchor_id=None, enabled=True):
    return AgentContext(
        user={"id": "u1", "tenant_id": "t1", "plan": "pro"},
        tenant_id="t1",
        anchors={"last_history_id": anchor_id} if anchor_id else {},
        anchors_enabled=enabled,
    )


class TestCollect(unittest.TestCase):
    def test_gate_off_is_noop(self):
        ctx = _ctx(enabled=False)
        r = ToolResult(ok=True, data={"items": [{"id": "h1"}], "total": 1})
        anchors.collect(ctx, "list_history", r)
        self.assertEqual(ctx.anchors, {})

    def test_single_hit_list_anchors(self):
        ctx = _ctx()
        r = ToolResult(ok=True, data={"items": [{"id": "h1"}], "total": 1})
        anchors.collect(ctx, "list_history", r)
        self.assertEqual(ctx.anchors["last_history_id"], "h1")

    def test_multi_hit_list_does_not_anchor(self):
        # 多命中=用户还没挑,锚了就是替用户猜(绝不猜红线)。
        ctx = _ctx()
        r = ToolResult(ok=True, data={"items": [{"id": "h1"}, {"id": "h2"}], "total": 2})
        anchors.collect(ctx, "list_history", r)
        self.assertNotIn("last_history_id", ctx.anchors)

    def test_failed_result_does_not_anchor(self):
        ctx = _ctx()
        anchors.collect(ctx, "list_history", ToolResult(ok=False, data={"items": [{"id": "h1"}]}))
        self.assertEqual(ctx.anchors, {})

    def test_push_prepare_anchors_doc_and_endpoint(self):
        ctx = _ctx()
        r = ToolResult(ok=True, data={"push": {"history_id": "h7", "endpoint_id": "e2"}})
        anchors.collect(ctx, "push_to_erp", r)
        self.assertEqual(ctx.anchors["last_history_id"], "h7")
        self.assertEqual(ctx.anchors["last_pushed_endpoint_id"], "e2")


class TestResolveHistory(unittest.TestCase):
    def test_live_doc_resolves(self):
        with (
            patch("core.db.get_ocr_history_detail", return_value={"id": "h9", "client_id": None}),
            patch("core.db.get_visible_client_ids_for_user", return_value=None),
        ):
            doc = anchors.resolve_history(_ctx("h9"))
        self.assertEqual(doc["id"], "h9")

    def test_deleted_doc_returns_none(self):
        with patch("core.db.get_ocr_history_detail", return_value=None):
            self.assertIsNone(anchors.resolve_history(_ctx("h9")))

    def test_invisible_client_rejected(self):
        # 员工限定名单外的客户单不认锚(镜像 list_ocr_history 可见性口径)。
        with (
            patch("core.db.get_ocr_history_detail", return_value={"id": "h9", "client_id": 5}),
            patch("core.db.get_visible_client_ids_for_user", return_value=[1, 2]),
        ):
            self.assertIsNone(anchors.resolve_history(_ctx("h9")))

    def test_no_anchor_returns_none(self):
        self.assertIsNone(anchors.resolve_history(_ctx()))


class TestLocateDocGuards(unittest.TestCase):
    def setUp(self):
        self.ts = AgentToolset()
        patch(
            "services.agent.executor._plan_permissions",
            return_value={"can_view_history": True, "history_retention_days": 365},
        ).start()
        self.addCleanup(patch.stopall)

    def test_anchor_takes_priority_over_latest(self):
        with (
            patch("core.db.get_ocr_history_detail", return_value={"id": "h9", "client_id": None}),
            patch("core.db.get_visible_client_ids_for_user", return_value=None),
            patch("core.db.list_ocr_history") as lst,
        ):
            hist, fail = self.ts._locate_doc(_ctx("h9"), None)
        self.assertIsNone(fail)
        self.assertEqual(hist["id"], "h9")
        lst.assert_not_called()  # 锚点命中不再查列表(最近一张让位)

    def test_dead_anchor_falls_back_to_latest(self):
        with (
            patch("core.db.get_ocr_history_detail", return_value=None),
            patch("core.db.get_visible_client_ids_for_user", return_value=None),
            patch(
                "core.db.list_ocr_history",
                return_value={"items": [{"id": "h1", "seller_name": "7-11"}], "total": 1},
            ),
        ):
            hist, fail = self.ts._locate_doc(_ctx("h9"), None)
        self.assertIsNone(fail)
        self.assertEqual(hist["id"], "h1")

    def test_keyword_ignores_anchor(self):
        with (
            patch("core.db.get_ocr_history_detail") as detail,
            patch("core.db.get_visible_client_ids_for_user", return_value=None),
            patch(
                "core.db.list_ocr_history",
                return_value={"items": [{"id": "h1", "seller_name": "7-11"}], "total": 1},
            ),
        ):
            hist, fail = self.ts._locate_doc(_ctx("h9"), "7-11")
        self.assertIsNone(fail)
        self.assertEqual(hist["id"], "h1")
        detail.assert_not_called()


if __name__ == "__main__":
    unittest.main()
