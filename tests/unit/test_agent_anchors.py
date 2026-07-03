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


def _img_ctx(doc_id="d9", ws=6):
    return AgentContext(
        user={"id": "u1", "tenant_id": "t1", "plan": "pro"},
        tenant_id="t1",
        workspace_client_id=ws,
        anchors={"last_image_doc_id": doc_id, "last_image_doc_ws": ws},
        anchors_enabled=True,
    )


class TestRecordImageDocs(unittest.TestCase):
    """图片路锚点挂钩(真机雷:发图后「推它」命中旧载体 PS2-0702 → 必须锚定刚扫那张)。"""

    def test_single_ingest_anchors_and_clears_history_key(self):
        with (
            patch("core.feature_flags.agent_anchor_enabled_for", return_value=True),
            patch(
                "services.line_binding.line_anchor_store.get_anchors",
                return_value={"last_history_id": "old"},
            ),
            patch("services.line_binding.line_anchor_store.set_anchors") as set_a,
        ):
            anchors.record_image_docs({"id": "u1"}, "t1", "U1", [{"doc_id": "d9"}], 6)
        stored = set_a.call_args.args[2]
        self.assertEqual(stored["last_image_doc_id"], "d9")
        self.assertEqual(stored["last_image_doc_ws"], 6)
        self.assertNotIn("last_history_id", stored)  # 新图接管指代

    def test_multiple_ingests_do_not_anchor(self):
        with (
            patch("core.feature_flags.agent_anchor_enabled_for", return_value=True),
            patch("services.line_binding.line_anchor_store.set_anchors") as set_a,
        ):
            anchors.record_image_docs(
                {"id": "u1"}, "t1", "U1", [{"doc_id": "d1"}, {"doc_id": "d2"}], 6
            )
        set_a.assert_not_called()

    def test_gate_off_is_noop(self):
        with (
            patch("core.feature_flags.agent_anchor_enabled_for", return_value=False) as flag,
            patch("services.line_binding.line_anchor_store.set_anchors") as set_a,
        ):
            anchors.record_image_docs({"id": "u1"}, "t1", "U1", [{"doc_id": "d9"}], 6)
        flag.assert_called_once()
        set_a.assert_not_called()

    def test_failure_swallowed(self):
        with patch("core.feature_flags.agent_anchor_enabled_for", side_effect=RuntimeError):
            anchors.record_image_docs({"id": "u1"}, "t1", "U1", [{"doc_id": "d9"}], 6)  # 不抛即过


class TestResolveImageDoc(unittest.TestCase):
    def _detail(self, status):
        return {"doc": {"id": "d9", "status": status}}

    def test_draft_doc_resolves_via_carrier(self):
        hist = {
            "id": "c1",
            "invoice_no": "IV69/00179",
            "seller_name": "Sincere",
            "total_amount": "2889",
        }
        with (
            patch("core.db.get_cursor_rls"),
            patch("services.purchase.docs.get_doc", return_value=self._detail("draft")),
            patch(
                "services.agent.doc_fallback.carrier_hist_for_detail", return_value=hist
            ) as carrier,
        ):
            out = anchors.resolve_history(_img_ctx(), allow_carrier_insert=True)
        self.assertEqual(out["id"], "c1")
        self.assertTrue(carrier.call_args.kwargs["insert"])

    def test_discarded_doc_rejected(self):
        # ทิ้ง 掉的死单不认锚 → 回落(绝不推已丢弃的单)。
        with (
            patch("core.db.get_cursor_rls"),
            patch("services.purchase.docs.get_doc", return_value=self._detail("discarded")),
        ):
            self.assertIsNone(anchors.resolve_history(_img_ctx(), allow_carrier_insert=True))

    def test_pure_read_does_not_insert_carrier(self):
        with (
            patch("core.db.get_cursor_rls"),
            patch("services.purchase.docs.get_doc", return_value=self._detail("posted")),
            patch("services.agent.doc_fallback.carrier_hist_for_detail") as carrier,
        ):
            anchors.resolve_history(_img_ctx())
        self.assertFalse(carrier.call_args.kwargs["insert"])


class TestPlanRetroHint(unittest.TestCase):
    def _sink_reply(self, ctx_anchors):
        from services.line_binding.line_agent_bridge import _make_write_sink

        sink = _make_write_sink({"id": "u1"}, "t", "zh", "t1", 6, "U1", "rt", None, None, object())
        ctx = AgentContext(user={"id": "u1"}, tenant_id="t1", anchors=ctx_anchors)
        with (
            patch("services.line_binding.line_intent_store.set_intent"),
            patch("services.line_binding.line_reply.reply_text_context") as reply,
        ):
            kind = sink(ctx, "plan_incoming_doc", {"plan": {"goals": ["push"]}}, "")
        self.assertEqual(kind, "card_sent")
        return reply.call_args.args[1]

    def test_hint_appended_when_recent_image_doc(self):
        # 图文同发 race 输掉的防错配:明说计划只管「下一张」+ 给回溯说法。
        self.assertIn("刚才那张", self._sink_reply({"last_image_doc_id": "d9"}))

    def test_no_hint_without_image_anchor(self):
        self.assertNotIn("刚才那张", self._sink_reply({}))


if __name__ == "__main__":
    unittest.main()
