import unittest
from unittest import mock

from services.line_dms import cards, query_access, query_cards, query_flow

BINDING = {"tenant_id": "t1", "user_id": "u1"}


class QueryAccessTests(unittest.TestCase):
    def test_requires_active_profile_and_explicit_permission(self):
        with mock.patch.object(
            query_access.roster_store,
            "get_profile",
            return_value={"status": "active", "can_query_dms": True},
        ):
            self.assertTrue(query_access.can_query(BINDING))
        with mock.patch.object(
            query_access.roster_store,
            "get_profile",
            return_value={"status": "inactive", "can_query_dms": True},
        ):
            self.assertFalse(query_access.can_query(BINDING))
        with mock.patch.object(
            query_access.roster_store,
            "get_profile",
            return_value={"status": "active", "can_query_dms": False},
        ):
            self.assertFalse(query_access.can_query(BINDING))


class QueryFlowTests(unittest.IsolatedAsyncioTestCase):
    async def test_forged_query_postback_is_denied_server_side(self):
        with (
            mock.patch.object(query_flow, "_can_query", new=mock.AsyncMock(return_value=False)),
            mock.patch.object(query_flow, "_reply") as reply,
            mock.patch.object(query_flow.store, "set_session") as save,
        ):
            await query_flow.handle_postback(
                BINDING,
                "L1",
                "rt",
                query_cards.ACT_QUERY_TYPE,
                {"kind": "sales"},
                None,
            )
        self.assertEqual(reply.call_args.args[1], query_cards.TXT_DENIED)
        save.assert_not_called()

    async def test_menu_query_opens_type_buttons_for_allowed_member(self):
        with (
            mock.patch.object(query_flow, "_can_query", new=mock.AsyncMock(return_value=True)),
            mock.patch.object(query_flow.store, "set_session") as save,
            mock.patch.object(query_flow, "_send") as send,
        ):
            await query_flow.handle_postback(BINDING, "L1", "rt", cards.ACT_MENU_QUERY, {}, None)
        self.assertEqual(save.call_args.args[2], "query_menu")
        message = send.call_args.args[1]
        labels = [item["action"]["label"] for item in message["quickReply"]["items"]]
        self.assertEqual(labels[0], "1 บันทึกการขาย")
        self.assertEqual(len(labels), 3)

    async def test_sales_text_dimension_runs_after_one_text_answer(self):
        sess = {"state": "query_sales_input", "payload": {"field": "advisor"}}
        with (
            mock.patch.object(query_flow, "_can_query", new=mock.AsyncMock(return_value=True)),
            mock.patch.object(query_flow, "_begin_records", new=mock.AsyncMock()) as begin,
        ):
            handled = await query_flow.handle_text(BINDING, "L1", "rt", sess, "sale01")
        self.assertTrue(handled)
        self.assertEqual(begin.call_args.kwargs["field"], "advisor")
        self.assertEqual(begin.call_args.kwargs["query"], "sale01")

    async def test_latest_records_use_booking_date_sort(self):
        with (
            mock.patch.object(query_flow, "_can_query", new=mock.AsyncMock(return_value=True)),
            mock.patch.object(query_flow, "_begin_records", new=mock.AsyncMock()) as begin,
        ):
            await query_flow.handle_postback(
                BINDING,
                "L1",
                "rt",
                query_cards.ACT_QUERY_DIMENSION,
                {"dimension": "latest"},
                None,
            )
        self.assertEqual(begin.call_args.kwargs["field"], "booking_date")
        self.assertEqual(begin.call_args.kwargs["status"], "active")

    async def test_custom_top_limit_is_restricted_to_one_through_thirty(self):
        sess = {
            "state": "query_top_custom",
            "payload": {"group": "model", "metric": "amount"},
        }
        with (
            mock.patch.object(query_flow, "_can_query", new=mock.AsyncMock(return_value=True)),
            mock.patch.object(query_flow, "_begin_top", new=mock.AsyncMock()) as begin,
        ):
            handled = await query_flow.handle_text(
                BINDING, "L1", "rt", sess, "01/08/2569-31/08/2569 30"
            )
        self.assertTrue(handled)
        self.assertEqual(begin.call_args.kwargs["limit"], 30)
        self.assertEqual(begin.call_args.kwargs["date_from"], "01/08/2569")

    async def test_refresh_invokes_fresh_read_each_time(self):
        params = {
            "query_kind": "records",
            "field": "advisor",
            "query": "sale01",
            "status": "active",
            "limit": 10,
            "page": 1,
        }
        sess = {"state": "query_results", "payload": params}
        with (
            mock.patch.object(query_flow, "_can_query", new=mock.AsyncMock(return_value=True)),
            mock.patch.object(query_flow, "_begin_records", new=mock.AsyncMock()) as begin,
        ):
            for _ in range(2):
                await query_flow.handle_postback(
                    BINDING,
                    "L1",
                    "rt",
                    query_cards.ACT_QUERY_PAGE,
                    {"kind": "records", "direction": "refresh"},
                    sess,
                )
        self.assertEqual(begin.await_count, 2)

    async def test_permission_is_checked_again_before_results_are_sent(self):
        params = {
            "field": "advisor",
            "query": "sale01",
            "status": "active",
            "limit": 10,
            "page": 1,
        }
        with (
            mock.patch.object(
                query_flow.sales_readback,
                "fetch_sales_records",
                return_value={"ok": True, "rows": []},
            ),
            mock.patch.object(query_flow, "_can_query", new=mock.AsyncMock(return_value=False)),
            mock.patch.object(query_flow, "_push") as push,
            mock.patch.object(query_flow, "_send") as send,
        ):
            await query_flow._run_records(BINDING, "L1", params)
        push.assert_called_once_with("L1", query_cards.TXT_DENIED)
        send.assert_not_called()


class QueryCardTests(unittest.TestCase):
    def test_sales_dimensions_fit_line_quick_reply_limit(self):
        message = query_cards.sales_dimension_message()
        self.assertEqual(len(message["quickReply"]["items"]), 13)

    def test_record_dashboard_keeps_dms_draft_status_visible(self):
        result = {
            "page": 1,
            "limit": 10,
            "has_more": False,
            "rows": [
                {
                    "booking_no": "BK-1",
                    "record_status": "แบบร่าง",
                    "customer": "ลูกค้า",
                    "vehicle": "Model X",
                }
            ],
        }
        board = query_cards.sales_board(result)
        rendered = str(board)
        self.assertIn("แบบร่าง", rendered)
        self.assertIn("แบบร่างไม่นับเป็นยอดขาย", rendered)


if __name__ == "__main__":
    unittest.main()
