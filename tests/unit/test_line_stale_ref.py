# -*- coding: utf-8 -*-
"""引用旧卡片目标定位 + 死单安全网(line_stale_ref · 05 Slice 1 · 账务红线)守门。

核心:用户明确引用的卡 → 只对那张当前真实状态负责。死单(VOIDED/DISCARDED)不改、给出路;
被更正(SUPERSEDED)落最新活单;★绝不回落到 active 的另一张活单(screenshot-29 真事故)。
"""

import unittest
from decimal import Decimal
from unittest import mock

from services.expense import line_correct
from services.expense import line_correct_flow as flow
from services.expense import line_stale_ref as sr
from services.line_binding import line_message_refs as refs


class _Ctx:
    def __init__(self, cur):
        self._cur = cur

    def __enter__(self):
        return self._cur

    def __exit__(self, *a):
        return False


class LocateClarifyTargetTests(unittest.TestCase):
    def _locate(
        self,
        *,
        quoted="MID",
        text="金额改为300",
        state=None,
        live=None,
        tgt=None,
        active=None,
        active_detail=None,
        has_amount=True,
    ):
        tgt = tgt if tgt is not None else {"doc_id": "DEAD", "ws": 1, "error": None}
        from services.expense import conversation
        from services.purchase import docs as docs_svc

        with (
            mock.patch.object(sr.db, "get_cursor_rls", return_value=_Ctx(object())),
            mock.patch.object(refs, "resolve_target", return_value=tgt),
            mock.patch.object(refs, "resolve_card_state", return_value=(state, live)),
            mock.patch.object(conversation, "peek_pending", return_value=active),
            mock.patch.object(docs_svc, "get_doc", return_value=active_detail),
        ):
            return sr.locate_clarify_target("t", 1, "U1", text, quoted, "zh", has_amount=has_amount)

    def test_live_routes_to_quoted_doc(self):
        detail = {"doc": {"status": "draft"}}
        loc = self._locate(state=refs.LIVE, live=detail)
        self.assertEqual((loc["doc_id"], loc["detail"], loc["notice"]), ("DEAD", detail, ""))

    def test_superseded_routes_to_live_descendant_with_notice(self):
        live = {
            "doc": {
                "status": "posted",
                "id": "D2",
                "grand_total": "300.00",
                "workspace_client_id": 1,
            }
        }
        loc = self._locate(state=refs.SUPERSEDED, live=live)
        self.assertEqual(loc["doc_id"], "D2")  # 最新活单·非原死单
        self.assertTrue(loc["notice"])  # 带「已更新为」前缀

    def test_voided_replies_no_route(self):
        loc = self._locate(state=refs.VOIDED, live=None)
        self.assertIn("reply", loc)
        self.assertNotIn("doc_id", loc)

    def test_discarded_replies_no_route(self):
        loc = self._locate(state=refs.DISCARDED, live=None)
        self.assertIn("reply", loc)

    def test_expired_ref_replies(self):
        loc = self._locate(tgt={"doc_id": None, "ws": 1, "error": "ref_not_found"})
        self.assertIn("reply", loc)

    def test_no_quote_active_continuation(self):
        # 无引用 → 沿用 active 续接(行为不变):落 active 指向的活单。
        loc = self._locate(
            quoted=None,
            active={"missing": f"{line_correct._ACTIVE_PREFIX}1:D9"},
            active_detail={"doc": {"status": "draft"}},
        )
        self.assertEqual(loc["doc_id"], "D9")

    def test_no_quote_no_active_with_amount_passes_through(self):
        loc = self._locate(quoted=None, active=None, has_amount=True)
        self.assertTrue(loc.get("passthrough"))


class StaleQuoteNeverTouchesOtherDocTests(unittest.TestCase):
    """★账务事故防回归:引用死单 → 绝不改 active 指向的另一张活单。"""

    def _run_clarify(self, *, state, live, text):
        from services.expense import conversation
        from services.purchase import docs as docs_svc

        ctx = {"line_user_id": "U1", "tenant_id": "t", "quote_token": "q"}
        applied, sent = [], []
        with (
            mock.patch.object(flow.db, "get_cursor_rls", return_value=_Ctx(object())),
            mock.patch.object(sr.db, "get_cursor_rls", return_value=_Ctx(object())),
            mock.patch.object(
                refs, "resolve_target", return_value={"doc_id": "DEAD", "ws": 1, "error": None}
            ),
            mock.patch.object(refs, "resolve_card_state", return_value=(state, live)),
            # active 指向另一张活单 D150(screenshot-29 被误改的那张)
            mock.patch.object(
                conversation,
                "peek_pending",
                return_value={"missing": f"{line_correct._ACTIVE_PREFIX}1:D150"},
            ),
            mock.patch.object(
                docs_svc, "get_doc", return_value={"doc": {"status": "draft"}, "lines": [{}]}
            ),
            mock.patch.object(conversation, "save_pending"),
            mock.patch.object(conversation, "clear_pending"),
            mock.patch.object(
                line_correct,
                "_apply_or_confirm",
                side_effect=lambda *a, **k: applied.append((a[5], a[6])) or True,
            ),
            mock.patch.object(
                flow.line_reply,
                "reply_text_context",
                side_effect=lambda tok, body, **k: sent.append(body),
            ),
        ):
            res = flow.maybe_clarify_feedback({}, "tok", text, "zh", 1, "MID", ctx)
        return res, applied, sent

    def test_quoted_voided_change_amount_touches_nothing(self):
        # 引用已撤单 + 「金额改为300」→ 不改任何单(★D150 绝不被碰)·回 stale_voided。
        res, applied, sent = self._run_clarify(state=refs.VOIDED, live=None, text="金额改为300")
        self.assertTrue(res)
        self.assertEqual(applied, [])  # ★没有任何 _apply_or_confirm
        self.assertTrue(sent and "撤销" in sent[0])

    def test_quoted_superseded_lands_on_live_not_active(self):
        # 引用被更正的死单 + 改金额 → 落最新活后代 D2(非死单·非 active 的 D150)。
        live = {
            "doc": {
                "status": "draft",
                "id": "D2",
                "grand_total": "300.00",
                "workspace_client_id": 1,
            },
            "lines": [{}],
        }
        res, applied, _ = self._run_clarify(state=refs.SUPERSEDED, live=live, text="金额改为300")
        self.assertTrue(res)
        self.assertEqual(len(applied), 1)
        self.assertEqual(applied[0][0], "D2")  # 目标=最新活单
        self.assertNotEqual(applied[0][0], "D150")  # ★绝非 active 的另一张


if __name__ == "__main__":
    unittest.main()
